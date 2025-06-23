"""
Trading Service - Scalable function-based approach for processing trading data
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

from stock_portfolio_shared.models.spreadsheet_task import SpreadsheetTask
from stock_portfolio_shared.utils.base_manager import BaseManager

# Setup logging
from utils.logging_config import setup_logging
logger = setup_logging(__name__)

# Import configuration and services
from config import Config
from services.data_processing_service import DataProcessingService
from services.execution_record_service import ExecutionRecordService

# Import models and database
from models.execution_record import ExecutionRecord

class TradingOrchestrator:
    """Scalable trading service for processing spreadsheet data"""
    
    def __init__(self, manager: BaseManager, executor: ThreadPoolExecutor = None):
        # Initialize configuration and services
        self.config = Config()
        self.data_processing_service = DataProcessingService()
        self.execution_record_service = ExecutionRecordService()
        
        # Use provided manager
        self.manager = manager
        
        # Use provided executor or create a default one
        self.executor = executor or ThreadPoolExecutor(max_workers=4)
        
        # Environment setup
        self.worker_directory = os.path.dirname(os.path.dirname(__file__))
        self.env_file = os.path.join(self.worker_directory, 'secrets', '.env')
        
        logger.info(f"TradingOrchestrator initialized with shared executor")
    
    async def process_spreadsheet(self, spreadsheet_task: SpreadsheetTask, max_retries: int = 0) -> bool:
        """
        Process a single spreadsheet asynchronously using threading
        
        Args:
            spreadsheet_task: SpreadsheetTask object containing spreadsheet info and credentials
            
        Returns:
            bool: Success status
        """
        
        execution_record_id = None
        logger.info(f"Starting async processing for spreadsheet: {spreadsheet_task.spreadsheet_id}")
        for attempt in range(max_retries + 1):
            try:
                # Run the processing in a thread pool
                loop = asyncio.get_event_loop()
                result, execution_record = await loop.run_in_executor(
                    self.executor,
                    self._process_spreadsheet_sync,
                    spreadsheet_task,
                    attempt,
                    execution_record_id
                )
                if result:
                    logger.info(f"Completed processing for {spreadsheet_task.spreadsheet_id}: {result}")
                    return True
                elif attempt < max_retries:
                    # Only set execution_record_id if we have a valid record
                    if execution_record_id is None and execution_record and hasattr(execution_record, 'id'):
                        execution_record_id = execution_record.id
                    elif execution_record_id is None:
                        logger.warning(f"No valid execution record ID for retry on {spreadsheet_task.spreadsheet_id}")
                        return False
                    
                    delay = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed, retrying record {execution_record_id} in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    return False
            
            except Exception as e:
                logger.error(f"Exception in async processing for {spreadsheet_task.spreadsheet_id}: {e}")
                return False
            
    
    def _process_spreadsheet_sync(self, spreadsheet_task: SpreadsheetTask, attempt: int = 0, execution_record_id: int = None) -> Tuple[bool, ExecutionRecord]:
        """
        Synchronous processing function that runs in a thread
        
        Args:
            spreadsheet_task: SpreadsheetTask object containing spreadsheet info and credentials
            attempt: Current retry attempt number
            execution_record_id: ID of execution record to retry (if retrying)
            
        Returns:
            tuple: (Success status, ExecutionRecord)
        """
        start_time = datetime.now()
        execution_record = None
        
        try:
            # Load specific execution record if retrying
            if attempt > 0 and execution_record_id is not None:
                execution_record = self.execution_record_service.load_execution_record_by_id(execution_record_id)
                if execution_record and execution_record.can_retry():
                    try:
                        execution_record.update_retry_info(attempt)
                        self.execution_record_service.save_execution_record(execution_record)
                    except Exception as e:
                        logger.error(f"Failed to update retry info for {spreadsheet_task.spreadsheet_id}: {e}")
                        return False, execution_record
                elif not execution_record:
                    logger.error(f"Execution record not found for {spreadsheet_task.spreadsheet_id}")
                    return False, None
                else:
                    logger.error(f"cannot retry execution for spreadsheet: {spreadsheet_task.spreadsheet_id} with id: {execution_record_id}")
                    return False, execution_record
            else:
                logger.info(f"Processing spreadsheet {spreadsheet_task.spreadsheet_id}")
                
                # Create execution record
                try:
                    execution_record = self.execution_record_service.create_execution_record(spreadsheet_task.spreadsheet_id, start_time)
                    if execution_record is None:
                        logger.error(f"Failed to create execution record for {spreadsheet_task.spreadsheet_id}")
                        return False, None
                except Exception as e:
                    logger.error(f"Exception creating execution record for {spreadsheet_task.spreadsheet_id}: {e}")
                    return False, None
            
            # Get spreadsheet data first
            spreadsheet, sheet_names, raw_data = self._get_spreadsheet_data(spreadsheet_task)
            
            # Update execution record with data hash
            if execution_record:
                self.execution_record_service.update_execution_record_data_hash(execution_record, raw_data)
            
            if raw_data.empty:
                logger.warning(f"No data found in spreadsheet {spreadsheet_task.spreadsheet_id}")
                if execution_record:
                    execution_record.mark_failed("No data found in spreadsheet")
                    self.execution_record_service.save_execution_record(execution_record)
                return False, execution_record
            
            # Check if data has changed
            if not self.execution_record_service.data_has_changed(spreadsheet_task.spreadsheet_id, raw_data):
                logger.info(f"Data unchanged for {spreadsheet_task.spreadsheet_id}, skipping processing")
                if execution_record:
                    execution_record.mark_completed(0, 0)
                    self.execution_record_service.save_execution_record(execution_record)
                return True, execution_record
            
            # Process data in parallel
            results = self._process_data_parallel(sheet_names, raw_data)
            
            # Update spreadsheet with results
            formatting_funcs = self.manager.get_formatting_funcs(sheet_names)
            self._update_spreadsheet(spreadsheet, results, formatting_funcs)
            
            # Calculate processing duration and rows processed
            processing_duration = (datetime.now() - start_time).total_seconds()
            total_rows = sum(len(df) for df in results.values() if isinstance(df, pd.DataFrame))
            
            # Mark execution as completed
            if execution_record:
                execution_record.mark_completed(processing_duration, total_rows)
                self.execution_record_service.save_execution_record(execution_record)
            
            logger.info(f"Successfully processed spreadsheet {spreadsheet_task.spreadsheet_id}")
            return True, execution_record
            
        except Exception as e:
            logger.error(f"Error processing spreadsheet {spreadsheet_task.spreadsheet_id}: {e}")
            if execution_record:
                try:
                    execution_record.mark_failed(str(e))
                    self.execution_record_service.save_execution_record(execution_record)
                except Exception as save_error:
                    logger.error(f"Failed to save failed execution record: {save_error}")
            return False, execution_record
    
    def _get_spreadsheet_data(self, spreadsheet_task: SpreadsheetTask) -> Tuple:
        """Get data from spreadsheet using the provided manager and SpreadsheetTask"""
        try:
            # Use manager for Google Sheets or Excel based on SpreadsheetTask
            spreadsheet = self.manager.get_spreadsheet(spreadsheet_task)
            sheet_names = self.manager.get_sheet_names(spreadsheet_task)
            raw_data = self.manager.read_data(spreadsheet, sheet_names[0])
            logger.info(f"Retrieved data from {spreadsheet_task.spreadsheet_id}: {len(raw_data)} rows, {len(sheet_names)} sheets")
            return spreadsheet, sheet_names, raw_data
            
        except Exception as e:
            logger.error(f"Error getting spreadsheet data for {spreadsheet_task.spreadsheet_id}: {e}")
            raise
    
    def _process_data_parallel(self, sheet_names: List[str], raw_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Process data in parallel using multiple threads
        
        Args:
            raw_data: Raw transaction data
            
        Returns:
            Dict containing processed dataframes
        """
        logger.info("Starting parallel data processing")
        
        # First, process transaction details (this is the base for other processing)
        trans_details_data = self.data_processing_service.process_transaction_details(raw_data)
        logger.info(f"Completed {sheet_names[1]} processing")
        
        # Define processing tasks that depend on trans_details_data
        tasks = [
            (sheet_names[2], self.data_processing_service.process_share_profit_loss, trans_details_data.copy()),
            (sheet_names[3], self.data_processing_service.process_daily_profit_loss, trans_details_data.copy()),
            (sheet_names[4], self.data_processing_service.process_taxation, trans_details_data.copy())
        ]
        
        results = {
            sheet_names[1]: trans_details_data  # Add the already processed transaction details
        }
        
        # Submit tasks to thread pool
        future_to_task = {
            self.executor.submit(func, data): (name, func, data)
            for name, func, data in tasks
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_task):
            task_name, func, data = future_to_task[future]
            try:
                result = future.result()
                results[task_name] = result
                logger.info(f"Completed {task_name} processing")
            except Exception as e:
                logger.error(f"Error in {task_name} processing: {e}")
                results[task_name] = pd.DataFrame()  # Empty dataframe on error
        
        return results
    
    def _update_spreadsheet(self, spreadsheet, results: Dict[str, pd.DataFrame], formatting_funcs: Dict[str, Callable]):
        """Update spreadsheet with processed results"""
        logger.info(f"Updating spreadsheet with {len(results)} processed datasets")
        
        # Update each sheet with corresponding data
        for sheet_name, data in results.items():
            logger.info(f"Updating sheet {sheet_name} with {len(data)} rows")
            if not data.empty:
                
                self.manager.update_data(spreadsheet, sheet_name, data, formatting_funcs.get(sheet_name)) 
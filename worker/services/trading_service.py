"""
Trading Service - Scalable function-based approach for processing trading data
"""

import pandas as pd
import numpy as np
import logging
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

from stock_portfolio_shared.utils.base_manager import BaseManager

# Setup logging
from utils.logging_config import setup_logging
logger = setup_logging(__name__)

# Import configuration and services
from config import Config
from services.data_processing_service import DataProcessingService
from stock_portfolio_shared.constants import Raw_constants
from stock_portfolio_shared.utils.data_processor import DataProcessor
from stock_portfolio_shared.utils.common_utils import CommonUtils
from stock_portfolio_shared.utils.sheet_manager import SheetsManager
from stock_portfolio_shared.utils.excel_manager import ExcelManager

# Import models and database
from models.execution_record import ExecutionRecord
from extensions import db

# Import constants
from models.constants import (
    TransDetails_constants, Raw_constants, DailyProfitLoss_constants, 
    Taxation_constants, Data_constants
)

class TradingService:
    """Scalable trading service for processing spreadsheet data"""
    
    def __init__(self, manager: BaseManager, max_workers: int = 4):
        # Initialize configuration and services
        self.config = Config()
        self.data_processing_service = DataProcessingService()
        self.data_processor = DataProcessor()
        self.common_utils = CommonUtils()
        
        # Use provided manager
        self.manager = manager
        
        # Threading configuration
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Environment setup
        self.worker_directory = os.path.dirname(os.path.dirname(__file__))
        self.env_file = os.path.join(self.worker_directory, 'secrets', '.env')
        
        logger.info(f"TradingService initialized with {max_workers} workers")
    
    def update_manager(self, spreadsheet_type: str, credentials: Dict = None):
        """Get appropriate manager based on spreadsheet type"""
        
        if spreadsheet_type == "sheets" and credentials:
            self.manager = SheetsManager(credentials)
        else:
            self.manager = ExcelManager()
    
    async def process_spreadsheet(self, spreadsheet_id: str, max_retries: int = 3) -> bool:
        """
        Process a single spreadsheet asynchronously using threading
        
        Args:
            spreadsheet_id: Google Sheets ID or Excel file path
            
            
        Returns:
            bool: Success status
        """
        
        execution_record_id = None
        logger.info(f"Starting async processing for spreadsheet: {spreadsheet_id}")
        for attempt in range(max_retries + 1):
            try:
                # Run the processing in a thread pool
                loop = asyncio.get_event_loop()
                result, execution_record = await loop.run_in_executor(
                    self.executor,
                    self._process_spreadsheet_sync,
                    spreadsheet_id,
                    attempt,
                    execution_record_id
                )
                if result:
                    logger.info(f"Completed processing for {spreadsheet_id}: {result}")
                    return True
                elif attempt < max_retries:
                    if execution_record_id is None:
                        execution_record_id = execution_record.id
                    
                    delay = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed, retrying record {execution_record_id} in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    return False
            
            except Exception as e:
                logger.error(f"Exception in async processing for {spreadsheet_id}: {e}")
                return False
            
    
    def _process_spreadsheet_sync(self, spreadsheet_id: str, attempt: int = 0, execution_record_id: int = None) -> bool:
        """
        Synchronous processing function that runs in a thread
        
        Args:
            spreadsheet_id: Google Sheets ID or Excel file path
            
        Returns:
            bool: Success status
        """
        start_time = datetime.now()
        execution_record = None
        
        try:
            # Load specific execution record if retrying
            if attempt > 0 and execution_record_id is not None:
                execution_record = self._load_execution_record_by_id(execution_record_id)
                if execution_record and execution_record.can_retry():
                    try:
                        execution_record.update_retry_info(attempt)
                        self._save_execution_record(execution_record)
                    except Exception as e:
                        logger.error(f"Failed to update retry info for {spreadsheet_id}: {e}")
                        return False, execution_record
                elif not execution_record:
                    logger.error(f"Execution record not found for {spreadsheet_id}")
                    return False, None
                else:
                    logger.error(f"cannot retry execution for spreadsheet: {spreadsheet_id} with id: {execution_record_id}")
                    return False, execution_record
            else:
                logger.info(f"Processing spreadsheet {spreadsheet_id}")
                
                # Create execution record
                execution_record = self._create_execution_record(spreadsheet_id, start_time)
            
            # Get spreadsheet data first
            spreadsheet, sheet_names, raw_data = self._get_spreadsheet_data(spreadsheet_id)
            
            # Update execution record with data hash
            self._update_execution_record_data_hash(execution_record, raw_data)
            
            if raw_data.empty:
                logger.warning(f"No data found in spreadsheet {spreadsheet_id}")
                execution_record.mark_failed("No data found in spreadsheet")
                self._save_execution_record(execution_record)
                return False, execution_record
            
            # Check if data has changed
            if not self._data_has_changed(spreadsheet_id, raw_data):
                logger.info(f"Data unchanged for {spreadsheet_id}, skipping processing")
                execution_record.mark_completed(0, 0)
                self._save_execution_record(execution_record)
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
            execution_record.mark_completed(processing_duration, total_rows)
            self._save_execution_record(execution_record)
            
            logger.info(f"Successfully processed spreadsheet {spreadsheet_id}")
            return True, execution_record
            
        except Exception as e:
            logger.error(f"Error processing spreadsheet {spreadsheet_id}: {e}")
            if execution_record:
                execution_record.mark_failed(str(e))
                self._save_execution_record(execution_record)
            return False, execution_record
    
    def _load_execution_record_by_id(self, record_id: int) -> ExecutionRecord:
        """
        Load execution record by primary key
        
        Args:
            record_id: Primary key of the execution record
            
        Returns:
            ExecutionRecord: The specific execution record
        """
        try:
            record = ExecutionRecord.query.get(record_id)  # ✅ Uses primary key lookup
            if record:
                logger.debug(f"Loaded execution record {record_id} for {record.spreadsheet_id}")
            return record
            
        except Exception as e:
            logger.error(f"Failed to load execution record {record_id}: {e}")
            return None
    
    def _get_spreadsheet_data(self, spreadsheet_id: str) -> Tuple:
        """Get data from spreadsheet using the provided manager"""
        try:
            # Use manager for Google Sheets
            spreadsheet = self.manager.get_spreadsheet(spreadsheet_id)
            sheet_names = self.manager.get_sheet_names(spreadsheet_id)
            raw_data = self.manager.read_data(spreadsheet, sheet_names[0])
            logger.info(f"Retrieved data from {spreadsheet_id}: {len(raw_data)} rows, {len(sheet_names)} sheets")
            return spreadsheet, sheet_names, raw_data
            
        except Exception as e:
            logger.error(f"Error getting spreadsheet data for {spreadsheet_id}: {e}")
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
        trans_details_data = self._process_transaction_details(raw_data)
        logger.info(f"Completed {sheet_names[1]} processing")
        
        # Define processing tasks that depend on trans_details_data
        tasks = [
            (sheet_names[2], self._process_share_profit_loss, trans_details_data.copy()),
            (sheet_names[3], self._process_daily_profit_loss, trans_details_data.copy()),
            (sheet_names[4], self._process_taxation, trans_details_data.copy())
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
    
    def _process_transaction_details(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process transaction details"""
        return self.data_processing_service.process_transaction_details(data)
    
    def _process_share_profit_loss(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process share profit loss"""
        return self.data_processing_service.process_share_profit_loss(data)
    
    def _process_daily_profit_loss(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process daily profit loss data"""
        logger.info("Processing Daily Profit Loss Data")
        
        # Initialize data with extra columns
        extra_cols = [
            TransDetails_constants.STT, TransDetails_constants.GST, 
            TransDetails_constants.SEBI_TRANSACTION_CHARGES,
            TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES, 
            TransDetails_constants.BROKERAGE, TransDetails_constants.STAMP_DUTY, 
            TransDetails_constants.DP_CHARGES, TransDetails_constants.STOCK_EXCHANGE, 
            TransDetails_constants.INTRADAY_COUNT
        ]
        data = self.data_processing_service.formatting_service.initialize_data(data, extra_cols=extra_cols)
        
        # Convert date for sorting
        data[Raw_constants.DATE] = pd.to_datetime(data[Raw_constants.DATE], format=self.config.DATE_FORMAT)
        grouped_data = data.groupby([Raw_constants.DATE, Raw_constants.NAME])

        row_data = {}
        daily_spendings = {}
        
        # Create DataFrame with DailyProfitLoss constants
        constants_dict = {key: value for key, value in DailyProfitLoss_constants.__dict__.items() 
                         if not key.startswith('__')}
        df = pd.DataFrame(columns=list(constants_dict.values()))
        
        for (date, name), group in grouped_data:
            date_str = date.strftime(self.config.DATE_FORMAT)
            if date_str not in daily_spendings:
                daily_spendings[date_str] = 0
            
            # Get price details from market data service
            price_details = self.data_processing_service.market_data_service.get_stock_price_details(date, name)
            
            if date_str not in row_data:
                row_data[date_str] = {}
            
            average_price = 0
            quantity = 0
            amount_invested = 0
            
            for _, transaction in group.iterrows():
                average_price = (average_price * quantity + transaction[TransDetails_constants.FINAL_AMOUNT]) / (quantity + abs(transaction[TransDetails_constants.QUANTITY]))
                quantity += abs(transaction[TransDetails_constants.QUANTITY])
                amount_invested += transaction[TransDetails_constants.FINAL_AMOUNT]
                daily_spendings[date_str] += transaction[TransDetails_constants.FINAL_AMOUNT]
            
            # Create row data
            row_data[date_str][name] = {
                DailyProfitLoss_constants.AVERAGE_PRICE: average_price,
                DailyProfitLoss_constants.QUANTITY: quantity,
                DailyProfitLoss_constants.AMOUNT_INVESTED: amount_invested,
                DailyProfitLoss_constants.OPENING_PRICE: price_details[2] if len(price_details) > 2 else 0,
                DailyProfitLoss_constants.HIGH: price_details[3] if len(price_details) > 3 else 0,
                DailyProfitLoss_constants.LOW: price_details[4] if len(price_details) > 4 else 0,
                DailyProfitLoss_constants.CLOSING_PRICE: price_details[5] if len(price_details) > 5 else 0,
                DailyProfitLoss_constants.VOLUME: price_details[6] if len(price_details) > 6 else 0,
                DailyProfitLoss_constants.DAILY_SPENDINGS: daily_spendings[date_str]
            }
        
        # Create final DataFrame
        for date, stocks in row_data.items():
            for stock_name, stock_data in stocks.items():
                new_row = pd.Series({
                    DailyProfitLoss_constants.DATE: date,
                    DailyProfitLoss_constants.NAME: stock_name,
                    DailyProfitLoss_constants.AVERAGE_PRICE: stock_data[DailyProfitLoss_constants.AVERAGE_PRICE],
                    DailyProfitLoss_constants.QUANTITY: stock_data[DailyProfitLoss_constants.QUANTITY],
                    DailyProfitLoss_constants.AMOUNT_INVESTED: stock_data[DailyProfitLoss_constants.AMOUNT_INVESTED],
                    DailyProfitLoss_constants.OPENING_PRICE: stock_data[DailyProfitLoss_constants.OPENING_PRICE],
                    DailyProfitLoss_constants.HIGH: stock_data[DailyProfitLoss_constants.HIGH],
                    DailyProfitLoss_constants.LOW: stock_data[DailyProfitLoss_constants.LOW],
                    DailyProfitLoss_constants.CLOSING_PRICE: stock_data[DailyProfitLoss_constants.CLOSING_PRICE],
                    DailyProfitLoss_constants.VOLUME: stock_data[DailyProfitLoss_constants.VOLUME],
                    DailyProfitLoss_constants.DAILY_SPENDINGS: stock_data[DailyProfitLoss_constants.DAILY_SPENDINGS]
                })
                df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
        
        return self.data_processing_service.calculation_service.convert_dtypes(df)
    
    def _process_taxation(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process taxation data"""
        logger.info("Processing Taxation Data")
        
        # Initialize data with extra columns
        extra_cols = [
            TransDetails_constants.STT, TransDetails_constants.GST, 
            TransDetails_constants.SEBI_TRANSACTION_CHARGES,
            TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES, 
            TransDetails_constants.BROKERAGE, TransDetails_constants.STAMP_DUTY, 
            TransDetails_constants.DP_CHARGES, TransDetails_constants.STOCK_EXCHANGE, 
            TransDetails_constants.INTRADAY_COUNT
        ]
        data = self.data_processing_service.formatting_service.initialize_data(data, extra_cols=extra_cols)
        
        # Group by name
        grouped_data = data.groupby(Raw_constants.NAME)
        
        # Create DataFrame with Taxation constants
        constants_dict = {key: value for key, value in Taxation_constants.__dict__.items() 
                         if not key.startswith('__')}
        df = pd.DataFrame(columns=list(constants_dict.values()))
        
        for name, group in grouped_data:
            ltcg = 0
            stcg = 0
            intraday_income = 0
            
            # Process transactions for tax calculations
            for _, transaction in group.iterrows():
                if transaction[TransDetails_constants.INTRADAY_COUNT] > 0:
                    # Intraday transaction
                    if transaction[TransDetails_constants.TRANSACTION_TYPE] == self.config.SELL:
                        intraday_income += transaction[TransDetails_constants.NET_AMOUNT]
                else:
                    # Delivery transaction
                    if transaction[TransDetails_constants.TRANSACTION_TYPE] == self.config.SELL:
                        # This is a simplified calculation - in reality, you'd need to match with buy transactions
                        # and calculate actual capital gains
                        if self.data_processing_service.calculation_service.is_long_term(
                            transaction[Raw_constants.DATE], transaction[Raw_constants.DATE]
                        ):
                            ltcg += transaction[TransDetails_constants.NET_AMOUNT]
                        else:
                            stcg += transaction[TransDetails_constants.NET_AMOUNT]
            
            new_row = pd.Series({
                Taxation_constants.DATE: datetime.now().strftime(self.config.DATE_FORMAT),
                Taxation_constants.NAME: name,
                Taxation_constants.LTCG: ltcg,
                Taxation_constants.STCG: stcg,
                Taxation_constants.INTRADAY_INCOME: intraday_income
            })
            df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
        
        return df
    
    def _update_spreadsheet(self, spreadsheet, results: Dict[str, pd.DataFrame], formatting_funcs: Dict[str, Callable]):
        """Update spreadsheet with processed results"""
        logger.info(f"Updating spreadsheet with {len(results)} processed datasets")
        
        # Update each sheet with corresponding data
        for sheet_name, data in results.items():
            logger.info(f"Updating sheet {sheet_name} with {len(data)} rows")
            if not data.empty:
                
                self.manager.update(spreadsheet, sheet_name, data, formatting_funcs.get(sheet_name))
    
    async def process_batch_async(self, spreadsheets: List[Dict], credentials: Dict) -> int:
        """
        Process multiple spreadsheets concurrently
        
        Args:
            spreadsheets: List of spreadsheet dictionaries
            credentials: Google API credentials
            
        Returns:
            int: Number of successfully processed spreadsheets
        """
        try:
            logger.info(f"Starting batch processing for {len(spreadsheets)} spreadsheets")
            
            # Create tasks for all spreadsheets
            tasks = []
            for spreadsheet in spreadsheets:
                spreadsheet_id = self.common_utils.extract_spreadsheet_id(spreadsheet['url'])
                if spreadsheet_id:
                    task = self.process_spreadsheet(spreadsheet_id, credentials)
                    tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful results
            success_count = sum(1 for result in results if result is True)
            
            logger.info(f"Batch processing completed: {success_count}/{len(spreadsheets)} successful")
            return success_count
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return 0
    
    def shutdown(self):
        """Clean shutdown of the service"""
        logger.info("Shutting down TradingService")
        self.executor.shutdown(wait=True)
        logger.info("TradingService shutdown complete")
    
    def _create_execution_record(self, spreadsheet_id: str, execution_time: datetime) -> ExecutionRecord:
        """
        Create a new execution record in the database
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            execution_time: When the execution started
            
        Returns:
            ExecutionRecord: New execution record
        """
        try:
            # Generate worker ID (you might want to make this configurable)
            worker_id = f"worker_{os.getpid()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create new execution record
            execution_record = ExecutionRecord(
                execution_time=execution_time,
                worker_id=worker_id,
                data_hash="",  # Will be set when data is loaded
                spreadsheet_id=spreadsheet_id,
                status='running',
                user_id=None  # Could be set from credentials if available
            )
            
            # Add to database session
            db.session.add(execution_record)
            db.session.commit()
            
            logger.info(f"Created execution record for {spreadsheet_id}")
            return execution_record
            
        except Exception as e:
            logger.error(f"Failed to create execution record for {spreadsheet_id}: {e}")
            db.session.rollback()
            # Return a temporary record for error handling
            return ExecutionRecord(
                execution_time=execution_time,
                worker_id=f"worker_{os.getpid()}",
                data_hash="",
                spreadsheet_id=spreadsheet_id,
                status='failed',
                error_message=str(e)
            )
    
    def _save_execution_record(self, execution_record: ExecutionRecord):
        """
        Save the execution record to the database
        
        Args:
            execution_record: Execution record to save
        """
        try:
            # Update the record in the database
            db.session.merge(execution_record)
            db.session.commit()
            
            logger.info(f"Saved execution record for {execution_record.spreadsheet_id} with status {execution_record.status}")
            
        except Exception as e:
            logger.error(f"Failed to save execution record for {execution_record.spreadsheet_id}: {e}")
            db.session.rollback()
    
    def _load_execution_record(self, spreadsheet_id: str) -> ExecutionRecord:
        """
        Load the latest execution record for a spreadsheet from the database
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            
        Returns:
            ExecutionRecord: Latest execution record or None if not found
        """
        try:
            # Get the most recent execution record for this spreadsheet
            record = ExecutionRecord.query.filter_by(
                spreadsheet_id=spreadsheet_id
            ).order_by(ExecutionRecord.execution_time.desc()).first()
            
            if record:
                logger.info(f"Loaded execution record for {spreadsheet_id} from {record.execution_time}")
            else:
                logger.info(f"No execution record found for {spreadsheet_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Failed to load execution record for {spreadsheet_id}: {e}")
            return None
    
    def _get_data_hash(self, data: pd.DataFrame) -> str:
        """
        Generate a hash of the data to detect changes
        
        Args:
            data: DataFrame to hash
            
        Returns:
            str: Hash of the data
        """
        # Use the ExecutionRecord's generate_data_hash method
        return ExecutionRecord.generate_data_hash(data)
    
    def _data_has_changed(self, spreadsheet_id: str, current_data: pd.DataFrame) -> bool:
        """
        Check if the data has changed since last execution using database records
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            current_data: Current raw data
            
        Returns:
            bool: True if data has changed, False otherwise
        """
        current_hash = self._get_data_hash(current_data)
        
        # Get the latest execution record from database
        record = self._load_execution_record(spreadsheet_id)
        
        if not record:
            logger.info(f"No previous execution record found for {spreadsheet_id}, will process")
            return True
        
        last_hash = record.data_hash
        if last_hash != current_hash:
            logger.info(f"Data has changed for {spreadsheet_id} (hash: {current_hash[:8]}... vs {last_hash[:8]}...)")
            return True
        else:
            logger.info(f"Data unchanged for {spreadsheet_id}, skipping processing")
            return False
    
    def _update_execution_record_data_hash(self, execution_record: ExecutionRecord, data: pd.DataFrame):
        """
        Update the execution record with the data hash
        
        Args:
            execution_record: Execution record to update
            data: Data to generate hash from
        """
        try:
            execution_record.data_hash = self._get_data_hash(data)
            db.session.commit()
            logger.debug(f"Updated data hash for execution record {execution_record.id}")
        except Exception as e:
            logger.error(f"Failed to update data hash: {e}")
            db.session.rollback()
    
    def get_execution_history(self, spreadsheet_id: str, limit: int = 10) -> List[Dict]:
        """
        Get execution history for a spreadsheet
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            limit: Maximum number of records to return
            
        Returns:
            List[Dict]: List of execution records as dictionaries
        """
        try:
            records = ExecutionRecord.query.filter_by(
                spreadsheet_id=spreadsheet_id
            ).order_by(ExecutionRecord.execution_time.desc()).limit(limit).all()
            
            return [record.to_dict() for record in records]
            
        except Exception as e:
            logger.error(f"Failed to get execution history for {spreadsheet_id}: {e}")
            return []
    
    def get_execution_statistics(self, spreadsheet_id: str = None) -> Dict:
        """
        Get execution statistics
        
        Args:
            spreadsheet_id: Optional spreadsheet ID to filter by
            
        Returns:
            Dict: Execution statistics
        """
        try:
            query = ExecutionRecord.query
            
            if spreadsheet_id:
                query = query.filter_by(spreadsheet_id=spreadsheet_id)
            
            total_executions = query.count()
            successful_executions = query.filter_by(status='completed').count()
            failed_executions = query.filter_by(status='failed').count()
            
            # Get average processing duration
            avg_duration = db.session.query(db.func.avg(ExecutionRecord.processing_duration)).scalar() or 0
            
            # Get total rows processed
            total_rows = db.session.query(db.func.sum(ExecutionRecord.rows_processed)).scalar() or 0
            
            return {
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                'average_duration': avg_duration,
                'total_rows_processed': total_rows
            }
            
        except Exception as e:
            logger.error(f"Failed to get execution statistics: {e}")
            return {} 
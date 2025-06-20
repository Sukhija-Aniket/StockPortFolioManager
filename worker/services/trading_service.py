"""
Trading Service - Scalable function-based approach for processing trading data
"""

import pandas as pd
import os
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

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

# Import constants
from models.constants import TransDetails_constants, Raw_constants, DailyProfitLoss_constants, Taxation_constants

class TradingService:
    """Scalable trading service for processing spreadsheet data"""
    
    def __init__(self, max_workers: int = 4):
        # Initialize configuration and services
        self.config = Config()
        self.data_processing_service = DataProcessingService()
        self.data_processor = DataProcessor()
        self.common_utils = CommonUtils()
        self.sheets_manager = SheetsManager()
        self.excel_manager = ExcelManager()
        
        # Threading configuration
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Environment setup
        self.worker_directory = os.path.dirname(os.path.dirname(__file__))
        self.env_file = os.path.join(self.worker_directory, 'secrets', '.env')
        
        logger.info(f"TradingService initialized with {max_workers} workers")
    
    async def process_spreadsheet_async(self, spreadsheet_id: str, credentials: Dict, 
                                      spreadsheet_type: str = 'sheets') -> bool:
        """
        Process a single spreadsheet asynchronously using threading
        
        Args:
            spreadsheet_id: Google Sheets ID or Excel file path
            credentials: Google API credentials
            spreadsheet_type: 'sheets' or 'excel'
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Starting async processing for spreadsheet: {spreadsheet_id}")
            
            # Run the processing in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._process_spreadsheet_sync,
                spreadsheet_id,
                credentials,
                spreadsheet_type
            )
            
            logger.info(f"Completed processing for {spreadsheet_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Exception in async processing for {spreadsheet_id}: {e}")
            return False
    
    def _process_spreadsheet_sync(self, spreadsheet_id: str, credentials: Dict, 
                                spreadsheet_type: str) -> bool:
        """
        Synchronous processing function that runs in a thread
        
        Args:
            spreadsheet_id: Google Sheets ID or Excel file path
            credentials: Google API credentials
            spreadsheet_type: 'sheets' or 'excel'
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Processing spreadsheet {spreadsheet_id} of type {spreadsheet_type}")
            
            # Get spreadsheet data first
            spreadsheet, sheet_names, raw_data = self._get_spreadsheet_data(
                spreadsheet_type, spreadsheet_id, credentials
            )
            
            if raw_data.empty:
                logger.warning(f"No data found in spreadsheet {spreadsheet_id}")
                return False
            
            # Check if data has changed
            if not self._data_has_changed(spreadsheet_id, raw_data):
                logger.info(f"Data unchanged for {spreadsheet_id}, skipping processing")
                return True
            
            # Process data in parallel
            results = self._process_data_parallel(sheet_names, raw_data)
            
            # Update spreadsheet with results
            formatting_funcs = self.sheets_manager.get_formatting_funcs()
            self._update_spreadsheet(spreadsheet, results, spreadsheet_type, formatting_funcs)
            
            # Save execution record
            self._save_execution_record(spreadsheet_id, self._get_data_hash(raw_data), results)
            
            logger.info(f"Successfully processed spreadsheet {spreadsheet_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing spreadsheet {spreadsheet_id}: {e}")
            return False
    
    def _get_spreadsheet_data(self, spreadsheet_type: str, spreadsheet_id: str, 
                             credentials: Dict) -> Tuple:
        """Get data from spreadsheet"""
        if spreadsheet_type == 'sheets':
            spreadsheet = self.sheets_manager.authenticate_and_get_sheets(
                None, spreadsheet_id, credentials
            )
            worksheets = spreadsheet.worksheets()
            sheet_names = [worksheet.title for worksheet in worksheets]
            raw_data = self.sheets_manager.read_data_from_sheets(spreadsheet, sheet_names[0])
        else:
            # Excel processing
            excel_file = os.path.join(self.worker_directory, 'assets', spreadsheet_id)
            spreadsheet = self.excel_manager.load_workbook(excel_file)
            sheet_names = spreadsheet.sheetnames
            raw_data = self.excel_manager.read_data_from_excel(spreadsheet, sheet_names[0])
        
        return spreadsheet, sheet_names, raw_data
    
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
    
    def _update_spreadsheet(self, spreadsheet, results: Dict[str, pd.DataFrame], 
                          spreadsheet_type: str, formatting_funcs: Dict[str, Callable]):
        """Update spreadsheet with processed results"""
        logger.info(f"Updating spreadsheet with {len(results)} processed datasets")
        
        # Update each sheet with corresponding data
        for sheet_name, data in results.items():
            logger.info(f"Updating sheet {sheet_name} with {len(data)} rows")
            if not data.empty:
                if spreadsheet_type == 'sheets':
                    self.sheets_manager.update_sheet(spreadsheet, f"{sheet_name}", data, formatting_funcs[sheet_name])
                else:
                    self.excel_manager.update_excel(spreadsheet, f"{sheet_name}", data, formatting_funcs[sheet_name])
    
    def _script_already_executed(self, spreadsheet_type: str) -> bool:
        """Check if script has already been executed today"""
        from dotenv import load_dotenv
        load_dotenv(self.env_file)
        
        last_execution_date = os.getenv(f'LAST_EXECUTION_DATE_{spreadsheet_type.upper()}')
        if last_execution_date == datetime.now().strftime(self.config.DATE_FORMAT):
            logger.info("The script has already been executed today")
            return True
        return False
    
    def _update_execution_date(self, spreadsheet_type: str):
        """Update execution date in environment file"""
        current_date = datetime.now().strftime(self.config.DATE_FORMAT)
        self.common_utils.update_env_file(
            f'LAST_EXECUTION_DATE_{spreadsheet_type.upper()}', 
            current_date, 
            self.env_file
        )
    
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
                    task = self.process_spreadsheet_async(spreadsheet_id, credentials)
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
    
    def _get_data_hash(self, data: pd.DataFrame) -> str:
        """
        Generate a hash of the data to detect changes
        
        Args:
            data: DataFrame to hash
            
        Returns:
            str: Hash of the data
        """
        # Convert DataFrame to a string representation and hash it
        data_str = data.to_string()
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _get_execution_record_path(self, spreadsheet_id: str) -> str:
        """
        Get the path to the execution record file
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            
        Returns:
            str: Path to execution record file
        """
        records_dir = os.path.join(self.scripts_directory, 'execution_records')
        os.makedirs(records_dir, exist_ok=True)
        return os.path.join(records_dir, f"{spreadsheet_id}.json")
    
    def _load_execution_record(self, spreadsheet_id: str) -> Dict:
        """
        Load the execution record for a spreadsheet
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            
        Returns:
            Dict: Execution record or empty dict if not found
        """
        record_path = self._get_execution_record_path(spreadsheet_id)
        if os.path.exists(record_path):
            try:
                with open(record_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load execution record for {spreadsheet_id}: {e}")
        return {}
    
    def _save_execution_record(self, spreadsheet_id: str, data_hash: str, results: Dict[str, pd.DataFrame]):
        """
        Save the execution record for a spreadsheet
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            data_hash: Hash of the processed data
            results: Processing results
        """
        record_path = self._get_execution_record_path(spreadsheet_id)
        record = {
            'spreadsheet_id': spreadsheet_id,
            'last_execution': datetime.now().isoformat(),
            'data_hash': data_hash,
            'rows_processed': len(results.get('transaction_details', pd.DataFrame())),
            'results_summary': {
                name: len(df) if isinstance(df, pd.DataFrame) else 0 
                for name, df in results.items()
            }
        }
        
        try:
            with open(record_path, 'w') as f:
                json.dump(record, f, indent=2)
            logger.info(f"Saved execution record for {spreadsheet_id}")
        except Exception as e:
            logger.error(f"Failed to save execution record for {spreadsheet_id}: {e}")
    
    def _data_has_changed(self, spreadsheet_id: str, current_data: pd.DataFrame) -> bool:
        """
        Check if the data has changed since last execution
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            current_data: Current raw data
            
        Returns:
            bool: True if data has changed, False otherwise
        """
        current_hash = self._get_data_hash(current_data)
        record = self._load_execution_record(spreadsheet_id)
        
        if not record:
            logger.info(f"No previous execution record found for {spreadsheet_id}, will process")
            return True
        
        last_hash = record.get('data_hash')
        if last_hash != current_hash:
            logger.info(f"Data has changed for {spreadsheet_id} (hash: {current_hash[:8]}... vs {last_hash[:8]}...)")
            return True
        else:
            logger.info(f"Data unchanged for {spreadsheet_id}, skipping processing")
            return False 
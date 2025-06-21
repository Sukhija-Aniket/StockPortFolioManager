import pandas as pd
import logging
from stock_portfolio_shared.utils.sheet_manager import SheetsManager
from stock_portfolio_shared.utils.excel_manager import ExcelManager
from stock_portfolio_shared.utils.data_processor import DataProcessor
from stock_portfolio_shared.utils.common_utils import CommonUtils

logger = logging.getLogger(__name__)

# Initialize managers and processors from shared library
sheets_manager = SheetsManager()
excel_manager = ExcelManager()
data_processor = DataProcessor()
common_utils = CommonUtils()

def upload_data(file_path, typ, spreadsheet_id, creds, http): 
    """Main function to upload data to sheets or excel using shared library"""
    # Use shared library's data processor for path validation
    valid_path = data_processor.check_valid_path(file_path)
    if valid_path:
        # Handling User data and preparing raw data
        logger.info(f"Processing file: {file_path}")
        input_data = pd.read_csv(file_path)
        
        # Use shared library's data processor for formatting
        final_input_data = data_processor.format_add_data(input_data)
        
        # Get spreadsheet data
        from config import Config
        spreadsheet, sheet_names, raw_data = sheets_manager.get_sheets_and_data(
            spreadsheet_id, 
            creds, 
        ) if typ == "sheets" else sheets_manager.get_sheets_and_data(
            typ, 
            Config.API_KEY_FILE, 
            None, 
            spreadsheet_id, 
            creds, 
            http
        )
        
        # Check for duplicates using shared library
        data_processor.data_already_exists(raw_data, final_input_data)
        
        # Combine data
        raw_data = pd.concat([raw_data, final_input_data], ignore_index=True)
        
        # Update spreadsheet
        updating_func = excel_manager.get_updating_func(typ)
        updating_func(spreadsheet, sheet_names[0], raw_data)
        
        logger.info("Data uploaded successfully")
    else:
        logger.error(f"Invalid path: {file_path}")
        raise FileNotFoundError(f"Invalid path: {file_path}")
import pandas as pd
import logging
from stock_portfolio_shared.utils.sheets import SheetsManager
from stock_portfolio_shared.utils.excel import ExcelManager
from stock_portfolio_shared.utils.data_processing import DataProcessor
from stock_portfolio_shared.utils.common import CommonUtils

logger = logging.getLogger(__name__)

# Initialize managers and processors from shared library
sheets_manager = SheetsManager()
excel_manager = ExcelManager()
data_processor = DataProcessor()
common_utils = CommonUtils()

# Functions for sheets (using shared library)
def authenticate_and_get_sheets(credentials_file, spreadsheet_id, credentials=None, http=None):
    return sheets_manager.authenticate_and_get_sheets(spreadsheet_id, credentials, http)

def read_data_from_sheets(spreadsheet, sheet_name):
    return sheets_manager.read_data_from_sheets(spreadsheet, sheet_name)

def format_background_sheets(spreadsheet, sheet, cell_range):
    return sheets_manager.format_background_sheets(spreadsheet, sheet, cell_range)

def initialize_sheets(spreadsheet, sheet_name):
    return sheets_manager.initialize_sheets(spreadsheet, sheet_name)

def update_sheet(spreadsheet, sheet_name, data, formatting_function=None):
    return sheets_manager.update_sheet(spreadsheet, sheet_name, data, formatting_function)

def display_and_format_sheets(spreadsheet, sheet, data):
    return sheets_manager.display_and_format_sheets(sheet, data)

def get_sheets_and_data(typ, credentials_file, spreadsheet_id, spreadsheet_file, credentials=None, http=None):
    return sheets_manager.get_sheets_and_data(typ, credentials_file, spreadsheet_id, spreadsheet_file, credentials, http)

# Functions for Excel (using shared library)
def read_data_from_excel(spreadsheet_file, sheet_name):
    return excel_manager.read_data_from_excel(spreadsheet_file, sheet_name)

def update_excel(spreadsheet, sheet_name, data, formatting_function=None):
    return excel_manager.update_excel(spreadsheet, sheet_name, data, formatting_function)

def display_and_format_excel(sheet, data):
    return excel_manager.display_and_format_excel(sheet, data)

def format_background_excel(sheet, cell_range):
    return excel_manager.format_background_excel(sheet, cell_range)

def initialize_excel(spreadsheet, sheet_name):
    return excel_manager.initialize_excel(spreadsheet, sheet_name)

# Common Functions (using shared library)
def get_updating_func(typ):
    return excel_manager.get_updating_func(typ)

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
            typ, 
            Config.API_KEY_FILE, 
            spreadsheet_id, 
            None, 
            creds, 
            http
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

def get_args_and_input(args, excel_file_name, spreadsheet_id, env_file):
    """Get arguments and input data for processing using shared library"""
    try:
        # Use shared library's common utils for argument parsing
        input_file, typ, credentials = common_utils.get_args_and_input(args, excel_file_name, spreadsheet_id, env_file)
        
        # Get spreadsheet file path using shared library
        spreadsheet_file = data_processor.get_valid_path(input_file)
        
        # Get spreadsheet ID
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required")
        
        return {
            'credentials': credentials,
            'spreadsheet_file': spreadsheet_file,
            'spreadsheet_id': spreadsheet_id,
            'env_file': env_file
        }
        
    except Exception as e:
        logger.error(f"Error getting arguments: {e}")
        raise
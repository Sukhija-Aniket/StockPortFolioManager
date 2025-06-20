import pandas as pd
import os
import sys
from datetime import datetime
import logging

# Setup logging
from worker.constants import TransDetails_constants, Raw_constants, DailyProfitLoss_constants, Taxation_constants
from utils.logging_config import setup_logging
logger = setup_logging(__name__)

# Import configuration and services
from config import Config
from services.data_processing_service import DataProcessingService
from stock_portfolio_shared.constants import DATE_FORMAT, SELL, Raw_constants, Data_constants
from stock_portfolio_shared.utils.data_processing import DataProcessor
from stock_portfolio_shared.utils.common import CommonUtils
from stock_portfolio_shared.utils.sheets import SheetsManager
from stock_portfolio_shared.utils.excel import ExcelManager

# Initialize configuration and services
config = Config()
data_processing_service = DataProcessingService()
data_processor = DataProcessor()
common_utils = CommonUtils()
sheets_manager = SheetsManager()
excel_manager = ExcelManager()

scripts_directory = os.path.dirname(__file__)
# parent_directory = os.path.dirname(scripts_directory)
# sys.path.append(parent_directory)

from constants import *

# Important Information
from dotenv import load_dotenv
env_file = os.path.join(scripts_directory, 'secrets', '.env')
load_dotenv(env_file)

api_key_file_name = 'tradingprojects-apiKey.json'
excel_file_name = os.getenv('EXCEL_FILE_NAME')
spreadsheet_id = os.getenv('SPREADSHEET_ID')
spreadsheet_file = os.path.join(scripts_directory, 'assets', excel_file_name)
credentials_file = os.path.join(scripts_directory, 'secrets', api_key_file_name)

logger.info("Trading script initialized with environment variables loaded")

# Required Utility Functions

def script_already_executed(typ):
    """Check if script has already been executed today"""
    last_execution_date = os.getenv(f'LAST_EXECUTION_DATE_{typ.upper()}')
    if last_execution_date == datetime.now().strftime(config.DATE_FORMAT):
        logger.info("The script has already been executed today, Exiting...")
        exit()
    common_utils.update_env_file(f'LAST_EXECUTION_DATE_{typ.upper()}', last_execution_date, config.env_file)

def process_transaction_details(data):
    """Process transaction details using the service"""
    return data_processing_service.process_transaction_details(data)

def process_share_profit_loss(data):
    """Process share profit loss using the service"""
    return data_processing_service.process_share_profit_loss(data)

def process_daily_profit_loss(data):
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
    data = data_processing_service.formatting_service.initialize_data(data, extra_cols=extra_cols)
    
    # Convert date for sorting
    data[Raw_constants.DATE] = pd.to_datetime(data[Raw_constants.DATE], format=config.DATE_FORMAT)
    grouped_data = data.groupby([Raw_constants.DATE, Raw_constants.NAME])

    row_data = {}
    daily_spendings = {}
    
    # Create DataFrame with DailyProfitLoss constants
    constants_dict = {key: value for key, value in DailyProfitLoss_constants.__dict__.items() 
                     if not key.startswith('__')}
    df = pd.DataFrame(columns=list(constants_dict.values()))
    
    for (date, name), group in grouped_data:
        date_str = date.strftime(config.DATE_FORMAT)
        if date_str not in daily_spendings:
            daily_spendings[date_str] = 0
        
        # Get price details from market data service
        price_details = data_processing_service.market_data_service.get_stock_price_details(date, name)
        
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
    
    return data_processing_service.calculation_service.convert_dtypes(df)

def process_taxation(data):
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
    data = data_processing_service.formatting_service.initialize_data(data, extra_cols=extra_cols)
    
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
                if transaction[TransDetails_constants.TRANSACTION_TYPE] == config.SELL:
                    intraday_income += transaction[TransDetails_constants.NET_AMOUNT]
            else:
                # Delivery transaction
                if transaction[TransDetails_constants.TRANSACTION_TYPE] == config.SELL:
                    # This is a simplified calculation - in reality, you'd need to match with buy transactions
                    # and calculate actual capital gains
                    if data_processing_service.calculation_service.is_long_term(
                        transaction[Raw_constants.DATE], transaction[Raw_constants.DATE]
                    ):
                        ltcg += transaction[TransDetails_constants.NET_AMOUNT]
                    else:
                        stcg += transaction[TransDetails_constants.NET_AMOUNT]
        
        new_row = pd.Series({
            Taxation_constants.DATE: datetime.now().strftime(config.DATE_FORMAT),
            Taxation_constants.NAME: name,
            Taxation_constants.LTCG: ltcg,
            Taxation_constants.STCG: stcg,
            Taxation_constants.INTRADAY_INCOME: intraday_income
        })
        df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
    
    return data_processing_service.calculation_service.convert_dtypes(df)

def main():
    """Main function to process trading data"""
    try:
        # Get arguments using shared library
        input_file, typ, credentials = common_utils.get_args_and_input(
            sys.argv, 
            config.EXCEL_FILE_NAME, 
            config.SPREADSHEET_ID, 
            config.env_file
        )
        
        # Check if script already executed
        script_already_executed(typ)
        
        # Read input data
        if input_file:
            logger.info(f"Processing file: {input_file}")
            input_data = pd.read_csv(input_file)
            # Use shared library for data formatting
            final_input_data = data_processor.format_add_data(input_data)
        else:
            logger.error("No input file provided")
            return
        
        # Get spreadsheet data
        spreadsheet, sheet_names, raw_data = sheets_manager.get_sheets_and_data(
            typ, 
            config.API_KEY_FILE, 
            config.SPREADSHEET_ID, 
            config.SPREADSHEET_FILE, 
            credentials, 
            None
        )
        
        # Check for duplicates using shared library
        if data_processor.data_already_exists(raw_data, final_input_data):
            logger.warning("Data already exists, skipping processing")
            return
        
        # Combine data
        raw_data = pd.concat([raw_data, final_input_data], ignore_index=True)
        
        # Process different types of data
        trans_details_data = process_transaction_details(raw_data.copy())
        share_profit_loss_data = process_share_profit_loss(trans_details_data.copy())
        daily_profit_loss_data = process_daily_profit_loss(trans_details_data.copy())
        taxation_data = process_taxation(trans_details_data.copy())
        
        # Update sheets
        updating_func = excel_manager.get_updating_func(typ)
        
        # Update each sheet
        updating_func(spreadsheet, sheet_names[0], trans_details_data)  # Transactions
        if len(sheet_names) > 1:
            updating_func(spreadsheet, sheet_names[1], share_profit_loss_data)  # Share Profit/Loss
        if len(sheet_names) > 2:
            updating_func(spreadsheet, sheet_names[2], daily_profit_loss_data)  # Daily Profit/Loss
        if len(sheet_names) > 3:
            updating_func(spreadsheet, sheet_names[3], taxation_data)  # Taxation
        
        logger.info("Trading script completed successfully")
        
    except Exception as e:
        logger.error(f"Error in trading script: {e}")
        raise

if __name__ == "__main__":
    main()


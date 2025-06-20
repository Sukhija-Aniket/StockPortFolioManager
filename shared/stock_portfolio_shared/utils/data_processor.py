"""
Data processing utilities for Stock Portfolio Manager
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from ..constants import DATE_FORMAT, DATA_TIME_FORMAT, SELL, Raw_constants, Data_constants
import os

logger = logging.getLogger(__name__)

class DataProcessor:
    """Manages data processing operations"""
    
    @staticmethod
    def replace_out_of_range_floats(obj):
        """Replace out of range floats with None"""
        if isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
        elif isinstance(obj, list):
            return [DataProcessor.replace_out_of_range_floats(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: DataProcessor.replace_out_of_range_floats(value) for key, value in obj.items()}
        return obj
    
    @staticmethod
    def get_symbol(row):
        """Extract symbol from row data"""
        symbol = row[Data_constants.NAME]
        symbol = str(symbol).split('-')[0]
        return str(symbol)
    
    @staticmethod
    def get_data_date(date):
        """Convert date to required format"""
        date_obj = datetime.strptime(date, DATA_TIME_FORMAT)
        date_str = datetime.strftime(date_obj, DATE_FORMAT)
        return date_str
    
    @staticmethod
    def get_data_quantity(row):
        """Get data quantity from row"""
        quantity = row[Data_constants.QUANTITY]
        val = str(quantity).split('.')[0]
        if str(row[Data_constants.TYPE]).upper() == SELL:
            val = '-' + val
        return val
    
    @staticmethod
    def get_net_amount(row):
        """Calculate net amount from row"""
        val = int(row[Raw_constants.QUANTITY]) * float(row[Raw_constants.PRICE])
        return str(val)
    
    @staticmethod
    def format_add_data(input_data):
        """Format input data for processing"""
        input_data[Data_constants.QUANTITY] = input_data.apply(
            DataProcessor.get_data_quantity, axis=1)
        constants_dict = {key: value for key, value in Raw_constants.__dict__.items() if not key.startswith('__')}
        df = pd.DataFrame(columns=list(constants_dict.values()))
        
        df[Raw_constants.DATE] = input_data[Data_constants.DATE].apply(
            lambda x: DataProcessor.get_data_date(x))
        df[Raw_constants.NAME] = input_data.apply(DataProcessor.get_symbol, axis=1)
        df[Raw_constants.PRICE] = input_data[Data_constants.PRICE]
        df[Raw_constants.QUANTITY] = input_data[Data_constants.QUANTITY]
        df[Raw_constants.NET_AMOUNT] = df.apply(DataProcessor.get_net_amount, axis=1)
        df[Raw_constants.STOCK_EXCHANGE] = input_data[Data_constants.STOCK_EXCHANGE]
        return df
    
    @staticmethod
    def data_already_exists(raw_data, input_data):
        """Check if data already exists"""
        input_data.reset_index(drop=True, inplace=True)
        if not raw_data.empty:
            is_duplicate = raw_data[
                (raw_data[Raw_constants.DATE] == input_data[Raw_constants.DATE][0]) &
                (raw_data[Raw_constants.NAME] == input_data[Raw_constants.NAME][0])
            ].shape[0] > 0

            if is_duplicate:
                logger.info("Orders Data Already Exists in the file, Exiting...")
                exit()
    
    @staticmethod
    def check_valid_path(path):
        """Check if path is valid"""
        if path is None or not os.path.exists(path):
            return None
        return True
    
    @staticmethod
    def get_valid_path(path):
        """Get valid path with user input if needed"""
        if path is None:
            return None
        if not os.path.exists(path):
            logger.error("The Provided Path for file downloaded from Zerodha does not exist!")
            path = input("Enter correct Absolute Path, including /home: ")
            path = DataProcessor.get_valid_path(path)   
        return path
    
    @staticmethod
    def format_data_for_display(data):
        """Format data for display purposes"""
        # This is a placeholder - implement based on specific display requirements
        return data
    
    @staticmethod
    def process_trading_data(data):
        """Process trading data for analysis"""
        # This is a placeholder - implement based on specific trading analysis requirements
        return data
    
    @staticmethod
    def validate_data(data):
        """Validate data integrity"""
        # This is a placeholder - implement based on specific validation requirements
        return True
    
    @staticmethod
    def ensure_directory_exists(directory_path):
        """Ensure directory exists, create if it doesn't"""
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        return directory_path
    
    @staticmethod
    def get_file_extension(file_path):
        """Get file extension from path"""
        return os.path.splitext(file_path)[1].lower()
    
    @staticmethod
    def is_valid_file_type(file_path, allowed_extensions):
        """Check if file type is valid"""
        extension = DataProcessor.get_file_extension(file_path)
        return extension in allowed_extensions 
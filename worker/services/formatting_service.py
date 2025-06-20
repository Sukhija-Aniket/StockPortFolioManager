import pandas as pd
import numpy as np
import logging
from models.constants import Data_constants, ShareProfitLoss_constants, Taxation_constants
from config import Config

logger = logging.getLogger(__name__)

class FormattingService:
    """Service for data formatting and presentation"""
    
    def __init__(self):
        self.config = Config()
    
    
    def initialize_data(self, data, extra_cols=None, sort_list=None):
        """Initialize data with additional columns and sorting"""
        try:
            if extra_cols:
                for col in extra_cols:
                    if col not in data.columns:
                        data[col] = 0
            
            if sort_list:
                data = data.sort_values(by=sort_list)
            
            return data
            
        except Exception as e:
            logger.error(f"Error initializing data: {e}")
            raise
    
    def replace_out_of_range_floats(self, obj):
        """Replace NaN and infinite values with None"""
        try:
            if isinstance(obj, float):
                if np.isnan(obj) or np.isinf(obj):
                    return None
            elif isinstance(obj, list):
                return [self.replace_out_of_range_floats(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: self.replace_out_of_range_floats(value) for key, value in obj.items()}
            return obj
            
        except Exception as e:
            logger.error(f"Error replacing out of range floats: {e}")
            return obj
    
    def get_spl_row(self):
        """Get default Share Profit Loss row"""
        return {
            ShareProfitLoss_constants.DATE: self.config.DEFAULT_DATE,
            ShareProfitLoss_constants.AVERAGE_BUY_PRICE: 0,
            ShareProfitLoss_constants.AVERAGE_SALE_PRICE: 0,
            ShareProfitLoss_constants.AVERAGE_COST_OF_SOLD_SHARES: 0,
            ShareProfitLoss_constants.SHARES_BOUGHT: 0,
            ShareProfitLoss_constants.SHARES_SOLD: 0,
            ShareProfitLoss_constants.TOTAL_INVESTMENT: 0,
            ShareProfitLoss_constants.CURRENT_INVESTMENT: 0
        }
    
    def get_taxation_row(self):
        """Get default Taxation row"""
        return {
            Taxation_constants.DATE: self.config.DEFAULT_DATE,
            Taxation_constants.LTCG: 0,
            Taxation_constants.STCG: 0,
            Taxation_constants.INTRADAY_INCOME: 0
        }
    
    def _get_symbol(self, row):
        """Extract symbol from row data"""
        symbol = row[Data_constants.NAME]
        symbol = str(symbol).split('-')[0]
        return str(symbol)
    
    def _get_data_date(self, date):
        """Format date to standard format"""
        return pd.to_datetime(date).strftime(self.config.DATE_FORMAT)
    
    def _get_data_quantity(self, row):
        """Get quantity with sign based on transaction type"""
        quantity = row[Data_constants.QUANTITY]
        # Convert to numeric, handling string inputs
        try:
            quantity = pd.to_numeric(quantity, errors='coerce')
            if pd.isna(quantity):
                quantity = 0
        except (ValueError, TypeError):
            quantity = 0
            
        if row[Data_constants.TYPE] == self.config.SELL:
            quantity = -quantity
        return quantity
    
    def _get_net_amount(self, row):
        """Calculate net amount for a transaction"""
        quantity = row[Data_constants.QUANTITY]
        price = row[Data_constants.PRICE]
        
        # Convert to numeric, handling string inputs
        try:
            quantity = pd.to_numeric(quantity, errors='coerce')
            price = pd.to_numeric(price, errors='coerce')
            if pd.isna(quantity) or pd.isna(price):
                return 0
        except (ValueError, TypeError):
            return 0
            
        return quantity * price
    
    def _update_transaction_type(self, x):
        """Update transaction type based on quantity"""
        # Convert to numeric, handling string inputs
        try:
            x = pd.to_numeric(x, errors='coerce')
            if pd.isna(x):
                x = 0
        except (ValueError, TypeError):
            x = 0
            
        return self.config.BUY if x > 0 else self.config.SELL 
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from models.constants import TransDetails_constants, Raw_constants
from config import Config

logger = logging.getLogger(__name__)

class CalculationService:
    """Service for financial calculations and computations"""
    
    def __init__(self):
        self.config = Config()
    
    def calculate_stt(self, row):
        """Calculate Securities Transaction Tax"""
        try:
            net_amount = self._safe_numeric(row[TransDetails_constants.NET_AMOUNT])
            if row[TransDetails_constants.TRANSACTION_TYPE] == self.config.BUY:
                return abs(net_amount * 0.0005)
            else:
                return abs(net_amount * 0.0005)
        except Exception as e:
            logger.error(f"Error calculating STT: {e}")
            return 0
    
    def calculate_transaction_charges(self, row):
        """Calculate SEBI transaction charges"""
        try:
            net_amount = self._safe_numeric(row[TransDetails_constants.NET_AMOUNT])
            return abs(net_amount * 0.000001)
        except Exception as e:
            logger.error(f"Error calculating transaction charges: {e}")
            return 0
    
    def calculate_brokerage(self, row):
        """Calculate brokerage charges"""
        try:
            # Simple brokerage calculation - can be customized based on broker
            net_amount = self._safe_numeric(row[TransDetails_constants.NET_AMOUNT])
            return abs(net_amount * 0.0005)
        except Exception as e:
            logger.error(f"Error calculating brokerage: {e}")
            return 0
    
    def calculate_stamp_duty(self, row):
        """Calculate stamp duty"""
        try:
            net_amount = self._safe_numeric(row[TransDetails_constants.NET_AMOUNT])
            return abs(net_amount * 0.00015)
        except Exception as e:
            logger.error(f"Error calculating stamp duty: {e}")
            return 0
    
    def calculate_dp_charges(self, row, dp_data=None):
        """Calculate DP charges"""
        try:
            # Default DP charges - can be customized
            quantity = self._safe_numeric(row[TransDetails_constants.QUANTITY])
            return 13.5 if quantity > 0 else 0
        except Exception as e:
            logger.error(f"Error calculating DP charges: {e}")
            return 0
    
    def _safe_numeric(self, value):
        """Safely convert value to numeric"""
        try:
            if pd.isna(value):
                return 0
            return pd.to_numeric(value, errors='coerce')
        except (ValueError, TypeError):
            return 0
    
    def calculate_average_cost_of_sold_shares(self, info_map):
        """Calculate average cost of sold shares"""
        try:
            total_cost = 0.0
            total_shares = 0
            
            if self.config.BUY in info_map:
                # Process DataFrame group instead of list
                for _, transaction in info_map[self.config.BUY].iterrows():
                    try:
                        final_amount = float(transaction[TransDetails_constants.FINAL_AMOUNT]) if transaction[TransDetails_constants.FINAL_AMOUNT] is not None else 0.0
                        quantity = float(transaction[TransDetails_constants.QUANTITY]) if transaction[TransDetails_constants.QUANTITY] is not None else 0.0
                        total_cost += final_amount
                        total_shares += quantity
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid transaction data in average cost calculation: {transaction}")
                        continue
            
            if total_shares > 0:
                return total_cost / total_shares
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating average cost: {e}")
            return 0.0
    
    def is_long_term(self, buy_date, sell_date):
        """Check if holding period is long term (more than 1 year)"""
        try:
            buy_dt = datetime.strptime(buy_date, self.config.DATE_FORMAT)
            sell_dt = datetime.strptime(sell_date, self.config.DATE_FORMAT)
            return (sell_dt - buy_dt).days > 365
        except Exception as e:
            logger.error(f"Error checking long term: {e}")
            return False
    
    def update_intraday_count(self, data):
        """Update intraday count for transactions"""
        try:
            # Group by date and name
            grouped = data.groupby([Raw_constants.DATE, Raw_constants.NAME])
            
            for (date, name), group in grouped:
                buy_count = 0
                sell_count = 0
                
                for _, row in group.iterrows():
                    if row[TransDetails_constants.TRANSACTION_TYPE] == self.config.BUY:
                        buy_count += 1
                    elif row[TransDetails_constants.TRANSACTION_TYPE] == self.config.SELL:
                        sell_count += 1
                
                # Update intraday count
                mask = (data[Raw_constants.DATE] == date) & (data[Raw_constants.NAME] == name)
                data.loc[mask, TransDetails_constants.INTRADAY_COUNT] = min(buy_count, sell_count)
            
            return data
            
        except Exception as e:
            logger.error(f"Error updating intraday count: {e}")
            return data
    
    def convert_dtypes(self, df):
        """Convert data types in dataframe"""
        try:
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        converted_col = df[col].astype(str)
                        converted_col = converted_col.str.replace(',', '', regex=False)
                        converted_col = pd.to_numeric(converted_col, errors='raise')
                        df[col] = converted_col
                    except ValueError:
                        pass
            return df
        except Exception as e:
            logger.error(f"Error converting data types: {e}")
            return df 
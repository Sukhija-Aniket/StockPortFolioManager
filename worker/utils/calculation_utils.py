from datetime import datetime
import logging
import pandas as pd
from stock_portfolio_shared.constants.raw_constants import Raw_constants
from stock_portfolio_shared.constants.trans_details_constants import TransDetails_constants
from stock_portfolio_shared.utils.data_processor import DataProcessor
from config import Config
from utils.logging_config import setup_logging
logger = setup_logging(__name__)
config = Config()

def calculate_stt(row):
    """Calculate Securities Transaction Tax"""
    try:
        net_amount = DataProcessor.safe_numeric(row[TransDetails_constants.NET_AMOUNT])
        if row[TransDetails_constants.TRANSACTION_TYPE] == config.BUY:
            return abs(net_amount * 0.0005)
        else:
            return abs(net_amount * 0.0005)
    except Exception as e:
        logger.error(f"Error calculating STT: {e}")
        return 0

def calculate_transaction_charges(row):
    """Calculate SEBI transaction charges"""
    try:
        net_amount = DataProcessor.safe_numeric(row[TransDetails_constants.NET_AMOUNT])
        return abs(net_amount * 0.000001)
    except Exception as e:
        logger.error(f"Error calculating transaction charges: {e}")
        return 0

def calculate_brokerage(row):
    """Calculate brokerage charges"""
    try:
        # Simple brokerage calculation - can be customized based on broker
        net_amount = DataProcessor.safe_numeric(row[TransDetails_constants.NET_AMOUNT])
        return abs(net_amount * 0.0005)
    except Exception as e:
        logger.error(f"Error calculating brokerage: {e}")
        return 0

def calculate_stamp_duty(row):
    """Calculate stamp duty"""
    try:
        net_amount = DataProcessor.safe_numeric(row[TransDetails_constants.NET_AMOUNT])
        return abs(net_amount * 0.00015)
    except Exception as e:
        logger.error(f"Error calculating stamp duty: {e}")
        return 0

def calculate_dp_charges(row, dp_data=None):
    """Calculate DP charges"""
    try:
        # Default DP charges - can be customized
        quantity = DataProcessor.safe_numeric(row[TransDetails_constants.QUANTITY])
        return 13.5 if quantity > 0 else 0
    except Exception as e:
        logger.error(f"Error calculating DP charges: {e}")
        return 0

def calculate_average_cost_of_sold_shares(info_map):
    """Calculate average cost of sold shares"""
    try:
        total_cost = 0.0
        total_shares = 0
        
        if config.BUY in info_map:
            # Process DataFrame group instead of list
            for _, transaction in info_map[config.BUY].iterrows():
                try:
                    final_amount = DataProcessor.safe_numeric(transaction[TransDetails_constants.FINAL_AMOUNT])
                    quantity = DataProcessor.safe_numeric(transaction[TransDetails_constants.QUANTITY])
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

def is_long_term(buy_date, sell_date):
    """Check if holding period is long term (more than 1 year)"""
    try:
        buy_dt = datetime.strptime(buy_date, config.DATA_TIME_FORMAT)
        sell_dt = datetime.strptime(sell_date, config.DATA_TIME_FORMAT)
        return (sell_dt - buy_dt).days > 365
    except Exception as e:
        logger.error(f"Error checking long term: {e}")
        return False

def update_intraday_count(data):
    """Update intraday count for transactions"""
    try:
        # Group by date and name
        grouped = data.groupby([Raw_constants.DATE, Raw_constants.NAME])
        
        for (date, name), group in grouped:
            buy_count = 0
            sell_count = 0
            
            for _, row in group.iterrows():
                if row[TransDetails_constants.TRANSACTION_TYPE] == config.BUY:
                    buy_count += 1
                elif row[TransDetails_constants.TRANSACTION_TYPE] == config.SELL:
                    sell_count += 1
            
            # Update intraday count
            mask = (data[Raw_constants.DATE] == date) & (data[Raw_constants.NAME] == name)
            data.loc[mask, TransDetails_constants.INTRADAY_COUNT] = min(buy_count, sell_count)
        
        return data
        
    except Exception as e:
        logger.error(f"Error updating intraday count: {e}")
        return data

def update_transaction_type(quantity):
    """
    Determine transaction type based on quantity
    
    Args:
        quantity: The quantity value (positive = BUY, negative = SELL)
        
    Returns:
        str: 'BUY' or 'SELL'
    """
    try:
        # Convert to integer and check if positive or negative
        quantity_int = DataProcessor.safe_numeric(quantity)
        
        if quantity_int >= 0:
            return config.BUY
        else:
            return config.SELL
            
    except (ValueError, TypeError) as e:
        logger.error(f"Error determining transaction type for quantity {quantity}: {e}")
        # Default to BUY on error
        return config.BUY

def convert_dtypes(df):
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
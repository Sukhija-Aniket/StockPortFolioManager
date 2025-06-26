from datetime import datetime
import pandas as pd
from stock_portfolio_shared.constants.raw_constants import Raw_constants
from stock_portfolio_shared.constants.trans_details_constants import TransDetails_constants
from stock_portfolio_shared.utils.data_processor import DataProcessor
from worker.config.config import Config
from worker.config.logging_config import setup_logging
from worker.config.participant_config_manager import ParticipantConfigManager

logger = setup_logging(__name__)
config = Config()

# Initialize participant config manager
participant_config_manager = ParticipantConfigManager()

#
# intraDay_charges, delivery_charges = 0, 0
#     delivery_charges = (abs(row[Raw_constants.QUANTITY]) -
#                         row[TransDetails_constants.INTRADAY_COUNT]) * 0.001 * row[Raw_constants.PRICE]
#     if row[TransDetails_constants.TRANSACTION_TYPE] == SELL:
#         intraDay_charges = row[TransDetails_constants.INTRADAY_COUNT] * \
#             0.00025 * row[Raw_constants.PRICE]
#     return intraDay_charges + delivery_charges 
# 
def calculate_stt(row, participant_name: str = "zerodha"):
    """Calculate Securities Transaction Tax with participant-specific rates"""
    intraday_charges, delivery_charges = 0.0, 0.0
    try:
        # Get participant-specific STT rates
        delivery_rate = participant_config_manager.get_stt_rate(participant_name, is_intraday=False)
        intraday_rate = participant_config_manager.get_stt_rate(participant_name, is_intraday=True)
        
        # Calculate delivery charges (non-intraday portion)
        delivery_quantity = abs(row[Raw_constants.QUANTITY]) - row[TransDetails_constants.INTRADAY_COUNT]
        delivery_charges = delivery_quantity * delivery_rate * row[Raw_constants.PRICE]
        
        # Calculate intraday charges (only for SELL transactions)
        if row[TransDetails_constants.TRANSACTION_TYPE] == config.SELL:
            intraday_charges = row[TransDetails_constants.INTRADAY_COUNT] * intraday_rate * row[Raw_constants.PRICE]
        
        return intraday_charges + delivery_charges 
    except Exception as e:
        logger.error(f"Error calculating STT for {participant_name}: {e}")
        raise

def calculate_transaction_charges(row, participant_name: str = "zerodha"):
    """Calculate SEBI transaction charges with participant-specific rates"""
    try:
        net_amount = DataProcessor.safe_numeric(row[TransDetails_constants.NET_AMOUNT])
        rate = participant_config_manager.get_transaction_charges_rate(participant_name)
        return abs(net_amount * rate)
    except Exception as e:
        logger.error(f"Error calculating transaction charges for {participant_name}: {e}")
        raise

def calculate_brokerage(row, participant_name: str = "zerodha"):
    """Calculate brokerage charges with participant-specific rates"""
    try:
        net_amount = DataProcessor.safe_numeric(row[TransDetails_constants.NET_AMOUNT])
        brokerage_config = participant_config_manager.get_brokerage_rate(participant_name)
        
        if brokerage_config.get("type") == "percentage":
            rate = brokerage_config.get("rate", 0.0005)
            max_amount = brokerage_config.get("max_amount", 20.0)
            
            # Calculate percentage-based brokerage with maximum cap
            brokerage = abs(net_amount * rate)
            return min(brokerage, max_amount)
        else:
            # Fixed brokerage
            return brokerage_config.get("fixed_amount", 20.0)
            
    except Exception as e:
        logger.error(f"Error calculating brokerage for {participant_name}: {e}")
        raise

def calculate_stamp_duty(row, participant_name: str = "zerodha"):
    """Calculate stamp duty with participant-specific rates"""
    try:
        net_amount = DataProcessor.safe_numeric(row[TransDetails_constants.NET_AMOUNT])
        rate = participant_config_manager.get_stamp_duty_rate(participant_name)
        return abs(net_amount * rate)
    except Exception as e:
        logger.error(f"Error calculating stamp duty for {participant_name}: {e}")
        raise

def calculate_dp_charges(row, participant_name: str = "zerodha"):
    """Calculate DP charges with participant-specific rates"""
    try:
        quantity = DataProcessor.safe_numeric(row[TransDetails_constants.QUANTITY])
        dp_charges = participant_config_manager.get_dp_charges(participant_name)
        return dp_charges if quantity > 0 else 0
    except Exception as e:
        logger.error(f"Error calculating DP charges for {participant_name}: {e}")
        raise

def calculate_exchange_transaction_charges(row, participant_name: str = "zerodha"):
    """Calculate exchange transaction charges with participant-specific rates"""
    try:
        net_amount = DataProcessor.safe_numeric(row[TransDetails_constants.NET_AMOUNT])
        rate = participant_config_manager.get_exchange_transaction_charges_rate(participant_name)
        return abs(net_amount * rate)
    except Exception as e:
        logger.error(f"Error calculating exchange transaction charges for {participant_name}: {e}")
        raise

def calculate_gst(row, participant_name: str = "zerodha"):
    """Calculate GST with participant-specific rates"""
    try:
        # GST is calculated on brokerage + transaction charges + exchange charges
        brokerage = calculate_brokerage(row, participant_name)
        transaction_charges = calculate_transaction_charges(row, participant_name)
        exchange_charges = calculate_exchange_transaction_charges(row, participant_name)
        
        gst_rate = participant_config_manager.get_gst_rate(participant_name)
        return abs(gst_rate * (brokerage + transaction_charges + exchange_charges))
    except Exception as e:
        logger.error(f"Error calculating GST for {participant_name}: {e}")
        raise

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

def get_financial_year(date):
    """
    Get financial year for a given date
    FY starts from 1st April and ends on 31st March next year
    Example: FY 2021-22 means 1st April 2021 to 31st March 2022
    """
    try:
        if isinstance(date, str):
            date = pd.to_datetime(date)
        
        year = date.year
        month = date.month
        
        # If month is April to December, it's FY year-year+1
        # If month is January to March, it's FY year-1-year
        if month >= 4:  # April to December
            fy_start = year
            fy_end = year + 1
        else:  # January to March
            fy_start = year - 1
            fy_end = year
            
        return f"FY {fy_start}-{str(fy_end)[-2:]}"  # FY 2021-22 format
    except Exception as e:
        logger.error(f"Error getting financial year for date {date}: {e}")
        return "FY Unknown"
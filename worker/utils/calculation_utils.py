from datetime import datetime
import pandas as pd
from stock_portfolio_shared.constants.general_constants import BUY, SELL
from stock_portfolio_shared.constants.raw_constants import Raw_constants
from stock_portfolio_shared.constants.trans_details_constants import TransDetails_constants
from stock_portfolio_shared.utils.data_processor import DataProcessor
from config.config import Config
from config.logging_config import setup_logging
from config.participant_config_manager import ParticipantConfigManager

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

def calculate_exchange_transaction_charges(row, participant_name: str = "zerodha"):
    """Calculate SEBI transaction charges with participant-specific rates"""
    try:
        net_amount = row[Raw_constants.NET_AMOUNT]
        exchange = row[Raw_constants.STOCK_EXCHANGE]
        rate = participant_config_manager.get_exchange_transaction_charges_rate(participant_name, exchange)
        return abs(net_amount * rate)
    except Exception as e:
        logger.error(f"Error calculating exchange transaction charges for {participant_name}: {e}")
        raise

def calculate_brokerage(row, participant_name: str = "zerodha"):
    """Calculate brokerage charges with participant-specific rates"""
    try:
        net_amount = row[Raw_constants.NET_AMOUNT]
        intraday_brokerage_rate = participant_config_manager.get_brokerage_rate(participant_name, is_intraday=True)
        delivery_brokerage_rate = participant_config_manager.get_brokerage_rate(participant_name, is_intraday=False)
        delivery_quantity = abs(row[Raw_constants.QUANTITY]) - row[TransDetails_constants.INTRADAY_COUNT]
        delivery_brokerage = min(delivery_quantity * delivery_brokerage_rate["rate"] * row[Raw_constants.PRICE], delivery_brokerage_rate["max_amount"])
        intraday_brokerage = min(row[TransDetails_constants.INTRADAY_COUNT] * intraday_brokerage_rate["rate"] * row[Raw_constants.PRICE], intraday_brokerage_rate["max_amount"])
        return intraday_brokerage + delivery_brokerage
            
    except Exception as e:
        logger.error(f"Error calculating brokerage for {participant_name}: {e}")
        raise

def calculate_stamp_duty(row, participant_name: str = "zerodha"):
    """Calculate stamp duty with participant-specific rates"""
    try:
        delivery_rate = participant_config_manager.get_stamp_duty_rate(participant_name, is_intraday=False)
        intraday_rate = participant_config_manager.get_stamp_duty_rate(participant_name, is_intraday=True)
        
        delivery_quantity = abs(row[Raw_constants.QUANTITY]) - row[TransDetails_constants.INTRADAY_COUNT]
        delivery_charges = delivery_quantity * delivery_rate * row[Raw_constants.PRICE]
        
        intraday_charges = row[TransDetails_constants.INTRADAY_COUNT] * intraday_rate * row[Raw_constants.PRICE]
        
        return intraday_charges + delivery_charges
    except Exception as e:
        logger.error(f"Error calculating stamp duty for {participant_name}: {e}")
        raise

def calculate_dp_charges(row, dp_data, participant_name: str = "zerodha"):
    """Calculate DP charges with participant-specific rates"""
    try:
        if row[TransDetails_constants.TRANSACTION_TYPE] == config.SELL and (abs(row[Raw_constants.QUANTITY]) - row[TransDetails_constants.INTRADAY_COUNT]) > 0:
        
            # Only apply DP charges for delivery transactions (non-intraday)
            name = row[Raw_constants.NAME]
            date = row[Raw_constants.DATE]
            
            # Initialize name in dp_data if not exists
            if name not in dp_data:
                dp_data[name] = {}
            
            # Check if DP charges already applied for this name/date combination
            if date not in dp_data[name]:
                # First time seeing this name/date combination - apply DP charges
                dp_charges = participant_config_manager.get_dp_charges(participant_name)
                dp_data[name][date] = dp_charges
                return dp_charges
            else:
                # DP charges already applied for this name/date combination - return 0
                return 0
        else:
            # No delivery quantity - no DP charges
            return 0
            
    except Exception as e:
        logger.error(f"Error calculating DP charges for {participant_name}: {e}")
        raise

def calculate_sebi_transaction_charges(row, participant_name: str = "zerodha"):
    """Calculate exchange transaction charges with participant-specific rates"""
    try:
        net_amount = row[Raw_constants.NET_AMOUNT]
        rate = participant_config_manager.get_sebi_transaction_charges_rate(participant_name)
        return abs(net_amount * rate)
    except Exception as e:
        logger.error(f"Error calculating transaction charges for {participant_name}: {e}")
        raise

def calculate_gst(row, participant_name: str = "zerodha"):
    """Calculate GST with participant-specific rates"""
    try:
        # GST is calculated on brokerage + transaction charges + exchange charges
        brokerage = row[TransDetails_constants.BROKERAGE]
        dp_charges = row[TransDetails_constants.DP_CHARGES]
        exchange_charges = row[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES]
        gst_rate = participant_config_manager.get_gst_rate(participant_name)
        return abs(gst_rate * (brokerage + dp_charges + exchange_charges))
    except Exception as e:
        logger.error(f"Error calculating GST for {participant_name}: {e}")
        raise

def calculate_average_cost_of_sold_shares(infoMap: pd.DataFrame) -> float:
    logger.info(f"Calculating average cost of sold shares")
    try:
        sold_list = infoMap[SELL]
        buy_list = infoMap[BUY]

        j = 0
        price = 0
        intraCount = 0
        delCount = 0
        counter = 0

        logger.info(f"Calculating for IntraDay Orders")
        # Calculating for IntraDay Orders
        for i in range(0, len(sold_list)):
            sold_list[i][Raw_constants.QUANTITY] = abs(sold_list[i][Raw_constants.QUANTITY])
            sold_list[i][TransDetails_constants.FINAL_AMOUNT] = abs(sold_list[i][TransDetails_constants.FINAL_AMOUNT])
            if j >= len(buy_list):
                break
            if buy_list[j][Raw_constants.DATE] == sold_list[i][Raw_constants.DATE]:
                if buy_list[j][Raw_constants.QUANTITY] < sold_list[i][Raw_constants.QUANTITY]:
                    intraCount += buy_list[j][Raw_constants.QUANTITY]
                    sold_list[i][Raw_constants.QUANTITY] -= buy_list[j][Raw_constants.QUANTITY]
                    price += buy_list[j][TransDetails_constants.FINAL_AMOUNT]
                    buy_list[j][Raw_constants.QUANTITY] = 0
                    buy_list[j][TransDetails_constants.FINAL_AMOUNT] = 0
                    j += 1
                    i -= 1
                elif buy_list[j][Raw_constants.QUANTITY] > sold_list[i][Raw_constants.QUANTITY]:
                    price += ((buy_list[j][TransDetails_constants.FINAL_AMOUNT] * sold_list[i][Raw_constants.QUANTITY])/buy_list[j][Raw_constants.QUANTITY])
                    buy_list[j][TransDetails_constants.FINAL_AMOUNT] -= ((buy_list[j][TransDetails_constants.FINAL_AMOUNT] *
                                        sold_list[i][Raw_constants.QUANTITY])/buy_list[j][Raw_constants.QUANTITY])
                    buy_list[j][Raw_constants.QUANTITY] -= sold_list[i][Raw_constants.QUANTITY]
                    intraCount += sold_list[i][Raw_constants.QUANTITY]
                    sold_list[i][Raw_constants.QUANTITY] = 0
                else:
                    intraCount += sold_list[i][Raw_constants.QUANTITY]
                    sold_list[i][Raw_constants.QUANTITY] = 0
                    price += buy_list[j][TransDetails_constants.FINAL_AMOUNT]
                    buy_list[j][Raw_constants.QUANTITY] = 0
                    buy_list[j][TransDetails_constants.FINAL_AMOUNT] = 0
                    j += 1
            elif buy_list[j][Raw_constants.DATE] < sold_list[i][Raw_constants.DATE]:
                i -= 1
                j += 1

        
        # Calculating for Delivery Orders
        for x in sold_list:
            delCount += x[Raw_constants.QUANTITY]
        for x in buy_list:
            if x[Raw_constants.QUANTITY] <= (delCount - counter):
                price += x[TransDetails_constants.FINAL_AMOUNT]
                counter += x[Raw_constants.QUANTITY]
            else:
                price += (x[TransDetails_constants.FINAL_AMOUNT] * (delCount - counter))/x[Raw_constants.QUANTITY]
                counter = delCount
        counter += intraCount

        return price/counter
    except Exception as e:
        logger.error(f"Error calculating average cost of sold shares: {e}")
        raise



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
"""
Stock Portfolio Shared Library

Shared utilities and constants for the Stock Portfolio Manager application.
"""

__version__ = "0.1.1"
__author__ = "Stock Portfolio Manager"

# Import specific constants from individual files using relative imports
from .constants.general_constants import (
    BUY, SELL, DEFAULT_DATE, BSE, NSE, YFINANCE_DATE_FORMAT,
    ORDER_TIME_FORMAT, DATA_TIME_FORMAT, GLOBAL_QUOTE, COMPLETE,
    DOT_NS, DOT_BO, CELL_RANGE
)
from .constants.raw_constants import Raw_constants
from .constants.trans_details_constants import TransDetails_constants
from .constants.share_profit_loss_constants import ShareProfitLoss_constants
from .constants.daily_profit_loss_constants import DailyProfitLoss_constants
from .constants.taxation_constants import Taxation_constants
from .constants.data_constants import Data_constants
from .constants.order_constants import Order_constants

from .utils.sheet_manager import SheetsManager
from .utils.excel_manager import ExcelManager
from .utils.data_processor import DataProcessor

__all__ = [
    # Constants
    "BUY", "SELL", "DEFAULT_DATE", "BSE", "NSE", "YFINANCE_DATE_FORMAT",
    "ORDER_TIME_FORMAT", "DATA_TIME_FORMAT", "GLOBAL_QUOTE", "COMPLETE",
    "DOT_NS", "DOT_BO", "CELL_RANGE",
    "Raw_constants", "TransDetails_constants", "ShareProfitLoss_constants",
    "DailyProfitLoss_constants", "Taxation_constants", "Data_constants", "Order_constants",
    # Utilities
    "SheetsManager",
    "ExcelManager", 
    "DataProcessor",
] 
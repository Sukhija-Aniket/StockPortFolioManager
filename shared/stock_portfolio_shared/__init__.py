"""
Stock Portfolio Shared Library

Shared utilities and constants for the Stock Portfolio Manager application.
"""

__version__ = "0.1.1"
__author__ = "Stock Portfolio Manager"

# Import specific constants from individual files using absolute imports
from stock_portfolio_shared.constants.general_constants import (
    BUY, SELL, DEFAULT_DATE, BSE, NSE, YFINANCE_DATE_FORMAT,
    ORDER_TIME_FORMAT, DATA_TIME_FORMAT, GLOBAL_QUOTE, COMPLETE,
    DOT_NS, DOT_BO, CELL_RANGE
)
from stock_portfolio_shared.constants.raw_constants import Raw_constants
from stock_portfolio_shared.constants.trans_details_constants import TransDetails_constants
from stock_portfolio_shared.constants.share_profit_loss_constants import ShareProfitLoss_constants
from stock_portfolio_shared.constants.daily_profit_loss_constants import DailyProfitLoss_constants
from stock_portfolio_shared.constants.taxation_constants import Taxation_constants
from stock_portfolio_shared.constants.data_constants import Data_constants
from stock_portfolio_shared.constants.order_constants import Order_constants

from stock_portfolio_shared.utils.sheet_manager import SheetsManager
from stock_portfolio_shared.utils.excel_manager import ExcelManager
from stock_portfolio_shared.utils.data_processor import DataProcessor

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
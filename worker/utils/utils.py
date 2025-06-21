import pandas as pd
import logging
from stock_portfolio_shared.utils.sheet_manager import SheetsManager
from stock_portfolio_shared.utils.excel_manager import ExcelManager
from stock_portfolio_shared.utils.data_processor import DataProcessor
from stock_portfolio_shared.utils.common_utils import CommonUtils

logger = logging.getLogger(__name__)

# Initialize managers and processors from shared library
sheets_manager = SheetsManager()
excel_manager = ExcelManager()
data_processor = DataProcessor()
common_utils = CommonUtils()
"""
Stock Portfolio Shared Library

Shared utilities and constants for the Stock Portfolio Manager application.
"""

__version__ = "0.1.0"
__author__ = "Stock Portfolio Manager"

from .constants import *
from .utils.sheet_manager import SheetsManager
from .utils.excel_manager import ExcelManager
from .utils.data_processor import DataProcessor

__all__ = [
    "SheetsManager",
    "ExcelManager", 
    "DataProcessor",
] 
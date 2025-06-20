"""
Stock Portfolio Shared Library

Shared utilities and constants for the Stock Portfolio Manager application.
"""

__version__ = "0.1.0"
__author__ = "Stock Portfolio Manager"

from .constants import *
from .utils.sheets import SheetsManager
from .utils.excel import ExcelManager
from .utils.data_processing import DataProcessor

__all__ = [
    "SheetsManager",
    "ExcelManager", 
    "DataProcessor",
] 
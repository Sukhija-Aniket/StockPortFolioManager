"""
Transaction Details constants for Stock Portfolio Manager
"""

from .raw_constants import Raw_constants

class TransDetails_constants(Raw_constants):
    # Inherits all fields from Raw_constants:
    # - DATE = 'Date'
    # - NAME = 'Name' 
    # - PRICE = 'Price'
    # - QUANTITY = 'Quantity'
    # - NET_AMOUNT = 'Net Amount'
    # - STOCK_EXCHANGE = 'Stock Exchange'
    
    # Additional processed fields:
    TRANSACTION_TYPE = 'Transaction Type'
    INTRADAY_COUNT = 'Intraday Count'
    STT = 'STT'
    SEBI_TRANSACTION_CHARGES = 'SEBI Transaction Charges'
    EXCHANGE_TRANSACTION_CHARGES = 'Exchange Transaction Charges'
    BROKERAGE = 'Brokerage'
    STAMP_DUTY = 'Stamp Duty'
    DP_CHARGES = 'DP_Charges'
    GST = 'GST'
    FINAL_AMOUNT = 'Final Amount' 
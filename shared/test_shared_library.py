#!/usr/bin/env python3
"""
Test script to verify shared library functionality
"""

import sys
import os

# Add the shared library to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_shared_library():
    """Test the shared library functionality"""
    print("Testing Stock Portfolio Shared Library...")
    
    try:
        # Test imports
        from stock_portfolio_shared.constants.general_constants import BUY, SELL, DATE_FORMAT
        print("✅ Constants imported successfully")
        
        from stock_portfolio_shared.utils.sheet_manager import SheetsManager
        print("✅ SheetsManager imported successfully")
        
        from stock_portfolio_shared.utils.excel_manager import ExcelManager
        print("✅ ExcelManager imported successfully")
        
        from stock_portfolio_shared.utils.data_processor import DataProcessor
        print("✅ DataProcessor imported successfully")
        
        # Test constants
        print(f"✅ BUY constant: {BUY}")
        print(f"✅ SELL constant: {SELL}")
        print(f"✅ DATE_FORMAT constant: {DATE_FORMAT}")
        
        # Test classes
        sheets_manager = SheetsManager()
        print("✅ SheetsManager instantiated successfully")
        
        excel_manager = ExcelManager()
        print("✅ ExcelManager instantiated successfully")
        
        data_processor = DataProcessor()
        print("✅ DataProcessor instantiated successfully")
        
        # Test data processing methods
        test_data = {
            'symbol': 'RELIANCE-EQ',
            'trade_date': '2025-06-19',
            'quantity': '100',
            'price': '2500.50',
            'trade_type': 'BUY',
            'exchange': 'NSE'
        }
        
        symbol = DataProcessor.get_symbol(test_data)
        print(f"✅ get_symbol result: {symbol}")
        
        date_str = DataProcessor.get_data_date('2025-06-19')
        print(f"✅ get_data_date result: {date_str}")
        
        print("\n🎉 All tests passed! Shared library is working correctly.")
        
    except Exception as e:
        print(f"❌ Error testing shared library: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_shared_library()
    sys.exit(0 if success else 1) 
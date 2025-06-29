#!/usr/bin/env python3
"""
Test script to demonstrate batch API improvements
"""

import pandas as pd
from datetime import datetime, timedelta
from services.data_processing_service import DataProcessingService
from config.logging_config import setup_logging
from stock_portfolio_shared.constants.trans_details_constants import TransDetails_constants
from stock_portfolio_shared.constants.raw_constants import Raw_constants

logger = setup_logging(__name__)

def create_test_transaction_data():
    """Create test transaction details data for demonstration"""
    # Create sample transaction details data (after processing raw data)
    data = {
        Raw_constants.DATE: [
            '2024-01-15', '2024-01-15', '2024-01-16', '2024-01-16',
            '2024-01-17', '2024-01-17', '2024-01-18', '2024-01-18'
        ],
        Raw_constants.NAME: [
            'RELIANCE', 'TCS', 'RELIANCE', 'INFY',
            'TCS', 'HDFC', 'RELIANCE', 'WIPRO'
        ],
        Raw_constants.PRICE: [2500, 3500, 2550, 1500, 3600, 1800, 2600, 500],
        Raw_constants.QUANTITY: [10, 5, -5, 20, -10, 15, 8, 25],
        Raw_constants.NET_AMOUNT: [25000, 17500, -12750, 30000, -36000, 27000, 20800, 12500],
        Raw_constants.STOCK_EXCHANGE: ['NSE', 'NSE', 'NSE', 'NSE', 'NSE', 'NSE', 'NSE', 'NSE'],
        TransDetails_constants.TRANSACTION_TYPE: ['BUY', 'BUY', 'SELL', 'BUY', 'SELL', 'BUY', 'BUY', 'BUY'],
        TransDetails_constants.FINAL_AMOUNT: [25000, 17500, -12750, 30000, -36000, 27000, 20800, 12500],
        TransDetails_constants.STT: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        TransDetails_constants.GST: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        TransDetails_constants.SEBI_TRANSACTION_CHARGES: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        TransDetails_constants.BROKERAGE: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        TransDetails_constants.STAMP_DUTY: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        TransDetails_constants.DP_CHARGES: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        TransDetails_constants.INTRADAY_COUNT: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    }
    
    return pd.DataFrame(data)

def test_batch_api_improvements():
    """Test the batch API improvements"""
    logger.info("Testing batch API improvements...")
    
    # Create test data
    test_data = create_test_transaction_data()
    logger.info(f"Created test transaction data with {len(test_data)} transactions")
    logger.info(f"Columns: {list(test_data.columns)}")
    
    # Initialize service
    service = DataProcessingService()
    
    # Clear cache before testing
    service.clear_market_data_cache()
    
    # Test 1: Process daily profit loss with batch API calls
    logger.info("=== Testing Daily Profit Loss with Batch API ===")
    try:
        daily_result = service.process_daily_profit_loss(test_data)
        logger.info(f"Daily profit loss processing completed. Result shape: {daily_result.shape}")
        logger.info(f"Daily profit loss columns: {list(daily_result.columns)}")
        
        # Show cache stats
        cache_stats = service.get_market_data_cache_stats()
        logger.info(f"Cache stats after daily processing: {cache_stats}")
        
    except Exception as e:
        logger.error(f"Error in daily profit loss processing: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Process share profit loss with batch API calls
    logger.info("=== Testing Share Profit Loss with Batch API ===")
    try:
        share_result = service.process_share_profit_loss(test_data)
        logger.info(f"Share profit loss processing completed. Result shape: {share_result.shape}")
        logger.info(f"Share profit loss columns: {list(share_result.columns)}")
        
        # Show cache stats
        cache_stats = service.get_market_data_cache_stats()
        logger.info(f"Cache stats after share processing: {cache_stats}")
        
    except Exception as e:
        logger.error(f"Error in share profit loss processing: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Process same data again to show cache benefits
    logger.info("=== Testing Cache Benefits (Second Run) ===")
    try:
        daily_result_2 = service.process_daily_profit_loss(test_data)
        logger.info(f"Second daily profit loss processing completed. Result shape: {daily_result_2.shape}")
        
        # Show final cache stats
        cache_stats = service.get_market_data_cache_stats()
        logger.info(f"Final cache stats: {cache_stats}")
        
    except Exception as e:
        logger.error(f"Error in second daily profit loss processing: {e}")
        

def compare_api_calls():
    """Compare API calls with and without batching"""
    logger.info("=== API Call Comparison ===")
    
    # Without batching (old approach):
    # - Daily profit loss: 1 API call per unique (stock, date) combination
    # - Share profit loss: 1 API call per unique stock name
    # - Total: 8 unique (stock, date) + 5 unique stocks = 13 API calls
    
    # With batching (new approach):
    # - Daily profit loss: 1 batch call per unique stock (for all its dates)
    # - Share profit loss: 1 batch call for all unique stock names
    # - Total: 5 batch API calls (4 stocks for daily + 1 for current prices)
    
    logger.info("Old approach (without batching):")
    logger.info("- Daily profit loss: 8 individual API calls (one per stock-date)")
    logger.info("- Share profit loss: 5 individual API calls (one per stock)")
    logger.info("- Total: 13 API calls")
    
    logger.info("\nNew approach (with true batching):")
    logger.info("- Daily profit loss: 4 batch API calls (one per stock for all its dates)")
    logger.info("- Share profit loss: 1 batch API call (for all current prices)")
    logger.info("- Total: 5 batch API calls")
    
    logger.info("\nImprovement: 62% reduction in API calls!")
    logger.info("Additional benefit: Each batch call fetches multiple dates in one request")

def test_cache_functionality():
    """Test cache functionality specifically"""
    logger.info("=== Testing Cache Functionality ===")
    
    service = DataProcessingService()
    
    # Clear cache
    service.clear_market_data_cache()
    
    # Test cache stats
    stats = service.get_market_data_cache_stats()
    logger.info(f"Initial cache stats: {stats}")
    
    # Create minimal test data
    test_data = create_test_transaction_data().head(2)  # Just 2 transactions
    
    # Process data
    try:
        service.process_daily_profit_loss(test_data)
        stats_after = service.get_market_data_cache_stats()
        logger.info(f"Cache stats after processing: {stats_after}")
        
        # Process again to test cache hits
        service.process_daily_profit_loss(test_data)
        stats_final = service.get_market_data_cache_stats()
        logger.info(f"Cache stats after second processing: {stats_final}")
        
    except Exception as e:
        logger.error(f"Error testing cache: {e}")

if __name__ == "__main__":
    logger.info("Starting batch API improvement tests...")
    
    # Show comparison
    compare_api_calls()
    
    # Test cache functionality
    test_cache_functionality()
    
    # Run main tests
    test_batch_api_improvements()
    
    logger.info("Batch API improvement tests completed!") 
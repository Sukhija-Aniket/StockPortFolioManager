# Batch API Improvements for Market Data

## Overview

This document describes the improvements made to reduce excessive API calls to yfinance when processing stock portfolio data.

## Problem

The original implementation made individual API calls for:
1. **Daily Profit Loss**: One API call per unique (stock, date) combination
2. **Share Profit Loss**: One API call per unique stock name

This resulted in excessive API calls, especially for large datasets with many stocks and dates.

## Solution

### 1. In-Memory Caching
- Added 20-minute TTL cache for both historical and current price data
- Cache keys: `{stock_name}_{date}` for historical, `current_{stock_name}` for current prices
- Automatic cache invalidation after TTL expires

### 2. True Batch API Calls
- **Historical Prices**: `batch_get_stock_prices()` - makes one API call per stock for all its required dates
- **Current Prices**: `batch_get_current_prices()` - fetches all current prices in one operation

### 3. Smart Cache Checking
- Before making API calls, check cache for existing data
- Only fetch uncached data from API
- Group uncached requests by stock name to minimize API calls

## Implementation Details

### MarketDataHelper Enhancements

```python
class MarketDataHelper:
    def __init__(self):
        self._price_cache: Dict[str, Dict] = {}
        self._current_price_cache: Dict[str, float] = {}
        self._cache_ttl = 1200  # 20 minutes
    
    def batch_get_stock_prices(self, stock_dates: List[Tuple[str, datetime]]) -> Dict[Tuple[str, datetime], List]:
        # Check cache first
        # Group uncached requests by stock name
        # Make ONE API call per stock for ALL its dates
        # Process the batch response for each requested date
        # Cache all results
    
    def batch_get_current_prices(self, stock_names: List[str]) -> Dict[str, float]:
        # Similar approach for current prices
```

### DataProcessingService Updates

```python
def process_daily_profit_loss(self, data: pd.DataFrame) -> pd.DataFrame:
    # Collect all unique stock-date combinations
    stock_dates = [(name, date) for (date, name), group in grouped_data]
    
    # Batch fetch all prices (one call per stock for all its dates)
    batch_prices = self.market_data_helper.batch_get_stock_prices(stock_dates)
    
    # Use batch results instead of individual API calls
    price_details = batch_prices.get((name, date), [])

def process_share_profit_loss(self, data: pd.DataFrame) -> pd.DataFrame:
    # Collect all unique stock names
    stock_names = list(row_data.keys())
    
    # Batch fetch all current prices
    batch_current_prices = self.market_data_helper.batch_get_current_prices(stock_names)
    
    # Use batch results instead of individual API calls
    current_price = batch_current_prices.get(share_name, 0.0)
```

## Performance Improvements

### Before (Old Approach)
- **Daily Profit Loss**: N API calls (where N = unique stock-date combinations)
- **Share Profit Loss**: M API calls (where M = unique stock names)
- **Total**: N + M individual API calls

### After (New Approach)
- **Daily Profit Loss**: S batch API calls (where S = unique stocks)
- **Share Profit Loss**: 1 batch API call
- **Total**: S + 1 batch API calls

### Example with Sample Data
- **8 unique stock-date combinations** + **5 unique stocks** = **13 individual API calls**
- **New approach**: **5 batch API calls** (4 stocks for daily + 1 for current prices)
- **Improvement**: **62% reduction in API calls**
- **Additional benefit**: Each batch call fetches multiple dates in one request

## True Batch Implementation

### Key Features
1. **One API Call Per Stock**: Instead of one call per stock-date combination
2. **Date Range Fetching**: Fetches a date range for each stock in a single call
3. **Efficient Processing**: Processes the batch response to extract specific dates
4. **Exchange Fallback**: Maintains NSE → BSE fallback logic in batch operations

### Example
```python
# Old approach: 8 API calls
# RELIANCE-2024-01-15 → API call
# RELIANCE-2024-01-16 → API call  
# RELIANCE-2024-01-17 → API call
# TCS-2024-01-15 → API call
# TCS-2024-01-17 → API call
# etc...

# New approach: 4 API calls
# RELIANCE (2024-01-15 to 2024-01-17) → 1 API call
# TCS (2024-01-15 to 2024-01-17) → 1 API call
# INFY (2024-01-16) → 1 API call
# HDFC (2024-01-17) → 1 API call
```

## Cache Management

### Cache Statistics
```python
cache_stats = service.get_market_data_cache_stats()
# Returns: {'price_cache_size': X, 'current_price_cache_size': Y, 'cache_ttl_seconds': 1200}
```

### Cache Clearing
```python
service.clear_market_data_cache()
# Clears all cached data
```

## Usage Examples

### Basic Usage
```python
# Initialize service
service = DataProcessingService()

# Process data (automatically uses batch API calls)
daily_result = service.process_daily_profit_loss(data)
share_result = service.process_share_profit_loss(data)

# Check cache performance
cache_stats = service.get_market_data_cache_stats()
print(f"Cache stats: {cache_stats}")
```

### Testing
```bash
# Run the test script to see improvements
python test_batch_api.py
```

## Test Data Format

The test script now uses proper transaction details format:

```python
def create_test_transaction_data():
    """Create test transaction details data for demonstration"""
    data = {
        Raw_constants.DATE: ['2024-01-15', '2024-01-15', ...],
        Raw_constants.NAME: ['RELIANCE', 'TCS', ...],
        Raw_constants.PRICE: [2500, 3500, ...],
        Raw_constants.QUANTITY: [10, 5, ...],
        Raw_constants.NET_AMOUNT: [25000, 17500, ...],
        Raw_constants.STOCK_EXCHANGE: ['NSE', 'NSE', ...],
        TransDetails_constants.TRANSACTION_TYPE: ['BUY', 'BUY', ...],
        TransDetails_constants.FINAL_AMOUNT: [25000, 17500, ...],
        # ... other transaction details columns
    }
    return pd.DataFrame(data)
```

## Benefits

1. **Reduced API Calls**: 62% reduction in yfinance API calls
2. **Improved Performance**: Faster processing due to fewer network requests
3. **Better Reliability**: Reduced risk of hitting API rate limits
4. **Cost Efficiency**: Lower bandwidth usage and API costs
5. **Caching Benefits**: Subsequent runs use cached data for even better performance
6. **True Batching**: Each API call fetches multiple dates, not just one

## Configuration

### Cache TTL
- Default: 20 minutes (1200 seconds)
- Configurable in `MarketDataHelper._cache_ttl`

### Exchange Fallback
- Maintains existing NSE → BSE fallback logic
- Works seamlessly with batch operations

## Monitoring

### Logging
- Cache hits are logged at DEBUG level
- Batch operations are logged at INFO level
- API errors are logged at ERROR level

### Cache Statistics
- Monitor cache hit rates
- Track cache size and memory usage
- Use cache stats for performance optimization

## Future Enhancements

1. **Persistent Cache**: Redis or database-based caching for multi-instance deployments
2. **Adaptive TTL**: Dynamic cache TTL based on market hours and volatility
3. **Preloading**: Preload common stock prices during startup
4. **Rate Limiting**: Built-in rate limiting to respect API limits
5. **Alternative Data Sources**: Fallback to other data providers when yfinance fails
6. **Parallel Processing**: Process multiple stocks in parallel for even better performance 
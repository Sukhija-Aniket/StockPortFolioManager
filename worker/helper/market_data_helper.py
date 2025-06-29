import yfinance as yf
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from config.config import Config

logger = logging.getLogger(__name__)

class MarketDataHelper:
    """Service for fetching market data and stock prices"""
    
    # Exchange configuration with priority order
    EXCHANGES = [
        {'suffix': '.NS', 'name': 'NSE', 'priority': 1},
        {'suffix': '.BO', 'name': 'BSE', 'priority': 2}
    ]
    
    def __init__(self):
        self.config = Config()
        # Cache for storing fetched data
        self._price_cache: Dict[str, Dict] = {}
        self._current_price_cache: Dict[str, float] = {}
        self._cache_ttl = 1200  # 20 minutes cache TTL
    
    def _get_cache_key(self, stock_name: str, date: datetime) -> str:
        """Generate cache key for stock and date"""
        date_str = date.strftime(self.config.DATA_TIME_FORMAT)
        return f"{stock_name}_{date_str}"
    
    def _get_current_price_cache_key(self, stock_name: str) -> str:
        """Generate cache key for current price"""
        return f"current_{stock_name}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if 'timestamp' not in cache_entry:
            return False
        return (datetime.now() - cache_entry['timestamp']).total_seconds() < self._cache_ttl
    
    def _try_exchange_data(self, stock_name: str, date: datetime, exchange_suffix: str):
        """
        Try to get data from a specific exchange
        
        Args:
            stock_name: Stock symbol
            date: Date to fetch data for
            exchange_suffix: Exchange suffix (.NS, .BO)
            
        Returns:
            dict: {'success': bool, 'exchange': str, 'data': pd.Series}
        """
        try:
            full_name = stock_name + exchange_suffix
            stock = yf.Ticker(full_name)
            hist = stock.history(start=date - timedelta(days=5), end=date - timedelta(days=4))
            
            if not hist.empty:
                row = hist.iloc[0]
                return {
                    'success': True,
                    'exchange': full_name,
                    'data': row
                }
        except Exception as e:
            logger.warning(f"Failed to get {exchange_suffix} data for {stock_name}: {e}")
        
        return {'success': False}
    
    def _get_data_with_fallback(self, stock_name: str, date: datetime):
        """
        Get data with exchange fallback (NSE → BSE)
        
        Args:
            stock_name: Stock symbol
            date: Date to fetch data for
            
        Returns:
            dict: Exchange result with success status and data
        """
        # Try exchanges in priority order
        for exchange in self.EXCHANGES:
            result = self._try_exchange_data(stock_name, date, exchange['suffix'])
            if result['success']:
                return result
        
        logger.warning(f"No data found for {stock_name} on {date} in any exchange")
        return {'success': False}
    
    def _format_ohlcv_data(self, row, date: datetime, exchange_name: str):
        """
        Format OHLCV data for detailed response
        
        Args:
            row: DataFrame row with OHLCV data
            date: Date of the data
            exchange_name: Full exchange name
            
        Returns:
            list: Formatted OHLCV data with metadata
        """
        return [
            date.strftime(self.config.DATA_TIME_FORMAT),
            exchange_name,
            float(row['Open']),
            float(row['High']),
            float(row['Low']),
            float(row['Close']),
            int(row['Volume'])
        ]
    
    def get_stock_price_details(self, date, stock_name):
        """
        Get stock price details using yfinance with fallback to BSE and caching
        
        Args:
            date: Date to fetch data for
            stock_name: Stock symbol
            
        Returns:
            list: Formatted price details or empty list if not found
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(stock_name, date)
            if cache_key in self._price_cache and self._is_cache_valid(self._price_cache[cache_key]):
                logger.debug(f"Cache hit for {stock_name} on {date}")
                return self._price_cache[cache_key]['data']
            
            # Fetch from API
            result = self._get_data_with_fallback(stock_name, date)
            
            if result['success']:
                formatted_data = self._format_ohlcv_data(
                    result['data'], date, result['exchange']
                )
                
                # Cache the result
                self._price_cache[cache_key] = {
                    'data': formatted_data,
                    'timestamp': datetime.now()
                }
                
                return formatted_data
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {stock_name}: {e}")
            return []
    
    def batch_get_stock_prices(self, stock_dates: List[Tuple[str, datetime]]) -> Dict[Tuple[str, datetime], List]:
        """
        Batch fetch stock prices for multiple stock-date combinations
        
        Args:
            stock_dates: List of (stock_name, date) tuples
            
        Returns:
            dict: Mapping of (stock_name, date) to price details
        """
        results = {}
        uncached_requests = []
        
        # Check cache first
        for stock_name, date in stock_dates:
            cache_key = self._get_cache_key(stock_name, date)
            if cache_key in self._price_cache and self._is_cache_valid(self._price_cache[cache_key]):
                results[(stock_name, date)] = self._price_cache[cache_key]['data']
                logger.debug(f"Cache hit for {stock_name} on {date}")
            else:
                uncached_requests.append((stock_name, date))
        
        # Group uncached requests by stock name to make true batch API calls
        stock_groups = {}
        for stock_name, date in uncached_requests:
            if stock_name not in stock_groups:
                stock_groups[stock_name] = []
            stock_groups[stock_name].append(date)
        
        # Make true batch API calls - one call per stock for all its dates
        for stock_name, dates in stock_groups.items():
            logger.info(f"Making batch API call for {stock_name} for {len(dates)} dates")
            
            try:
                # Get the date range for this stock
                min_date = min(dates)
                max_date = max(dates)
                
                # Add buffer days for better data retrieval
                start_date = min_date - timedelta(days=5)
                end_date = max_date + timedelta(days=1)
                
                # Try exchanges in priority order for batch fetch
                batch_data = None
                exchange_used = None
                
                for exchange in self.EXCHANGES:
                    try:
                        full_name = stock_name + exchange['suffix']
                        stock = yf.Ticker(full_name)
                        hist = stock.history(start=start_date, end=end_date)
                        
                        if not hist.empty:
                            batch_data = hist
                            exchange_used = full_name
                            logger.debug(f"Successfully fetched batch data for {full_name}")
                            break
                    except Exception as e:
                        logger.warning(f"Failed to get {exchange['suffix']} batch data for {stock_name}: {e}")
                        continue
                
                if batch_data is not None:
                    # Process each requested date from the batch data
                    for date in dates:
                        try:
                            # Find the closest date in the batch data
                            date_str = date.strftime('%Y-%m-%d')
                            if date_str in batch_data.index:
                                row = batch_data.loc[date_str]
                                formatted_data = self._format_ohlcv_data(row, date, exchange_used)
                                
                                # Cache the result
                                cache_key = self._get_cache_key(stock_name, date)
                                self._price_cache[cache_key] = {
                                    'data': formatted_data,
                                    'timestamp': datetime.now()
                                }
                                
                                results[(stock_name, date)] = formatted_data
                                logger.debug(f"Found data for {stock_name} on {date_str}")
                            else:
                                # Try to find the closest available date
                                available_dates = batch_data.index.strftime('%Y-%m-%d').tolist()
                                logger.warning(f"Date {date_str} not found for {stock_name}. Available dates: {available_dates[:5]}...")
                                results[(stock_name, date)] = []
                        except Exception as e:
                            logger.error(f"Error processing date {date} for {stock_name}: {e}")
                            results[(stock_name, date)] = []
                else:
                    logger.warning(f"No batch data found for {stock_name} in any exchange")
                    for date in dates:
                        results[(stock_name, date)] = []
                        
            except Exception as e:
                logger.error(f"Error in batch API call for {stock_name}: {e}")
                for date in dates:
                    results[(stock_name, date)] = []
        
        return results
    
    def get_current_stock_price(self, stock_name):
        """
        Get current stock price using the stock price details function with caching
        
        Args:
            stock_name: Stock symbol
            
        Returns:
            float: Current stock price or 0.0 if not found
        """
        try:
            # Check cache first
            cache_key = self._get_current_price_cache_key(stock_name)
            if cache_key in self._current_price_cache:
                logger.debug(f"Current price cache hit for {stock_name}")
                return self._current_price_cache[cache_key]
            
            # Use the stock price details function
            pricing_details = self.get_stock_price_details(datetime.now(), stock_name)
            
            # Return the closing price (index 5) from the pricing details
            current_price = 0.0
            if len(pricing_details) >= 6 and pricing_details[5] is not None:
                current_price = float(pricing_details[5])
            else:
                logger.warning(f"Could not get current price for {stock_name}")
            
            # Cache the result
            self._current_price_cache[cache_key] = current_price
            
            return current_price
                
        except Exception as e:
            logger.error(f"Error getting current price for {stock_name}: {e}")
            return 0.0
    
    def batch_get_current_prices(self, stock_names: List[str]) -> Dict[str, float]:
        """
        Batch fetch current prices for multiple stocks
        
        Args:
            stock_names: List of stock symbols
            
        Returns:
            dict: Mapping of stock_name to current price
        """
        results = {}
        uncached_stocks = []
        
        # Check cache first
        for stock_name in stock_names:
            cache_key = self._get_current_price_cache_key(stock_name)
            if cache_key in self._current_price_cache:
                results[stock_name] = self._current_price_cache[cache_key]
                logger.debug(f"Current price cache hit for {stock_name}")
            else:
                uncached_stocks.append(stock_name)
        
        # Fetch uncached prices
        for stock_name in uncached_stocks:
            logger.info(f"Fetching current price for {stock_name}")
            current_price = self.get_current_stock_price(stock_name)
            results[stock_name] = current_price
        
        return results
    
    def clear_cache(self):
        """Clear all cached data"""
        self._price_cache.clear()
        self._current_price_cache.clear()
        logger.info("Market data cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'price_cache_size': len(self._price_cache),
            'current_price_cache_size': len(self._current_price_cache),
            'cache_ttl_seconds': self._cache_ttl
        }
    
    def get_alpha_vantage_data(self, stock_name, function='GLOBAL_QUOTE'):
        """
        Get stock data from Alpha Vantage API
        
        Args:
            stock_name: Stock symbol
            function: API function to call
            
        Returns:
            list: Alpha Vantage data or empty list if not configured
        """
        try:
            # This would require an Alpha Vantage API key
            # For now, return empty data
            logger.warning("Alpha Vantage API not configured")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {stock_name}: {e}")
            return [] 
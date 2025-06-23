import yfinance as yf
import logging
from datetime import datetime, timedelta
from config import Config

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
            hist = stock.history(start=date, end=date + timedelta(days=1))
            
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
        Get stock price details using yfinance with fallback to BSE
        
        Args:
            date: Date to fetch data for
            stock_name: Stock symbol
            
        Returns:
            list: Formatted price details or empty list if not found
        """
        try:
            result = self._get_data_with_fallback(stock_name, date)
            
            if result['success']:
                return self._format_ohlcv_data(
                    result['data'], date, result['exchange']
                )
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {stock_name}: {e}")
            return []
    
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
    
    def get_current_stock_price(self, stock_name):
        """
        Get current stock price using the stock price details function
        
        Args:
            stock_name: Stock symbol
            
        Returns:
            float: Current stock price or 0.0 if not found
        """
        try:
            # Use the stock price details function
            pricing_details = self.get_stock_price_details(datetime.now(), stock_name)
            
            # Return the closing price (index 5) from the pricing details
            if len(pricing_details) >= 6 and pricing_details[5] is not None:
                return float(pricing_details[5])
            else:
                logger.warning(f"Could not get current price for {stock_name}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting current price for {stock_name}: {e}")
            return 0.0 
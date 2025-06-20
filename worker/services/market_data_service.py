import yfinance as yf
import logging
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

class MarketDataService:
    """Service for fetching market data and stock prices"""
    
    def __init__(self):
        self.config = Config()
    
    def get_prizing_details_yfinance(self, date, name):
        """Get pricing details using yfinance with fallback to BSE"""
        name = name.upper()
        nse_name = name + self.config.DOT_NS
        bse_name = name + self.config.DOT_BO
        output = [0, 0, 0, 0, 0]
        
        try:
            data = yf.download(nse_name, start=date, end=min(datetime.now(), date + timedelta(days=1)), period='10y')
            if not data.empty:
                output = [data['Open'].iloc[0], data['High'].iloc[0], data['Low'].iloc[0], data['Close'].iloc[0], data['Volume'].iloc[0]]
                return [float(x) for x in output]
        except Exception as e:
            logger.warning(f"Failed to get NSE data for {name}: {e}")
        
        try:
            data = yf.download(bse_name, start=date, end=min(datetime.now(), date + timedelta(days=1)), period='5d')
            if not data.empty:
                output = [data['Open'].iloc[0], data['High'].iloc[0], data['Low'].iloc[0], data['Close'].iloc[0], data['Volume'].iloc[0]]
                return [float(x) for x in output]
        except Exception as e:
            logger.error(f"Encountered exception using yfinance API for {name}: {e}")
        
        return output
    
    def get_stock_price_details(self, date, stock_name):
        """Get stock price details using yfinance"""
        try:
            # Add exchange suffix if not present
            if not stock_name.endswith(('.NS', '.BO')):
                stock_name += self.config.DOT_NS  # Default to NSE
            
            # Get stock data
            stock = yf.Ticker(stock_name)
            hist = stock.history(start=date, end=date + timedelta(days=1))
            
            if hist.empty:
                logger.warning(f"No data found for {stock_name} on {date}")
                return []
            
            # Extract price data
            row = hist.iloc[0]
            return [
                date.strftime(self.config.DATE_FORMAT),
                stock_name,
                float(row['Open']),
                float(row['High']),
                float(row['Low']),
                float(row['Close']),
                int(row['Volume'])
            ]
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {stock_name}: {e}")
            return []
    
    def get_alpha_vantage_data(self, stock_name, function='GLOBAL_QUOTE'):
        """Get stock data from Alpha Vantage API"""
        try:
            # This would require an Alpha Vantage API key
            # For now, return empty data
            logger.warning("Alpha Vantage API not configured")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {stock_name}: {e}")
            return []
    
    def get_current_stock_price(self, stock_name):
        """Get current stock price using the preferred pricing details function"""
        try:
            # Use the preferred pricing details function
            pricing_details = self.get_prizing_details_yfinance(datetime.now(), stock_name)
            
            # Return the closing price (index 3) from the pricing details
            if len(pricing_details) >= 4 and pricing_details[3] is not None:
                return float(pricing_details[3])
            else:
                logger.warning(f"Could not get current price for {stock_name}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting current price for {stock_name}: {e}")
            return 0.0 
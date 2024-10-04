import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
DATE_FORMAT = '%m/%d/%Y'
ydate = "%Y-%m-%d"
# Define the stock ticker and download start/end dates
stock_ticker = "GOOG"

start_date = datetime.now() - timedelta(days=2)
end_date = start_date+timedelta(days=3)
# Download historical data from Yahoo Finance
date = pd.to_datetime(start_date, format=DATE_FORMAT)
date = date.strftime(DATE_FORMAT)
stock_data = yf.download(stock_ticker, start=pd.to_datetime(start_date.strftime(DATE_FORMAT)), end=end_date, period='5d')

# Print the downloaded data
print(f"Data obtained for {stock_ticker}: {stock_data}")
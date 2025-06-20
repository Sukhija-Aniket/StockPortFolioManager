import os
from dotenv import load_dotenv

# Load environment variables
worker_directory = os.path.dirname(__file__)
env_file = os.path.join(worker_directory, 'secrets', '.env')
load_dotenv(env_file)

class Config:
    """Configuration class for scripts"""
    
    # File paths
    WORKER_DIRECTORY = worker_directory
    SECRETS_DIRECTORY = os.path.join(worker_directory, 'secrets')
    ASSETS_DIRECTORY = os.path.join(worker_directory, 'assets')
    
    # API Configuration
    API_KEY_FILE = os.path.join(SECRETS_DIRECTORY, 'tradingprojects-apiKey.json')
    
    # Environment variables
    EXCEL_FILE_NAME = os.getenv('EXCEL_FILE_NAME')
    SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
    SPREADSHEET_FILE = os.path.join(ASSETS_DIRECTORY, EXCEL_FILE_NAME) if EXCEL_FILE_NAME else None
    
    # RabbitMQ Configuration
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'guest')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'app.log'
    
    # Date formats
    DATE_FORMAT = '%m/%d/%Y'
    YFINANCE_DATE_FORMAT = '%Y-%m-%d'
    ORDER_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DATA_TIME_FORMAT = "%Y-%m-%d"
    
    # Transaction types
    BUY = 'BUY'
    SELL = 'SELL'
    
    # Exchanges
    BSE = 'BSE'
    NSE = 'NSE'
    
    # Other constants
    DEFAULT_DATE = '01/01/2020'
    GLOBAL_QUOTE = 'GLOBAL_QUOTE'
    COMPLETE = 'COMPLETE'
    DOT_NS = '.NS'
    DOT_BO = '.BO'
    CELL_RANGE = 'A2:P999' 
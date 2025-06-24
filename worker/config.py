import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
worker_directory = os.path.dirname(__file__)
env_file = os.path.join(worker_directory, 'secrets', '.env')
load_dotenv(env_file)

class Config:
    """Configuration class for worker service and general functionality"""
    
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
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/stock_portfolio')
    
    # Database Pool Configuration
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
    DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    DB_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))  # 1 hour
    
    # RabbitMQ Configuration
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'username')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'password')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
    
    # Worker Configuration
    WORKER_CONCURRENCY = int(os.getenv('WORKER_CONCURRENCY', '4'))
    WORKER_TIMEOUT = int(os.getenv('WORKER_TIMEOUT', '300'))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'worker.log')
    
    # Task Configuration
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '60'))  # seconds
    
    # Date formats
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
    
    @classmethod
    def get_rabbitmq_url(cls) -> str:
        """Get RabbitMQ connection URL"""
        return f"amqp://{cls.RABBITMQ_USERNAME}:{cls.RABBITMQ_PASSWORD}@{cls.RABBITMQ_HOST}:{cls.RABBITMQ_PORT}/"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        required_vars = [
            'DATABASE_URL',
            'RABBITMQ_HOST',
            'RABBITMQ_USERNAME',
            'RABBITMQ_PASSWORD'
        ]
        
        for var in required_vars:
            if not getattr(cls, var):
                raise ValueError(f"Required environment variable {var} is not set")
        
        return True 
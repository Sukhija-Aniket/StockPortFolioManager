import os
from dotenv import load_dotenv

# Load environment variables
app_directory = os.path.dirname(__file__)
env_file = os.path.join(app_directory, 'secrets', '.env')
load_dotenv(env_file)

class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv('APP_SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1000 * 1000  # 16MB max file size
    
    # Google OAuth Configuration
    GOOGLE_CREDENTIALS_FILE = os.path.join(app_directory, 'secrets', 'credentials.json')
    GOOGLE_SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    
    # Service URLs
    FRONTEND_SERVICE = os.getenv('FRONTEND_SERVICE', 'localhost:3000')
    BACKEND_SERVICE = os.getenv('BACKEND_SERVICE', 'localhost:5000')
    
    # RabbitMQ Configuration
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'guest')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
    
    # API Configuration
    API_KEY_FILE = os.path.join(app_directory, 'secrets', 'tradingprojects-apiKey.json')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'app.log'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    OAUTHLIB_INSECURE_TRANSPORT = "1"  # Allow HTTP for OAuth

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    OAUTHLIB_INSECURE_TRANSPORT = "0"  # Require HTTPS for OAuth

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 
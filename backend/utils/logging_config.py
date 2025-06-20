import logging
import os
from config import Config

def setup_logging(name=__name__, level=None):
    """Setup logging configuration"""
    if level is None:
        level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(Config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Config.LOG_FILE)
        ]
    )
    
    return logging.getLogger(name) 
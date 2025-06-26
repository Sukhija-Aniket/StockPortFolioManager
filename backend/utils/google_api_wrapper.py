"""
Google API Error Handler - Handles 401 errors and triggers re-authentication
"""
from functools import wraps
from googleapiclient.errors import HttpError
from utils.logging_config import setup_logging

logger = setup_logging(__name__)

class GoogleAuthError(Exception):
    """Custom exception for Google authentication errors"""
    pass

def handle_google_api_errors(func):
    """
    Decorator to handle Google API errors and trigger re-authentication
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function that handles Google API errors
        
    Raises:
        GoogleAuthError: When authentication is required (401 error)
        HttpError: For other HTTP errors
        Exception: For other exceptions
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpError as e:
            if e.resp.status == 401:
                # Token is invalid/expired - trigger re-authentication
                logger.warning(f"Google API 401 error in {func.__name__}: {e}")
                raise GoogleAuthError("Authentication required")
            elif e.resp.status == 403:
                # Permission denied
                logger.error(f"Google API 403 error in {func.__name__}: {e}")
                raise HttpError(e.resp, e.content, f"Permission denied: {e}")
            else:
                # Other HTTP errors
                logger.error(f"Google API error in {func.__name__}: {e}")
                raise e
        except Exception as e:
            # Handle other exceptions
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise e
    return wrapper 
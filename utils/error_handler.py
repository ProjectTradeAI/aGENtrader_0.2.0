"""
aGENtrader v2 Error Handler

This module provides utility functions and classes for handling errors gracefully.
"""

import os
import time
import logging
import functools
from typing import Dict, Any, Optional, Callable, List, Type, Union, Tuple
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('error_handler')

class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass

class DataFetchingError(Exception):
    """Exception raised for errors during data fetching."""
    pass

class APIKeyError(Exception):
    """Exception raised for missing or invalid API keys."""
    pass

class LLMError(Exception):
    """Exception raised for errors related to language model usage."""
    pass

def retry_with_backoff(max_retries: int = 3, 
                      initial_backoff: float = 1.0, 
                      backoff_factor: float = 2.0,
                      exceptions_to_retry: Optional[List[Type[Exception]]] = None) -> Callable:
    """
    Decorator to retry functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        initial_backoff: Initial backoff time in seconds
        backoff_factor: Factor to increase backoff time with each retry
        exceptions_to_retry: List of exception types to retry on
        
    Returns:
        Decorated function
    """
    if exceptions_to_retry is None:
        exceptions_to_retry = [Exception]
        
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            backoff = initial_backoff
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions_to_retry) as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Max retries reached for {func.__name__}: {str(e)}")
                        raise
                        
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} after error: {str(e)}")
                    logger.warning(f"Backing off for {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= backoff_factor
        
        return wrapper
    
    return decorator

def handle_api_errors(func: Callable) -> Callable:
    """
    Decorator to handle API-related errors gracefully.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {func.__name__}: {str(e)}")
            # Return a safe default value based on the function's expected return type
            return kwargs.get('default_return', {})
    
    return wrapper

def check_api_keys(required_keys: List[str]) -> bool:
    """
    Check if required API keys are present in environment variables.
    
    Args:
        required_keys: List of required API key environment variable names
        
    Returns:
        True if all keys are present, False otherwise
    """
    missing_keys = []
    
    for key in required_keys:
        if not os.environ.get(key):
            missing_keys.append(key)
    
    if missing_keys:
        logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
        return False
    
    return True

def request_api_key(key_name: str, service_name: str) -> None:
    """
    Log a message to request an API key.
    
    Args:
        key_name: Name of the API key
        service_name: Name of the service the key is for
    """
    logger.warning(f"Missing API key for {service_name}. Please set the {key_name} environment variable.")
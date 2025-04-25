"""
Error Handling Utility Module

This module provides centralized error handling capabilities for the aGENtrader v2 system.
It includes utilities for retrying operations, logging errors consistently, and managing
exception handling throughout the application.
"""

import os
import time
import json
import logging
import traceback
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union, cast
import yaml

from aGENtrader_v2.utils.config import get_config
from aGENtrader_v2.utils.logger import get_logger

# Get module logger
logger = get_logger("error_handler")

# Load error handling configuration
config = get_config()
error_config = config.get_section("error_handling")

# Default values if config is missing
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 2
DEFAULT_ALLOW_MOCK_FALLBACK = False
DEFAULT_LOG_FAILED_TRADES = True
DEFAULT_FAILED_TRADES_LOG = "logs/failed_trades.jsonl"
DEFAULT_ERROR_LOGS_DIR = "logs/errors"

# Extract configuration values with defaults
MAX_RETRIES = error_config.get("max_api_retries", DEFAULT_MAX_RETRIES)
BACKOFF_SECONDS = error_config.get("retry_backoff_seconds", DEFAULT_BACKOFF_SECONDS)
ALLOW_MOCK_FALLBACK = error_config.get("allow_mock_fallback", DEFAULT_ALLOW_MOCK_FALLBACK)
LOG_FAILED_TRADES = error_config.get("log_failed_trades", DEFAULT_LOG_FAILED_TRADES)
FAILED_TRADES_LOG = error_config.get("failed_trades_log", DEFAULT_FAILED_TRADES_LOG)
ERROR_LOGS_DIR = error_config.get("error_logs_dir", DEFAULT_ERROR_LOGS_DIR)

# Get parent directory (project root)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ensure log directories exist
os.makedirs(os.path.dirname(os.path.join(project_root, FAILED_TRADES_LOG)), exist_ok=True)
os.makedirs(os.path.join(project_root, ERROR_LOGS_DIR), exist_ok=True)

class TradeExecutionError(Exception):
    """Exception raised for errors during trade execution."""
    pass

class DataFetchingError(Exception):
    """Exception raised for errors during data fetching."""
    pass

class ValidationError(Exception):
    """Exception raised for data validation errors."""
    pass

class RetryExhaustedError(Exception):
    """Exception raised when retry attempts are exhausted."""
    pass

class MockDataFallbackError(Exception):
    """Exception raised when system attempts to fall back to mock data when not allowed."""
    pass

def retry_with_backoff(max_retries: Optional[int] = None, 
                     backoff_seconds: Optional[int] = None,
                     allowed_exceptions: Optional[List[Type[Exception]]] = None) -> Callable:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum retry attempts (default from config)
        backoff_seconds: Initial backoff seconds (default from config)
        allowed_exceptions: List of exception types to catch and retry
        
    Returns:
        Function decorator
    """
    max_retries = cast(int, max_retries if max_retries is not None else MAX_RETRIES)
    backoff_seconds = cast(int, backoff_seconds if backoff_seconds is not None else BACKOFF_SECONDS)
    allowed_exceptions = cast(List[Type[Exception]], allowed_exceptions if allowed_exceptions is not None else [Exception])
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Initialize variables
            retries = 0
            last_exception = None
            
            # Try until max retries reached
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except tuple(allowed_exceptions) as e:
                    last_exception = e
                    retries += 1
                    
                    if retries <= max_retries:
                        # Calculate wait time with exponential backoff: base * 2^retry
                        wait_time = backoff_seconds * (2 ** (retries - 1))
                        
                        # Log retry attempt
                        logger.warning(
                            f"Retry {retries}/{max_retries} for {func.__name__} after error: {str(e)}. "
                            f"Waiting {wait_time} seconds."
                        )
                        
                        # Wait before retrying
                        time.sleep(wait_time)
                    else:
                        # Log exhausted retries
                        logger.error(
                            f"Retry attempts exhausted ({max_retries}) for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        
                        # Raise custom exception
                        raise RetryExhaustedError(
                            f"Maximum retry attempts ({max_retries}) reached for {func.__name__}. "
                            f"Last error: {str(e)}"
                        ) from e
                        
            # This shouldn't be reached but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    
    return decorator

def handle_api_errors(func: Callable) -> Callable:
    """
    Decorator to handle API and external service errors.
    
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
            # Log API error
            logger.error(f"API error in {func.__name__}: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Re-raise as DataFetchingError
            raise DataFetchingError(f"Error fetching data from external API: {str(e)}") from e
            
    return wrapper

def validate_trade_data(trade_data: Dict[str, Any]) -> None:
    """
    Validate trade data for required fields and proper formats.
    
    Args:
        trade_data: Trade data dictionary to validate
        
    Raises:
        ValidationError: If trade data is invalid
    """
    # Required fields in a valid trade
    required_fields = ["pair", "action"]
    
    # Check for required fields
    for field in required_fields:
        if field not in trade_data:
            raise ValidationError(f"Missing required field '{field}' in trade data")
    
    # Validate action field
    valid_actions = ["BUY", "SELL", "HOLD"]
    if trade_data.get("action") not in valid_actions:
        raise ValidationError(
            f"Invalid action '{trade_data.get('action')}' in trade data. "
            f"Must be one of {valid_actions}"
        )
        
    # Validate confidence if present
    if "confidence" in trade_data:
        try:
            confidence = float(trade_data["confidence"])
            if not (0 <= confidence <= 100):
                raise ValidationError(
                    f"Confidence must be between 0 and 100, got {confidence}"
                )
        except (ValueError, TypeError):
            raise ValidationError(
                f"Confidence must be a number, got {trade_data['confidence']}"
            )

def log_failed_trade(trade_data: Dict[str, Any], error: str, error_type: str) -> None:
    """
    Log a failed trade to a persistent file for later analysis.
    
    Args:
        trade_data: Trade data dictionary
        error: Error message
        error_type: Type of error (e.g. 'validation', 'execution')
    """
    if not LOG_FAILED_TRADES:
        return
        
    # Create log entry
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "trade_data": trade_data,
        "error": error,
        "error_type": error_type,
        "stack_trace": traceback.format_exc()
    }
    
    # Append to log file
    try:
        log_file = os.path.join(project_root, FAILED_TRADES_LOG)
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        logger.info(f"Failed trade logged to {log_file}")
    except Exception as e:
        logger.error(f"Error logging failed trade: {e}")

def handle_trade_execution_error(func: Callable) -> Callable:
    """
    Decorator to handle trade execution errors.
    
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
            # Extract trade data from arguments (if present)
            trade_data = None
            for arg in args:
                if isinstance(arg, dict) and "action" in arg and "pair" in arg:
                    trade_data = arg
                    break
                    
            if not trade_data and "trade_data" in kwargs:
                trade_data = kwargs["trade_data"]
                
            if not trade_data and "decision" in kwargs:
                trade_data = kwargs["decision"]
                
            # Log error
            error_msg = f"Trade execution error in {func.__name__}: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Log failed trade
            if trade_data and LOG_FAILED_TRADES:
                log_failed_trade(trade_data, str(e), "execution")
                
            # Return error result instead of raising exception
            return {
                "status": "error",
                "message": error_msg,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
    return wrapper

def check_mock_fallback(allow_fallback: Optional[bool] = None) -> None:
    """
    Check if mock data fallback is allowed.
    
    Args:
        allow_fallback: Override for system configuration
        
    Raises:
        MockDataFallbackError: If fallback is not allowed
    """
    # Use parameter if provided, otherwise use config
    allow_fallback = cast(bool, allow_fallback if allow_fallback is not None else ALLOW_MOCK_FALLBACK)
    
    if not allow_fallback:
        error_msg = "Fallback to mock data is not allowed in current configuration"
        logger.error(error_msg)
        raise MockDataFallbackError(error_msg)
        
    logger.warning("Falling back to mock data as configured")

def check_api_keys(key_name: str, env_var_name: Optional[str] = None) -> bool:
    """
    Check if an API key is available through environment variables or config.
    
    Args:
        key_name: Name of the key to check (e.g., 'coinapi_key')
        env_var_name: Optional custom environment variable name
                     (defaults to uppercase of key_name)
        
    Returns:
        True if the key is available, False otherwise
    """
    env_var_name = env_var_name or key_name.upper()
    
    # Check environment variable first
    if os.environ.get(env_var_name):
        logger.debug(f"Found {key_name} in environment variable {env_var_name}")
        return True
    
    # Check configuration
    config_key = key_name.lower()
    if config.get(config_key):
        logger.debug(f"Found {key_name} in configuration")
        return True
    
    # Check secrets file
    try:
        with open(os.path.join(project_root, "config/secrets.yaml"), "r") as f:
            secrets = yaml.safe_load(f)
            if secrets and isinstance(secrets, dict) and secrets.get(key_name):
                logger.debug(f"Found {key_name} in secrets file")
                return True
    except Exception:
        # Secrets file is optional
        pass
    
    logger.warning(f"API key '{key_name}' not found in environment, config, or secrets")
    return False

def request_api_key(key_name: str, env_var_name: Optional[str] = None) -> None:
    """
    Log instructions for obtaining the required API key.
    
    Args:
        key_name: Name of the API key (e.g., 'coinapi_key')
        env_var_name: Optional custom environment variable name
    """
    env_var_name = env_var_name or key_name.upper()
    
    logger.critical(f"MISSING API KEY: {key_name}")
    logger.critical(f"Please set the {env_var_name} environment variable")
    logger.critical(f"You can also add it to config/secrets.yaml as {key_name}: YOUR_KEY")
    
    # Provide service-specific instructions
    if key_name == "coinapi_key":
        logger.critical("To get a CoinAPI key:")
        logger.critical("1. Visit https://www.coinapi.io/")
        logger.critical("2. Sign up for a free or paid plan")
        logger.critical("3. Copy your API key from your account dashboard")
    
    # General instruction for setting environment variable
    logger.critical(f"\nTo set the environment variable:")
    logger.critical(f"export {env_var_name}=your_api_key_here\n")
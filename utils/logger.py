"""
Logger Utility Module

This module provides a centralized logging configuration for the entire application.
It ensures consistent logging behavior across all modules and prevents duplicate
configuration through a singleton pattern.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional

# Configure base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "agent_output.log")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Singleton to track if the root logger has been configured
_logger_configured = False

# Store loggers to avoid creating duplicates
_loggers: Dict[str, logging.Logger] = {}

# Format strings
CONSOLE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str, 
               level: int = logging.INFO,
               console_level: Optional[int] = None,
               file_level: Optional[int] = None,
               max_bytes: int = 10 * 1024 * 1024,  # 10 MB
               backup_count: int = 5) -> logging.Logger:
    """
    Get a configured logger with the given name.
    
    This function ensures that:
    1. Each named logger is only created once
    2. The root logging configuration is only applied once
    3. Both console and file handlers are configured
    
    Args:
        name: Name of the logger, typically the module name
        level: Overall logging level
        console_level: Console handler logging level (defaults to level)
        file_level: File handler logging level (defaults to level)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured Logger instance
    """
    global _logger_configured, _loggers
    
    # Return existing logger if already created
    if name in _loggers:
        return _loggers[name]
    
    # Set default levels if not provided
    console_level = console_level or level
    file_level = file_level or level
    
    # Configure root logger only once
    if not _logger_configured:
        # Don't use basicConfig to avoid conflicts with other libraries
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.WARNING)  # Set conservative level for root
        _logger_configured = True
    
    # Create and configure the logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatters
    console_formatter = logging.Formatter(CONSOLE_FORMAT, DATE_FORMAT)
    file_formatter = logging.Formatter(FILE_FORMAT, DATE_FORMAT)
    
    # Add console handler if not already present
    has_console_handler = any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) 
                             for h in logger.handlers)
    if not has_console_handler:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if not already present
    has_file_handler = any(isinstance(h, RotatingFileHandler) for h in logger.handlers)
    if not has_file_handler:
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setLevel(file_level)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except (IOError, PermissionError) as e:
            # If can't write to file, log a warning but continue
            logging.warning(f"Could not create log file at {LOG_FILE}: {e}")
    
    # Store the logger
    _loggers[name] = logger
    
    return logger

# Example usage
if __name__ == "__main__":
    # Get loggers with different names
    logger1 = get_logger("test_logger")
    logger2 = get_logger("another_logger")
    
    # Log messages
    logger1.debug("This is a debug message")
    logger1.info("This is an info message")
    logger1.warning("This is a warning message")
    logger1.error("This is an error message")
    
    # Getting the same logger returns the same instance
    logger1_again = get_logger("test_logger")
    logger1_again.info("Using the same logger instance")
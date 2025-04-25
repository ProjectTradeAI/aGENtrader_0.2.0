"""
aGENtrader v2 Error Handler

This module provides standardized error handling utilities for the aGENtrader system.
"""

import os
import logging
import traceback
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Configure logger
logger = logging.getLogger('aGENtrader.utils.error_handler')

class ErrorHandler:
    """Error handler with standardized responses and logging."""
    
    # Define error types with codes
    ERROR_TYPES = {
        'API_CONNECTION_ERROR': 1001,
        'API_AUTHENTICATION_ERROR': 1002,
        'API_RATE_LIMIT_ERROR': 1003,
        'API_RESPONSE_ERROR': 1004,
        'DATA_VALIDATION_ERROR': 2001,
        'DATA_PARSING_ERROR': 2002,
        'ANALYSIS_ERROR': 3001,
        'TECHNICAL_ANALYSIS_ERROR': 3002,
        'SENTIMENT_ANALYSIS_ERROR': 3003,
        'AGENT_ERROR': 4001,
        'SYSTEM_ERROR': 5001,
        'CONFIGURATION_ERROR': 5002,
    }
    
    def __init__(self, log_dir: str = 'logs'):
        """
        Initialize the error handler.
        
        Args:
            log_dir: Directory to store error logs
        """
        self.log_dir = log_dir
        self.invalid_api_log_dir = os.path.join(log_dir, 'invalid_api_responses')
        
        # Ensure log directories exist
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.invalid_api_log_dir, exist_ok=True)
    
    def log_error(self, error_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Log an error with standardized format.
        
        Args:
            error_type: Type of error (from ERROR_TYPES)
            message: Error message
            details: Additional error details
            
        Returns:
            Standardized error response dictionary
        """
        if error_type not in self.ERROR_TYPES:
            logger.warning(f"Unknown error type: {error_type}, defaulting to SYSTEM_ERROR")
            error_type = 'SYSTEM_ERROR'
        
        error_code = self.ERROR_TYPES[error_type]
        
        # Create error response
        error_response = {
            'success': False,
            'error': {
                'code': error_code,
                'type': error_type,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        if details:
            error_response['error']['details'] = details
        
        # Log the error
        logger.error(f"{error_type}: {message}")
        if details:
            logger.debug(f"Error details: {json.dumps(details)}")
        
        return error_response
    
    def handle_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle an exception with full traceback logging.
        
        Args:
            exception: The exception to handle
            context: Additional context for the error
            
        Returns:
            Standardized error response dictionary
        """
        error_type = 'SYSTEM_ERROR'
        message = str(exception)
        
        # Get exception traceback
        tb = traceback.format_exc()
        
        # Create details with exception info
        details = {
            'exception_type': exception.__class__.__name__,
            'traceback': tb
        }
        
        # Add context if provided
        if context is not None:
            details_with_context = details.copy()
            details_with_context['context'] = context
            details = details_with_context
        
        # Log the error
        logger.error(f"Exception: {exception.__class__.__name__}: {message}")
        logger.debug(f"Traceback: {tb}")
        
        return self.log_error(error_type, message, details)
    
    def log_invalid_api_response(self, endpoint: str, response: Any, expected_schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Log an invalid API response for later analysis.
        
        Args:
            endpoint: API endpoint that returned the response
            response: The invalid response
            expected_schema: The expected response schema
            
        Returns:
            Error response dictionary
        """
        # Create a filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{endpoint.replace('/', '_')}.json"
        filepath = os.path.join(self.invalid_api_log_dir, filename)
        
        # Prepare log data
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'response': response
        }
        
        if expected_schema:
            log_data['expected_schema'] = expected_schema
        
        # Write to log file
        try:
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            logger.info(f"Invalid API response logged to {filepath}")
        except Exception as e:
            logger.error(f"Failed to log invalid API response: {str(e)}")
        
        # Return error response
        message = f"Invalid API response from {endpoint}"
        return self.log_error('API_RESPONSE_ERROR', message, {'endpoint': endpoint})


# Create a singleton instance
error_handler = ErrorHandler()
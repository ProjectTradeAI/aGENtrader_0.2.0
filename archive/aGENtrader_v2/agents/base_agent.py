"""
aGENtrader v2 Base Agent Class

This module provides the base agent class with common functionality
for all specialist agents in the aGENtrader v2 system.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger('aGENtrader.agents.base')

class BaseAnalystAgent:
    """Base class for all analyst agents in the aGENtrader v2 system."""

    def __init__(self, data_fetcher=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            data_fetcher: Data fetcher instance for retrieving market data
            config: Configuration parameters
        """
        self.data_fetcher = data_fetcher
        self.config = config or {}
        self.logger = logging.getLogger(f'aGENtrader.agents.{self.__class__.__name__}')
        
        # Set default configuration values if not provided
        if not self.config.get('default_symbol'):
            self.config['default_symbol'] = 'BITSTAMP_SPOT_BTC_USD'
        
        if not self.config.get('default_interval'):
            self.config['default_interval'] = '1h'
            
        self.logger.debug(f"Initialized {self.__class__.__name__} with config: {self.config}")

    def analyze(
        self, 
        symbol: Optional[str] = None, 
        interval: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform analysis on market data. Must be implemented by subclasses.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Analysis results
        """
        raise NotImplementedError("Subclasses must implement the analyze method")

    def validate_input(self, symbol: Optional[str], interval: Optional[str]) -> bool:
        """
        Validate input parameters.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            True if inputs are valid, False otherwise
        """
        # Use default values if not provided
        if not symbol:
            self.logger.debug("No symbol provided, using default")
            return True
            
        if not interval:
            self.logger.debug("No interval provided, using default")
            return True
            
        return True

    def handle_data_fetching_error(self, error) -> Dict[str, Any]:
        """
        Handle errors that occur during data fetching.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Error response dictionary
        """
        self.logger.error(f"Data fetching error: {str(error)}")
        
        error_type = type(error).__name__
        error_message = str(error)
        
        return self.build_error_response(error_type, error_message)

    def build_error_response(self, error_type: str, message: str) -> Dict[str, Any]:
        """
        Build a standardized error response.
        
        Args:
            error_type: Type of error
            message: Error message
            
        Returns:
            Error response dictionary
        """
        return {
            'error': {
                'type': error_type,
                'message': message,
                'timestamp': datetime.now().isoformat()
            },
            'success': False
        }
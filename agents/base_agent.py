"""
aGENtrader v2 Base Agent Class - Simplified Test Version

This module provides a simplified base agent class for testing.
"""

import logging
from typing import Dict, Any, Optional

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
        self.logger = logging.getLogger('aGENtrader.agents.base')
    
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
        raise NotImplementedError("Subclasses must implement analyze method")
    
    def validate_input(self, symbol: Optional[str], interval: Optional[str]) -> bool:
        """
        Validate input parameters.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            True if inputs are valid, False otherwise
        """
        if symbol is None and 'default_symbol' not in self.config:
            self.logger.error("No symbol provided and no default symbol in config")
            return False
        
        if interval is None and 'default_interval' not in self.config:
            self.logger.error("No interval provided and no default interval in config")
            return False
        
        return True
    
    def build_error_response(self, error_type: str, message: str) -> Dict[str, Any]:
        """
        Build a standardized error response.
        
        Args:
            error_type: Type of error
            message: Error message
            
        Returns:
            Error response dictionary
        """
        self.logger.error(f"{error_type}: {message}")
        return {
            "success": False,
            "error_type": error_type,
            "message": message
        }
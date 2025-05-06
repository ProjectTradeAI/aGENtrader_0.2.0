"""
aGENtrader v2 Base Analyst Agent

This module defines the base analyst agent class that all specific analyst agents
should inherit from. It provides common functionality for market analysis.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import yaml
from .base_agent import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)

class BaseAnalystAgent(BaseAgent):
    """BaseAnalystAgent for aGENtrader v0.2.2
    
    This class provides common functionality for all analyst agents and
    defines the standard interface they should implement.
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize the base analyst agent.
        
        Args:
            agent_name: Name of the agent
        """
        self.version = "v0.2.2"
        super().__init__(agent_name=agent_name)
        self.name = agent_name  # For backward compatibility
        self.description = "Base analyst agent implementation"
    
    def analyze(self, symbol: Optional[str] = None, market_data: Optional[Dict[str, Any]] = None, 
                interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze market data and generate insights.
        
        This method should be implemented by subclasses.
        
        Args:
            symbol: Trading symbol
            market_data: Pre-fetched market data (optional)
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Analysis results
        """
        return self.build_error_response(
            "NOT_IMPLEMENTED",
            f"Agent {self.name} does not implement analyze()"
        )
        
    def get_analysis(self, symbol: Optional[str] = None, interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Get analysis for a trading pair. This is a wrapper for analyze().
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Analysis results
        """
        return self.analyze(symbol=symbol, interval=interval, **kwargs)
    
    def _get_trading_config(self) -> Dict[str, Any]:
        """
        Get trading configuration from settings file.
        
        Returns:
            Trading configuration dictionary
        """
        try:
            # Try to load from config/settings.yaml first
            config_path = "config/settings.yaml"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('trading', {})
            
            # Fallback to config/default.json
            config_path = "config/default.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('trading', {})
        except Exception as e:
            logger.error(f"Error loading trading config: {str(e)}")
            
        # Return empty dict if config couldn't be loaded
        return {}
        
    def validate_input(self, symbol: Optional[str] = None, interval: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate input parameters.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        
        if not symbol:
            errors.append("Symbol is required")
            
        if not interval:
            errors.append("Interval is required")
            
        if errors:
            return {
                "valid": False,
                "errors": errors
            }
            
        return {
            "valid": True
        }
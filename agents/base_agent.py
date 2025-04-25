"""
Base Agent Module for aGENtrader v2

This module provides the base agent classes that other agents inherit from.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# Set up logger
logger = logging.getLogger("aGENtrader.agents.base")

class BaseAnalystAgent:
    """
    Base class for all analyst agents.
    
    This class provides common functionality for all analyst agents including:
    - Configuration loading
    - Error handling
    - Standard analysis result structure
    """
    
    def __init__(self):
        """Initialize the base analyst agent."""
        # Set up logger
        self.logger = logging.getLogger(f"aGENtrader.agents.{self.__class__.__name__}")
        
        # Load default configs
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
        
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Load agent configuration from config file.
        
        Returns:
            Dictionary with agent configuration
        """
        try:
            config_path = os.path.join(self.config_dir, "agents.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                return config.get(self.__class__.__name__, {})
            return {}
        except Exception as e:
            self.logger.warning(f"Error loading agent config: {str(e)}")
            return {}
            
    def get_trading_config(self) -> Dict[str, Any]:
        """
        Load trading configuration from config file.
        
        Returns:
            Dictionary with trading configuration
        """
        try:
            config_path = os.path.join(self.config_dir, "trading.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.warning(f"Error loading trading config: {str(e)}")
            return {}
    
    def create_standard_result(self, 
                              signal: str, 
                              confidence: int, 
                              reason: str,
                              data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a standardized result dictionary.
        
        Args:
            signal: Trading signal (BUY, SELL, HOLD)
            confidence: Confidence level (0-100)
            reason: Reason for the signal
            data: Additional data to include
            
        Returns:
            Standardized result dictionary
        """
        result = {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "timestamp": None,  # Will be filled by the agent
            "data": data or {}
        }
        return result
        
    def handle_analysis_error(self, error: Exception, agent_type: str) -> Dict[str, Any]:
        """
        Create standardized error result.
        
        Args:
            error: Exception that occurred
            agent_type: Type of analysis that failed
            
        Returns:
            Error result dictionary
        """
        error_name = f"{agent_type.upper()}_ERROR"
        error_msg = f"Error performing {agent_type}: {str(error)}"
        
        self.logger.error(f"{error_name}: {error_msg}")
        
        return {
            "error": error_name,
            "error_message": error_msg,
            "signal": "HOLD",  # Default to HOLD on error
            "confidence": 0,
            "reason": f"Analysis failed: {str(error)}"
        }
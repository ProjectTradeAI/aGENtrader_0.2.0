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
        
    def validate_input(self, symbol: Optional[str], interval: Optional[str]) -> bool:
        """
        Validate input parameters for analysis.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            True if input is valid, False otherwise
        """
        if not symbol:
            self.logger.error("Symbol is required for analysis")
            return False
        
        if not interval:
            self.logger.error("Interval is required for analysis")
            return False
            
        return True
        
    def build_error_response(self, error_code: str, error_message: str) -> Dict[str, Any]:
        """
        Build standardized error response.
        
        Args:
            error_code: Error code
            error_message: Error message
            
        Returns:
            Error response dictionary
        """
        self.logger.error(f"{error_code}: {error_message}")
        
        return {
            "error": error_code,
            "error_message": error_message,
            "signal": "HOLD",  # Default to HOLD on error
            "confidence": 0,
            "reason": f"Analysis failed: {error_message}",
            "status": "error"
        }
        
    def validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate analysis result and ensure it has required fields.
        
        Args:
            result: Analysis result dictionary
            
        Returns:
            Validated result dictionary
        """
        required_fields = ["signal", "confidence", "reason"]
        
        # Check for error
        if "error" in result:
            return result
            
        # Check for required fields
        for field in required_fields:
            if field not in result:
                return self.build_error_response(
                    "INVALID_RESULT", 
                    f"Analysis result missing required field: {field}"
                )
                
        # Ensure signal is valid
        valid_signals = ["BUY", "SELL", "HOLD", "NEUTRAL"]
        if result["signal"] not in valid_signals:
            result["signal"] = "HOLD"
            
        # Ensure confidence is within range
        if not isinstance(result["confidence"], (int, float)) or result["confidence"] < 0 or result["confidence"] > 100:
            result["confidence"] = 50
            
        return result
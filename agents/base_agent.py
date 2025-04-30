"""
Base Agent Module for aGENtrader v2

This module provides the base agent classes that other agents inherit from.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from agents.agent_interface import AgentInterface, AnalystAgentInterface
from core.version import VERSION

# Set up logger
logger = logging.getLogger("aGENtrader.agents.base")

class BaseAgent(AgentInterface):
    """
    Base class for all aGENtrader agents.
    
    This class provides common functionality for all agents including:
    - Standardized identification
    - Configuration loading
    - Error handling
    - Logging
    """
    
    def __init__(self, agent_name=None):
        """Initialize the base agent.
        
        Args:
            agent_name: Optional name for the agent (used for agent-specific configurations)
        """
        # Set up logger
        self.logger = logging.getLogger(f"aGENtrader.agents.{self.__class__.__name__}")
        
        # Save agent name for agent-specific configurations
        self._agent_name = agent_name or self.__class__.__name__.lower()
        
        # Default properties
        self._description = "Base aGENtrader agent"
        
        # Load default configs
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
    
    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._agent_name
    
    @property
    def description(self) -> str:
        """Get the description of the agent."""
        return self._description
    
    @property
    def version(self) -> str:
        """Get the version of the agent."""
        return VERSION


class BaseAnalystAgent(BaseAgent, AnalystAgentInterface):
    """
    Base class for all analyst agents.
    
    This class provides common functionality for all analyst agents including:
    - Configuration loading
    - Error handling
    - Standard analysis result structure
    """
    
    def __init__(self, agent_name=None):
        """Initialize the base analyst agent.
        
        Args:
            agent_name: Optional name for the agent (used for agent-specific configurations)
        """
        super().__init__(agent_name=agent_name)
        self._description = "Base analyst agent for market analysis"
        
        # Common properties all analyst agents should have
        self.symbol = None
        self.interval = None
        self.data_provider = None
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and produce results.
        
        This method should be overridden by subclasses to provide specific analysis.
        The base implementation returns a default HOLD signal.
        
        Args:
            market_data: Dictionary containing market data for analysis
            
        Returns:
            Dictionary with analysis results
        """
        self.logger.warning("BaseAnalystAgent.analyze() called - this should be overridden by subclasses")
        
        # Extract symbol and interval from market data if available
        if market_data:
            self.symbol = market_data.get('symbol', self.symbol)
            self.interval = market_data.get('interval', self.interval)
        
        # Return a default HOLD signal with zero confidence
        return self.create_standard_result(
            signal="HOLD",
            confidence=0,
            reason="Base implementation - should be overridden",
            data={"warning": "Using default implementation"}
        )
        
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Load agent configuration from config file.
        
        Returns:
            Dictionary with agent configuration
        """
        try:
            # First try to load from settings.yaml which is our new config format
            yaml_config_path = os.path.join(self.config_dir, "settings.yaml")
            if os.path.exists(yaml_config_path):
                try:
                    import yaml
                    with open(yaml_config_path, "r") as f:
                        config = yaml.safe_load(f)
                    # Get the 'agents' section from settings.yaml
                    return config.get("agents", {})
                except ImportError:
                    self.logger.warning("PyYAML not installed, falling back to JSON config")
                    
            # Fall back to agents.json if settings.yaml isn't available
            json_config_path = os.path.join(self.config_dir, "agents.json")
            if os.path.exists(json_config_path):
                with open(json_config_path, "r") as f:
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
            # First try to load from settings.yaml which is our new config format
            yaml_config_path = os.path.join(self.config_dir, "settings.yaml")
            if os.path.exists(yaml_config_path):
                try:
                    import yaml
                    with open(yaml_config_path, "r") as f:
                        config = yaml.safe_load(f)
                    # Get the 'trading' section from settings.yaml
                    return config.get("trading", {})
                except ImportError:
                    self.logger.warning("PyYAML not installed, falling back to JSON config")
            
            # Fall back to trading.json if settings.yaml isn't available
            json_config_path = os.path.join(self.config_dir, "trading.json")
            if os.path.exists(json_config_path):
                with open(json_config_path, "r") as f:
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
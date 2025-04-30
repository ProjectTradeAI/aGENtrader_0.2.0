"""
aGENtrader v2 Base Agent

This module provides base classes for the agent architecture in aGENtrader v2.
These classes define the standard interfaces and common functionality for all agents.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

# Configure logging
logger = logging.getLogger(__name__)

class AgentInterface(ABC):
    """
    Base interface for all agents in the system.
    
    This abstract base class defines the methods that all agents must implement.
    """
    
    @abstractmethod
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get the agent's configuration.
        
        Returns:
            Dictionary containing agent configuration
        """
        pass
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Run the agent's main functionality.
        
        Returns:
            Result dictionary
        """
        pass

class BaseAgent(AgentInterface):
    """
    Base class for all agents in the system.
    
    This class provides common functionality like configuration loading,
    error handling, and performance tracking.
    """
    
    def __init__(self, agent_name: str = "base_agent"):
        """
        Initialize a base agent.
        
        Args:
            agent_name: Name of the agent
        """
        self.name = agent_name
        self.description = "Base agent implementation"
        self.last_run_time = None
        self.last_run_duration = None
        
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get the agent's configuration from the default config file.
        
        Returns:
            Dictionary containing agent configuration
        """
        config_file = os.environ.get("AGENT_CONFIG_PATH", "config/agent_config.json")
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file {config_file} not found, using default configuration")
                return {}
        except Exception as e:
            logger.error(f"Error loading agent config: {str(e)}")
            return {}
            
    def get_trading_config(self) -> Dict[str, Any]:
        """
        Get the trading configuration from the default config file.
        
        Returns:
            Dictionary containing trading configuration
        """
        config_file = os.environ.get("TRADING_CONFIG_PATH", "config/trading_config.json")
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Trading config file {config_file} not found, using default configuration")
                return {
                    "default_symbol": "BTC/USDT",
                    "default_interval": "1h",
                    "default_market": "binance",
                    "confidence_threshold": 70
                }
        except Exception as e:
            logger.error(f"Error loading trading config: {str(e)}")
            return {
                "default_symbol": "BTC/USDT",
                "default_interval": "1h",
                "default_market": "binance",
                "confidence_threshold": 70
            }
            
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Run the agent's main functionality with timing and error handling.
        
        Returns:
            Result dictionary
        """
        start_time = time.time()
        self.last_run_time = datetime.now().isoformat()
        
        try:
            result = self._run(*args, **kwargs)
            
            # Add metadata to result
            if isinstance(result, dict):
                result.update({
                    "agent": self.name,
                    "timestamp": self.last_run_time,
                    "elapsed_time": time.time() - start_time
                })
            
            self.last_run_duration = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"Error running agent {self.name}: {str(e)}", exc_info=True)
            self.last_run_duration = time.time() - start_time
            
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "agent": self.name,
                "timestamp": self.last_run_time,
                "elapsed_time": self.last_run_duration
            }
    
    def _run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Placeholder for the agent's main functionality.
        
        Should be overridden by subclasses.
        
        Returns:
            Result dictionary
        """
        return {
            "status": "warning",
            "message": f"Agent {self.name} does not implement _run()",
            "data": {}
        }
        
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
            "status": "error",
            "error_type": error_type,
            "message": message,
            "agent": self.name,
            "timestamp": datetime.now().isoformat()
        }
        
    def validate_input(self, symbol: Optional[str], interval: Optional[str]) -> bool:
        """
        Validate basic input parameters.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            True if inputs are valid, False otherwise
        """
        if not symbol:
            logger.warning("Missing symbol parameter")
            return False
            
        if not interval:
            logger.warning("Missing interval parameter")
            return False
            
        return True

class AnalystAgentInterface(AgentInterface):
    """
    Interface for analyst agents that provide market insights.
    
    These agents analyze market data and provide trading signals.
    """
    
    @abstractmethod
    def analyze(self, symbol: Optional[str] = None, interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze market data and generate insights.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Analysis results
        """
        pass
    
    @abstractmethod
    def _fetch_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch market data for analysis.
        
        Args:
            symbol: Trading symbol
            **kwargs: Additional parameters
            
        Returns:
            Market data
        """
        pass

class BaseAnalystAgent(BaseAgent, AnalystAgentInterface):
    """
    Base class for analyst agents that provide market insights.
    
    These agents analyze market data and provide trading signals.
    """
    
    def __init__(self, agent_name: str = "base_analyst"):
        """
        Initialize a base analyst agent.
        
        Args:
            agent_name: Name of the agent
        """
        super().__init__(agent_name=agent_name)
        self.description = "Base analyst agent implementation"
        
    def run(self, symbol: Optional[str] = None, interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Run the analyst agent with the specified parameters.
        
        This method serves as a wrapper for the analyze method.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Analysis results
        """
        if not symbol:
            trading_config = self.get_trading_config()
            symbol = trading_config.get("default_symbol", "BTC/USDT")
            
        if not interval:
            trading_config = self.get_trading_config()
            interval = trading_config.get("default_interval", "1h")
            
        return super().run(symbol=symbol, interval=interval, **kwargs)
        
    def _run(self, symbol: Optional[str] = None, interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Run the analyst agent's analyze method.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Analysis results
        """
        return self.analyze(symbol=symbol, interval=interval, **kwargs)
    
    def analyze(self, symbol: Optional[str] = None, market_data: Optional[Dict[str, Any]] = None, 
                interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze market data and generate insights.
        
        This method should be overridden by subclasses.
        
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
        
    def _fetch_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch market data for analysis.
        
        This method should be overridden by subclasses.
        
        Args:
            symbol: Trading symbol
            **kwargs: Additional parameters
            
        Returns:
            Market data
        """
        return {}

class DecisionAgentInterface(AgentInterface):
    """
    Interface for decision-making agents that determine trading actions.
    
    These agents combine multiple analysis results to make trading decisions.
    """
    
    @abstractmethod
    def make_decision(self, symbol: str, interval: str, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Make a trading decision based on multiple analyses.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            analyses: List of analysis results from different agents
            
        Returns:
            Decision result
        """
        pass

class BaseDecisionAgent(BaseAgent, DecisionAgentInterface):
    """
    Base class for decision-making agents that determine trading actions.
    
    These agents combine multiple analysis results to make trading decisions.
    """
    
    def __init__(self, agent_name: str = "base_decision"):
        """
        Initialize a base decision agent.
        
        Args:
            agent_name: Name of the agent
        """
        super().__init__(agent_name=agent_name)
        self.description = "Base decision agent implementation"
        
        # Load agent weights from config
        config = self.get_agent_config()
        self.confidence_threshold = config.get("confidence_threshold", 70)
        
    def run(self, symbol: str, interval: str, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run the decision agent with the specified parameters.
        
        This method serves as a wrapper for the make_decision method.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            analyses: List of analysis results from different agents
            
        Returns:
            Decision results
        """
        return super().run(symbol=symbol, interval=interval, analyses=analyses)
        
    def _run(self, symbol: str, interval: str, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run the decision agent's make_decision method.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            analyses: List of analysis results from different agents
            
        Returns:
            Decision results
        """
        return self.make_decision(symbol=symbol, interval=interval, analyses=analyses)
    
    def make_decision(self, symbol: str, interval: str, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Make a trading decision based on multiple analyses.
        
        This method should be overridden by subclasses.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            analyses: List of analysis results from different agents
            
        Returns:
            Decision result
        """
        return self.build_error_response(
            "NOT_IMPLEMENTED", 
            f"Agent {self.name} does not implement make_decision()"
        )

class ExecutionAgentInterface(AgentInterface):
    """
    Interface for execution agents that execute trading actions.
    
    These agents interact with exchange APIs to place and manage orders.
    """
    
    @abstractmethod
    def execute_trade(self, symbol: str, side: str, quantity: float, price: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        """
        Execute a trade on the exchange.
        
        Args:
            symbol: Trading symbol
            side: Trade side (buy or sell)
            quantity: Quantity to trade
            price: Price to trade at (optional for market orders)
            **kwargs: Additional parameters
            
        Returns:
            Execution result
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            order_id: ID of the order to cancel
            **kwargs: Additional parameters
            
        Returns:
            Cancellation result
        """
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Get a list of open orders.
        
        Args:
            symbol: Trading symbol (optional)
            **kwargs: Additional parameters
            
        Returns:
            List of open orders
        """
        pass
    
    @abstractmethod
    def get_position(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Get current position for a symbol.
        
        Args:
            symbol: Trading symbol
            **kwargs: Additional parameters
            
        Returns:
            Position information
        """
        pass
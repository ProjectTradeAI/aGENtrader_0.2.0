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

class BaseAgent:
    """BaseAgent for aGENtrader v0.2.2"""
    
    def __init__(self, agent_name: str):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Name of the agent
        """
        self.version = "v0.2.2"
        self.agent_name = agent_name
        self.name = agent_name  # For backward compatibility
        self.description = "Base analyst agent implementation"
        
    def build_error_response(self, error_code: str, error_message: str) -> Dict[str, Any]:
        """
        Build a standardized error response.
        
        Args:
            error_code: Error code string
            error_message: Error message description
            
        Returns:
            Error response dictionary
        """
        return {
            "error": True,
            "error_code": error_code,
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name
        }
    
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get the agent's configuration.
        
        Returns:
            Configuration dictionary
        """
        return {}
        
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
            symbol = "BTC/USDT"  # Default symbol
            
        if not interval:
            interval = "1h"  # Default interval
            
        return self._run(symbol=symbol, interval=interval, **kwargs)
        
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

class BaseAnalystAgent(BaseAgent):
    """
    Base class for analyst agents that analyze market data.
    
    These agents perform specialized analysis on market data and generate insights.
    """
    
    def __init__(self, agent_name: str = "base_analyst"):
        """
        Initialize a base analyst agent.
        
        Args:
            agent_name: Name of the agent
        """
        super().__init__(agent_name)
        self.version = "v0.2.2"
        self.description = "Base analyst agent implementation"
        
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
        super().__init__(agent_name)
        self.description = "Base decision agent implementation"
        
        # Load agent weights from config
        config = self.get_agent_config()
        self.confidence_threshold = config.get("confidence_threshold", 70)
        
    def run(self, symbol: str, interval: str, analyses: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Run the decision agent with the specified parameters.
        
        This method serves as a wrapper for the make_decision method.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            analyses: List of analysis results from different agents
            **kwargs: Additional parameters
            
        Returns:
            Decision results
        """
        return self._run(symbol=symbol, interval=interval, analyses=analyses, **kwargs)
        
    def _run(self, symbol: str, interval: str, analyses: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Run the decision agent's make_decision method.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            analyses: List of analysis results from different agents
            **kwargs: Additional parameters
            
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
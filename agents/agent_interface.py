"""
aGENtrader v2 Agent Interface Module

This module defines the standard interfaces that all agents must implement.
These interfaces promote consistency across agent implementations and
make the system more maintainable.
"""

import abc
from typing import Dict, Any, Optional, List, Union

class AgentInterface(abc.ABC):
    """
    Base interface that all aGENtrader agents must implement.
    
    This interface defines the minimal contract that all agents
    must fulfill to be compatible with the system.
    """
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """
        Get the name of the agent.
        
        Returns:
            String name of the agent
        """
        pass
    
    @property
    @abc.abstractmethod
    def description(self) -> str:
        """
        Get the description of the agent.
        
        Returns:
            String description of the agent's functionality
        """
        pass
    
    @property
    @abc.abstractmethod
    def version(self) -> str:
        """
        Get the version of the agent.
        
        Returns:
            String version of the agent implementation
        """
        pass


class AnalystAgentInterface(AgentInterface):
    """
    Interface for analyst agents that produce market analysis.
    
    Analyst agents examine market data and produce analysis results
    with trading signals and confidence levels.
    """
    
    @abc.abstractmethod
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and produce results.
        
        Args:
            market_data: Dictionary containing market data for analysis
            
        Returns:
            Dictionary with analysis results including at minimum:
            - signal: String trading signal (BUY, SELL, HOLD)
            - confidence: Integer confidence level (0-100)
            - reasoning: String explanation of the analysis
            - data: Optional dictionary with supporting data
        """
        pass


class DecisionAgentInterface(AgentInterface):
    """
    Interface for decision agents that synthesize analysis results.
    
    Decision agents take in the results of various analyst agents
    and produce a final trading decision.
    """
    
    @abc.abstractmethod
    def make_decision(self) -> Dict[str, Any]:
        """
        Make a trading decision based on analyst results.
        
        Returns:
            Dictionary with decision results including at minimum:
            - signal: String trading signal (BUY, SELL, HOLD)
            - confidence: Integer confidence level (0-100)
            - reasoning: String explanation of the decision
            - data: Optional dictionary with supporting data
            - contributions: Dictionary mapping analyst names to their contribution weight
        """
        pass
    
    @abc.abstractmethod
    def add_analyst_result(self, analysis_type: str, result: Dict[str, Any]) -> None:
        """
        Add an analyst result to be considered in decision making.
        
        Args:
            analysis_type: Type of analysis (e.g., 'technical', 'sentiment')
            result: Dictionary with analysis results
        """
        pass


class ExecutionAgentInterface(AgentInterface):
    """
    Interface for execution agents that handle trade execution.
    
    Execution agents take trading decisions and execute them on
    the target exchange, handling order management and monitoring.
    """
    
    @abc.abstractmethod
    def execute_trade(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade based on a decision.
        
        Args:
            decision: Dictionary with trading decision
            
        Returns:
            Dictionary with execution results
        """
        pass
    
    @abc.abstractmethod
    def get_position_status(self, symbol: str) -> Dict[str, Any]:
        """
        Get the current position status for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with position information
        """
        pass
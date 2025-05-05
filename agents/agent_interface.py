"""
aGENtrader v2 Agent Interfaces

This module defines the standard interfaces for all agents in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union

class AgentInterface(ABC):
    """
    Base interface for all agents in the system.
    
    All agents must implement this interface to ensure consistent behavior.
    """
    
    @abstractmethod
    def __init__(self, **kwargs):
        """Initialize the agent with configuration."""
        pass
    
    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the agent's core functionality.
        
        Returns:
            Dictionary with the agent's output
        """
        pass

class AnalystAgentInterface(AgentInterface):
    """
    Interface for analyst agents that perform market analysis.
    
    All analyst agents should implement this interface with standard
    method signatures and return value formats.
    """
    
    @abstractmethod
    def analyze(self, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Analyze market data and return insights.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Dictionary with analysis results including:
            - signal: Trading signal (BUY, SELL, HOLD)
            - confidence: Confidence level (0-100)
            - reasoning: Explanation of the analysis
            - data: Additional data relevant to the analysis
        """
        pass

class DecisionAgentInterface(AgentInterface):
    """
    Interface for decision-making agents that consolidate signals.
    
    Decision agents should implement this interface to ensure
    consistent behavior when combining signals from analyst agents.
    """
    
    @abstractmethod
    def make_decision(self, analyst_results: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Make a trading decision based on analyst results.
        
        Args:
            analyst_results: Dictionary containing outputs from analyst agents
            
        Returns:
            Dictionary with decision results including:
            - signal: Final trading signal (BUY, SELL, HOLD)
            - confidence: Overall confidence level (0-100)
            - reasoning: Explanation of the decision process
            - contributions: How each analyst contributed to the decision
        """
        pass

class ExecutionAgentInterface(AgentInterface):
    """
    Interface for execution agents that handle trade execution.
    
    Execution agents should implement this interface to ensure
    consistent behavior when executing trades.
    """
    
    @abstractmethod
    def execute_trade(self, decision: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Execute a trade based on a trading decision.
        
        Args:
            decision: Dictionary containing trading decision
            
        Returns:
            Dictionary with execution results including:
            - status: Execution status (SUCCESS, FAILURE, PARTIAL)
            - order_id: ID of the executed order (if successful)
            - error: Error message (if failure)
            - details: Additional execution details
        """
        pass
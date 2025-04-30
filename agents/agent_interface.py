"""
aGENtrader v2 Agent Interface

This module defines the base interfaces for all agent types in the system.
These interfaces ensure consistent API across different agent implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union


class AgentInterface(ABC):
    """
    Base interface for all agents in the system.
    
    This interface defines the minimal contract that all agents must fulfill.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for identification and logging"""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of agent's purpose and function"""
        pass
        
    @property
    @abstractmethod
    def version(self) -> str:
        """Agent version, typically aligned with system version"""
        pass


class AnalystAgentInterface(AgentInterface):
    """
    Interface for agents that analyze specific aspects of market data.
    
    These agents provide signal, confidence, and reasoning based on their analysis.
    """
    
    @abstractmethod
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and produce a signal with confidence.
        
        Args:
            market_data: Dictionary containing market data, including:
                - symbol: Trading symbol (e.g., BTC/USDT)
                - interval: Time interval (e.g., 1h, 4h, 1d)
                - ohlcv: List of OHLCV data
                - current_price: Current price
                - timestamp: Timestamp of the data
                
        Returns:
            Dictionary containing analysis results, including:
                - signal: Trading signal (BUY, SELL, HOLD, NEUTRAL)
                - confidence: Confidence level (0-100 integer)
                - reasoning: Explanation for the signal
                - data: Additional data and metrics from the analysis
                - timestamp: Analysis timestamp
        """
        pass
        
    @abstractmethod
    def create_standard_result(
        self, 
        signal: str, 
        confidence: int, 
        reason: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized result dictionary.
        
        Args:
            signal: Trading signal (BUY, SELL, HOLD, NEUTRAL)
            confidence: Confidence level (0-100 integer)
            reason: Explanation for the signal
            data: Additional data and metrics from the analysis
            
        Returns:
            Standardized result dictionary
        """
        pass
        
    @abstractmethod
    def handle_analysis_error(self, error: Exception, analysis_type: str) -> Dict[str, Any]:
        """
        Create an error result when analysis fails.
        
        Args:
            error: The exception that occurred
            analysis_type: Type of analysis that failed
            
        Returns:
            Error result dictionary with HOLD signal and 0 confidence
        """
        pass


class DecisionAgentInterface(AgentInterface):
    """
    Interface for agents that make trading decisions based on analyst inputs.
    
    These agents aggregate and weigh signals from multiple analyst agents.
    """
    
    @abstractmethod
    def add_analyst_result(self, analysis_type: str, result: Dict[str, Any]) -> None:
        """
        Add an analyst's result to be considered in decision making.
        
        Args:
            analysis_type: Type of analysis (e.g., 'technical', 'sentiment')
            result: Analyst result dictionary
        """
        pass
        
    @abstractmethod
    def make_decision(self) -> Dict[str, Any]:
        """
        Make a trading decision based on collected analyst results.
        
        Returns:
            Dictionary containing the decision, including:
                - signal: Trading signal (BUY, SELL, HOLD)
                - confidence: Overall confidence level (0-100)
                - reasoning: Explanation for the decision
                - contributions: How each analyst contributed
                - timestamp: Decision timestamp
        """
        pass
        
    @abstractmethod
    def clear_analyst_results(self) -> None:
        """
        Clear all collected analyst results.
        """
        pass


class ExecutionAgentInterface(AgentInterface):
    """
    Interface for agents that execute trading decisions.
    
    These agents handle trade execution, position management, and risk control.
    """
    
    @abstractmethod
    def execute_trade(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade based on a decision.
        
        Args:
            decision: Trading decision dictionary
            
        Returns:
            Dictionary containing execution results
        """
        pass
        
    @abstractmethod
    def get_position(self, symbol: str) -> Dict[str, Any]:
        """
        Get current position for a trading symbol.
        
        Args:
            symbol: Trading symbol (e.g., BTC/USDT)
            
        Returns:
            Dictionary containing position information
        """
        pass
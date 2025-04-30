"""
aGENtrader v2 Base Agent

This module provides base implementations for the agent interfaces.
These base classes handle common functionality for all agent types.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from .agent_interface import AgentInterface, AnalystAgentInterface, DecisionAgentInterface

# Configure logging
logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base class for all agents in the system.
    
    This class implements the common functionality required by all agents.
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Name of the agent
        """
        self._agent_name = agent_name
        self._init_time = time.time()
        
        # Initialize logger
        self._logger = logging.getLogger(f"aGENtrader.agents.{agent_name}")
        
    @property
    def name(self) -> str:
        """Get the agent's name."""
        return self._agent_name
        
    @property
    def description(self) -> str:
        """Get the agent's description."""
        return "Base agent implementation"
        
    @property
    def version(self) -> str:
        """Get the agent's version."""
        try:
            from core.version import VERSION
            return VERSION
        except ImportError:
            return "0.2.0"  # Default version if version module not found
            
    def get_current_timestamp(self) -> str:
        """
        Get the current timestamp in ISO format.
        
        Returns:
            Timestamp string in ISO format
        """
        return datetime.now().isoformat()
        
    def validate_input(self, *args, **kwargs) -> bool:
        """
        Validate input parameters.
        
        Args:
            *args: Positional arguments to validate
            **kwargs: Keyword arguments to validate
            
        Returns:
            True if all inputs are valid, False otherwise
        """
        # Basic implementation, subclasses should override with specific validation
        return all(arg is not None for arg in args) and all(kwarg is not None for kwarg in kwargs.values())
        
    def build_error_response(
        self, 
        error_code: str, 
        error_message: str, 
        signal: str = "HOLD"
    ) -> Dict[str, Any]:
        """
        Build a standardized error response.
        
        Args:
            error_code: Error code
            error_message: Error message
            signal: Default signal to use (usually HOLD)
            
        Returns:
            Standardized error response dictionary
        """
        return {
            "signal": signal,
            "confidence": 0,
            "reasoning": f"Error: {error_message}",
            "timestamp": self.get_current_timestamp(),
            "error": {
                "code": error_code,
                "message": error_message
            }
        }
        
    def validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize a result dictionary.
        
        Args:
            result: Result dictionary to validate
            
        Returns:
            Validated and normalized result dictionary
        """
        # Ensure required fields are present
        if "signal" not in result:
            result["signal"] = "HOLD"
            
        if "confidence" not in result:
            result["confidence"] = 0
            
        if "reasoning" not in result:
            result["reasoning"] = "No reasoning provided"
            
        if "timestamp" not in result:
            result["timestamp"] = self.get_current_timestamp()
            
        # Normalize signal to uppercase
        result["signal"] = result["signal"].upper()
        
        # Ensure confidence is an integer between 0 and 100
        try:
            result["confidence"] = int(result["confidence"])
            result["confidence"] = max(0, min(100, result["confidence"]))
        except (ValueError, TypeError):
            result["confidence"] = 0
            
        return result


class BaseAnalystAgent(BaseAgent, AnalystAgentInterface):
    """
    Base class for analyst agents that perform market analysis.
    
    This class implements common functionality for all analyst agents.
    """
    
    def __init__(self, agent_name: str, data_provider=None, config=None):
        """
        Initialize the base analyst agent.
        
        Args:
            agent_name: Name of the agent
            data_provider: Provider for market data
            config: Configuration dictionary
        """
        super().__init__(agent_name)
        self.data_provider = data_provider
        self.config = config or {}
        
        # Extract common config values
        self.symbol = self.config.get("symbol", "BTC/USDT")
        self.interval = self.config.get("interval", "1h")
        
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and produce a signal with confidence.
        
        This is a placeholder implementation. Subclasses should override this method.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Dictionary containing analysis results
        """
        self._logger.warning(f"{self.name} is using the base implementation of analyze()")
        return self.create_standard_result(
            signal="HOLD",
            confidence=0,
            reason="Base implementation - no analysis performed",
            data={"warning": "Subclass should override analyze method"}
        )
        
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
        result = {
            "signal": signal.upper(),
            "confidence": max(0, min(100, confidence)),
            "reasoning": reason,
            "timestamp": self.get_current_timestamp()
        }
        
        if data:
            result["data"] = data
            
        return result
        
    def handle_analysis_error(self, error: Exception, analysis_type: str) -> Dict[str, Any]:
        """
        Create an error result when analysis fails.
        
        Args:
            error: The exception that occurred
            analysis_type: Type of analysis that failed
            
        Returns:
            Error result dictionary with HOLD signal and 0 confidence
        """
        error_message = f"{analysis_type} analysis failed: {str(error)}"
        self._logger.error(error_message, exc_info=True)
        
        return self.create_standard_result(
            signal="HOLD",
            confidence=0,
            reason=f"Error in {analysis_type} analysis",
            data={
                "error": str(error),
                "error_type": error.__class__.__name__
            }
        )


class BaseDecisionAgent(BaseAgent, DecisionAgentInterface):
    """
    Base class for decision agents that make trading decisions.
    
    This class implements common functionality for making decisions based on analyst inputs.
    """
    
    def __init__(self, agent_name: str, analyst_results: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the base decision agent.
        
        Args:
            agent_name: Name of the agent
            analyst_results: Initial analyst results
        """
        super().__init__(agent_name)
        self.analyst_results = analyst_results or {}
        self.weights = self._default_weights()
        
    def _default_weights(self) -> Dict[str, float]:
        """
        Get default weights for different analysis types.
        
        Returns:
            Dictionary mapping analysis types to weights
        """
        return {
            "technical_analysis": 0.30,
            "sentiment_analysis": 0.20,
            "liquidity_analysis": 0.20,
            "funding_rate_analysis": 0.15,
            "open_interest_analysis": 0.15
        }
        
    def add_analyst_result(self, analysis_type: str, result: Dict[str, Any]) -> None:
        """
        Add an analyst's result to be considered in decision making.
        
        Args:
            analysis_type: Type of analysis (e.g., 'technical', 'sentiment')
            result: Analyst result dictionary
        """
        self.analyst_results[analysis_type] = self.validate_result(result)
        
    def clear_analyst_results(self) -> None:
        """
        Clear all collected analyst results.
        """
        self.analyst_results = {}
        
    def make_decision(self) -> Dict[str, Any]:
        """
        Make a trading decision based on collected analyst results.
        
        This is a simple implementation that weighs signals by confidence and weights.
        Subclasses can override with more sophisticated decision algorithms.
        
        Returns:
            Dictionary containing the decision
        """
        if not self.analyst_results:
            return self.build_error_response(
                "NO_ANALYST_RESULTS",
                "No analyst results available for decision making",
                "HOLD"
            )
            
        # Calculate weighted scores for each possible signal
        signal_scores = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        contributions = {}
        
        for analysis_type, result in self.analyst_results.items():
            # Skip results with errors
            if "error" in result:
                continue
                
            signal = result.get("signal", "HOLD").upper()
            confidence = result.get("confidence", 0)
            
            # Get weight for this analysis type
            weight = self.weights.get(analysis_type, 0.1)
            
            # Calculate contribution
            contribution = confidence * weight
            
            # Add contribution to appropriate signal
            if signal in signal_scores:
                signal_scores[signal] += contribution
            else:
                # Handle non-standard signals (NEUTRAL, etc.)
                signal_scores["HOLD"] += contribution
                
            # Record contribution
            contributions[analysis_type] = {
                "signal": signal,
                "confidence": confidence,
                "contribution": contribution
            }
            
        # Determine overall signal based on highest score
        decision_signal = max(signal_scores.items(), key=lambda x: x[1])[0]
        
        # Calculate total confidence (normalize to 0-100 scale)
        total_contribution = sum(signal_scores.values())
        total_possible = sum(self.weights.values()) * 100
        overall_confidence = int((total_contribution / total_possible) * 100) if total_possible > 0 else 0
        
        # Build reasoning text
        reasoning_parts = []
        for analysis_type, contrib_data in contributions.items():
            signal = contrib_data["signal"]
            confidence = contrib_data["confidence"]
            contribution = contrib_data["contribution"]
            
            reasoning_parts.append(
                f"{analysis_type} gives {signal} with {confidence}% confidence "
                f"(contribution: {contribution:.1f})"
            )
        
        reasoning = "Decision based on: " + ". ".join(reasoning_parts)
        
        # Build final decision
        decision = {
            "signal": decision_signal,
            "confidence": overall_confidence,
            "reasoning": reasoning,
            "timestamp": self.get_current_timestamp(),
            "contributions": contributions,
            "data": {
                "signal_scores": signal_scores,
                "analyst_data": {
                    analysis_type: result.get("data", {})
                    for analysis_type, result in self.analyst_results.items()
                }
            }
        }
        
        return decision
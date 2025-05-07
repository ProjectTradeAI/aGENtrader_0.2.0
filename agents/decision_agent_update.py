"""
aGENtrader v0.2.2 DecisionAgent Update with Self-Sanity Checks

This module provides an updated implementation for the DecisionAgent
that incorporates self-sanity checks to filter out agent outputs that don't pass
validation before making decisions.
"""

import logging
import traceback
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def make_decision_with_sanity_checks(self,
                     agent_analyses: Optional[Dict[str, Any]] = None,
                     symbol: Optional[str] = None,
                     interval: Optional[str] = None,
                     agent_weights_override: Optional[Dict[str, float]] = None,
                     market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Make a trading decision based on agent analyses with sanity checks.
    
    Args:
        agent_analyses: Dictionary containing analyses from specialized agents
        symbol: Trading symbol (default from config)
        interval: Time interval (default from config)
        agent_weights_override: Optional dictionary to override default agent weights
        market_data: Optional dictionary containing additional market data including data_provider
        
    Returns:
        Dictionary with trading decision
    """
    try:
        # If no agent_analyses provided, use the stored analyst_results
        if agent_analyses is None:
            agent_analyses = self.analyst_results
            
        # Validate inputs
        if not isinstance(agent_analyses, dict):
            raise ValidationError(f"agent_analyses must be a dictionary, got {type(agent_analyses)}")
            
        # Use symbol from instance if provided, or from parameters
        if self.symbol is not None:
            symbol = symbol or self.symbol
        symbol = symbol or self.default_symbol
        
        interval = interval or self.default_interval
        # Update the instance variable for interval (needed for conflict logging)
        self.interval = interval
        
        # Use provided agent weights if specified, otherwise use config weights
        agent_weights = agent_weights_override or self.agent_weights
        
        # Ensure agent weights is a dictionary
        if agent_weights and not isinstance(agent_weights, dict):
            self.logger.warning(f"agent_weights must be a dictionary, got {type(agent_weights)}")
            agent_weights = self.agent_weights  # Fall back to default weights
        
        self.logger.info(f"Making decision for {symbol} at {interval} interval")
        
        # Make sure symbol format is consistent
        symbol_normalized = symbol.replace("/", "") if symbol else ""
        display_symbol = symbol or self.default_symbol
        
        # Basic validation for empty analyses
        if not agent_analyses:
            self.logger.warning("No agent analyses provided")
            return self._create_safe_decision(
                action="HOLD",
                pair=display_symbol,
                confidence=0,
                reason="Insufficient data for decision",
                error=True,
                error_type="Missing Data"
            )
        
        # Filter out analyses with errors or that failed sanity checks
        valid_analyses = {}
        rejected_analyses = {}
        
        for key, analysis in agent_analyses.items():
            if not isinstance(analysis, dict):
                rejected_analyses[key] = {"error": True, "reason": "Not a dictionary"}
                continue
                
            # Check for error flag
            if analysis.get("error", False):
                rejected_analyses[key] = analysis
                continue
                
            # Check for sanity check flag
            passed_sanity = analysis.get("passed_sanity_check", True)  # Default to True for backward compatibility
            if not passed_sanity:
                self.logger.warning(f"Analysis from {key} failed its self-sanity check, excluding from decision")
                rejected_analyses[key] = analysis
                continue
                
            # If we get here, the analysis passed checks
            valid_analyses[key] = analysis
            
        # Log the rejected analyses
        if rejected_analyses:
            self.logger.warning(f"Rejected {len(rejected_analyses)} analyses that failed validity checks: {', '.join(rejected_analyses.keys())}")
                
        # Check if we have any valid analyses left after filtering
        if not valid_analyses:
            self.logger.warning("All agent analyses failed validity or sanity checks")
            return self._create_safe_decision(
                action="HOLD",
                pair=display_symbol,
                confidence=0,
                reason="All agent analyses failed sanity checks",
                error=True,
                error_type="All Failed Sanity Check"
            )
        
        # Log the analyses we're working with
        self.logger.info(f"Making decision with analyses from: {', '.join(valid_analyses.keys())}")
        
        # If we have enough agent data, try to make a weighted decision first
        if len(valid_analyses) >= 2:
            weighted_decision = self._make_weighted_decision(valid_analyses, str(display_symbol), agent_weights)
            if weighted_decision:
                # Ensure the decision includes passed_sanity_check flag
                weighted_decision["passed_sanity_check"] = True
                return weighted_decision
        
        # Rule-based decision if only liquidity analysis is available
        if "liquidity_analysis" in valid_analyses and len(valid_analyses) == 1:
            decision = self._make_liquidity_based_decision(valid_analyses["liquidity_analysis"], str(display_symbol))
            decision["passed_sanity_check"] = True
            return decision
        
        # If we have analyses, use LLM to synthesize
        decision = self._make_llm_decision(valid_analyses, str(display_symbol))
        decision["passed_sanity_check"] = True
        return decision
        
    except Exception as e:
        # Handle unexpected errors
        self.logger.error(f"Unexpected error in decision making: {e}")
        self.logger.error(traceback.format_exc())
        error_decision = self._handle_decision_error(e, symbol or self.default_symbol, "Unexpected Error")
        error_decision["passed_sanity_check"] = False
        return error_decision


def _create_safe_decision(self, action: str, pair: str, confidence: int, reason: str, 
                         error: bool = False, error_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a safe fallback decision when normal decision making isn't possible.
    
    Args:
        action: Trading action (BUY, SELL, HOLD, etc.)
        pair: Trading pair
        confidence: Confidence percentage
        reason: Reason for the decision
        error: Whether this decision is due to an error
        error_type: Type of error that caused this fallback
        
    Returns:
        Safe decision dictionary with passed_sanity_check flag
    """
    current_time = datetime.now().isoformat()
    
    # Create the decision
    decision = {
        "agent_name": self.agent_name,
        "timestamp": current_time,
        "symbol": pair,
        "interval": self.interval,
        "signal": action,
        "confidence": confidence,
        "directional_confidence": 0,
        "reasoning": reason,
        "contributing_agents": [],
        "conflict_score": 0,
        "passed_sanity_check": True  # Fallback decisions are considered sane by definition
    }
    
    # Add error info if applicable
    if error:
        decision["error"] = True
        decision["error_type"] = error_type or "Unknown Error"
        
    self.logger.warning(f"Using safe fallback {action} decision for {pair}: {reason}")
    
    return decision
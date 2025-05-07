"""
Updated Decision Agent Module for aGENtrader v0.2.2

This module enhances the DecisionAgent with self-sanity checks to filter out
agent outputs that don't pass validation before making decisions.
"""

import os
import sys
import json
import yaml
import logging
import traceback
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
from functools import wraps

# Add parent directory to path to allow importing from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import base agent module
from agents.base_agent import BaseAgent, BaseDecisionAgent

# Import required modules
from models.llm_client import LLMClient

# Import error handling utilities
from utils.error_handler import (
    ValidationError,
    DataFetchingError,
    retry_with_backoff,
    handle_api_errors,
    check_api_keys,
    request_api_key
)

# Import conflict logging utilities
from utils.conflict_logger import log_conflict

# Import sanity check utilities
try:
    from utils.sanity_check import filter_passed_sanity_checks
    SANITY_CHECKS_AVAILABLE = True
except ImportError:
    SANITY_CHECKS_AVAILABLE = False
    logging.warning("Sanity check utilities not available. Falling back to basic validation.")

# Configure logging
logger = logging.getLogger(__name__)

class DecisionAgent(BaseDecisionAgent):
    """
    Enhanced Decision Agent with self-sanity checks for aGENtrader v0.2.2
    
    This agent integrates analysis from other specialized agents and produces
    a final trading decision with confidence score and reasoning.
    
    It filters out any agent outputs that failed their self-sanity checks
    before making decisions.
    """
    
    def __init__(self, 
                 config: Optional[Dict[str, Any]] = None,
                 agent_weights: Optional[Dict[str, float]] = None,
                 min_confidence_threshold: Optional[int] = None,
                 symbol: Optional[str] = None):
        """
        Initialize the decision agent.
        
        Args:
            config: Configuration dictionary (optional)
            agent_weights: Agent weight dictionary (optional)
            min_confidence_threshold: Minimum confidence threshold (optional)
            symbol: Trading symbol (optional)
        """
        super().__init__("decision_agent")
        self.version = "v0.2.2"
        
        # Initialize with provided config or load from configuration file
        self.config = config or self.get_agent_config()
        
        # Default values
        self.default_symbol = self.config.get("default_pair", "BTC/USDT")
        self.default_interval = self.config.get("default_interval", "1h")
        self.min_confidence_threshold = min_confidence_threshold or self.config.get("min_confidence_threshold", 70)
        self.fallback_decision_enabled = self.config.get("fallback_decision_enabled", True)
        
        # Set symbol instance variable (used in logging and decisions)
        self.symbol = symbol or self.default_symbol
        
        # Set up agent weights - priority: 1) provided weights, 2) config weights, 3) defaults
        config_weights = {}
        if "agent_weights" in self.config:
            config_weights = self.config["agent_weights"]
        else:
            # Try to load from root config
            root_config = self.load_config_section("agent_weights")
            if root_config:
                config_weights = root_config
                
        self.agent_weights = agent_weights or config_weights or {
            "TechnicalAnalystAgent": 1.2,
            "SentimentAnalystAgent": 0.8,
            "LiquidityAnalystAgent": 1.0,
            "FundingRateAnalystAgent": 0.8,
            "OpenInterestAnalystAgent": 1.0
        }
        
        # Setup LLM client
        try:
            self.llm_client = self._setup_llm_client()
        except AttributeError:
            logging.warning("LLM client setup method not available, continuing without LLM support")
            self.llm_client = None
        
        # Store analyst results
        self.analyst_results = {}
        
        # Time interval
        self.interval = self.default_interval
        
        # Logger
        self.logger = logging.getLogger("aGENtrader.agents.decision")
        self.logger.info(f"Decision agent initialized with min confidence threshold: {self.min_confidence_threshold}%")
    
    def make_decision(self,
                     agent_analyses: Optional[Dict[str, Any]] = None,
                     symbol: Optional[str] = None,
                     interval: Optional[str] = None,
                     agent_weights_override: Optional[Dict[str, float]] = None,
                     market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a trading decision based on agent analyses.
        
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
            self.logger.info(f"Using agent weights: {agent_weights}")
            
            # Make sure symbol format is consistent
            symbol_normalized = symbol.replace("/", "") if symbol else ""
            display_symbol = symbol or self.default_symbol
            
            # Check for error states in agent analyses
            for analysis_key, analysis_data in agent_analyses.items():
                # Log a warning for any analysis with an error
                if isinstance(analysis_data, dict) and analysis_data.get("error") is True:
                    error_message = analysis_data.get("message", "Unknown error")
                    error_type = analysis_data.get("error_type", "General Error")
                    self.logger.warning(f"Error in {analysis_key}: {error_type} - {error_message}")
                    
                    # If this is an API key error, log critical message and prompt for key
                    if "api key" in error_message.lower() or error_type == "API Key Error":
                        if "coinapi" in error_message.lower():
                            self.logger.critical("Missing CoinAPI key detected in agent analysis")
                            # Try to access request_api_key if available
                            try:
                                request_api_key('coinapi_key', 'COINAPI_KEY')
                            except Exception:
                                # Log manually if function not available
                                self.logger.critical("Please set COINAPI_KEY environment variable or add to config/secrets.yaml")
            
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
            
        except ValidationError as e:
            # Handle validation errors
            self.logger.error(f"Validation error in decision making: {e}")
            error_decision = self._handle_decision_error(e, symbol or self.default_symbol, "Validation Error")
            error_decision["passed_sanity_check"] = False
            return error_decision
            
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
    
    def _setup_llm_client(self) -> Optional[LLMClient]:
        """
        Set up the LLM client for advanced decision making.
        
        Returns:
            Configured LLM client or None if setup fails
        """
        try:
            return LLMClient()
        except Exception as e:
            logging.warning(f"Failed to initialize LLM client: {str(e)}")
            return None
    
    def _make_weighted_decision(self, analyses: Dict[str, Any], symbol: str, agent_weights: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Make a weighted decision based on multiple analyses.
        
        Args:
            analyses: Dictionary of agent analyses
            symbol: Trading symbol
            agent_weights: Dictionary of agent weights
            
        Returns:
            Weighted decision dictionary or None if decision can't be made
        """
        self.logger.info(f"Attempting weighted decision from multiple analyses")
        
        # Default response if no valid signals
        if not analyses:
            return None
            
        # Collect all valid signals
        signals = {"BUY": [], "SELL": [], "HOLD": [], "NEUTRAL": []}
        signal_scores = {"BUY": 0, "SELL": 0, "HOLD": 0, "NEUTRAL": 0}
        agent_signals = {}
        
        for agent_type, analysis in analyses.items():
            # Skip if analysis is not a dictionary or doesn't have required fields
            if not isinstance(analysis, dict) or "signal" not in analysis or "confidence" not in analysis:
                continue
                
            # Get the signal and confidence
            signal = analysis.get("signal", "NEUTRAL")
            confidence = analysis.get("confidence", 0)
            
            # Skip invalid signals
            if signal not in signals:
                continue
                
            # Get the agent name
            agent_name = analysis.get("agent_name", agent_type)
            
            # Get the agent weight
            weight = 1.0  # Default weight
            for pattern, w in agent_weights.items():
                if pattern in agent_name:
                    weight = w
                    break
                    
            # Calculate weighted score
            weighted_score = confidence * weight
            
            # Log the agent's signal
            self.logger.info(f"{agent_name}: {signal} with confidence {confidence}, weight {weight}, weighted score {weighted_score}")
            
            # Add to signal list
            signals[signal].append({
                "agent": agent_name,
                "confidence": confidence,
                "weight": weight,
                "weighted_score": weighted_score
            })
            
            # Add to signal score
            signal_scores[signal] += weighted_score
            
            # Store in agent_signals for logging
            agent_signals[agent_name] = {
                "signal": signal,
                "confidence": confidence,
                "weight": weight,
                "weighted_score": weighted_score
            }
            
        # Log the signal breakdown
        self.logger.info("Signal breakdown:")
        for signal, agents in signals.items():
            count = len(agents)
            if count > 0:
                avg_confidence = sum(a["confidence"] for a in agents) / count
                self.logger.info(f"  {signal}: {count} agents (avg {avg_confidence:.1f}%, weighted score: {signal_scores[signal]})")
            else:
                self.logger.info(f"  {signal}: {count} agents")
                
        # Find the signal with the highest score
        max_score = 0
        max_signal = "NEUTRAL"
        for signal, score in signal_scores.items():
            if score > max_score:
                max_score = score
                max_signal = signal
                
        # If neutral is the highest, convert to HOLD for final signal
        final_signal = "HOLD" if max_signal == "NEUTRAL" else max_signal
        
        # If the signal is low confidence, convert to HOLD
        contributing_agents = [a["agent"] for a in signals[max_signal]]
        total_signal_confidence = sum(a["confidence"] for a in signals[max_signal]) / len(signals[max_signal]) if signals[max_signal] else 0
        
        # If neutral/hold has the top score, collect all neutral agents
        if final_signal == "HOLD":
            contributing_agents = [a["agent"] for a in signals["NEUTRAL"] + signals["HOLD"]]
            if contributing_agents:
                total_signal_confidence = sum(a["confidence"] for a in signals["NEUTRAL"] + signals["HOLD"]) / len(contributing_agents) if contributing_agents else 0
                
        # Calculate final confidence
        final_confidence = max(total_signal_confidence, max_score / (sum(signal_scores.values()) * 2) * 100) if sum(signal_scores.values()) > 0 else 0
        final_confidence = min(100, final_confidence)  # Cap at 100%
        
        # Check against minimum confidence threshold
        if final_confidence < self.min_confidence_threshold:
            if final_signal != "HOLD":
                self.logger.info(f"Signal {final_signal} was converted to HOLD due to low confidence ({final_confidence:.2f}%)")
                final_signal = "HOLD"
                final_confidence = min(max(final_confidence, 30), 70)  # Set hold confidence between 30-70%
                
        # Log the final decision
        self.logger.info(f"Final signal: {final_signal}, confidence: {final_confidence:.1f}%, directional confidence: {total_signal_confidence:.1f}%")
        self.logger.info(f"Contributing agents: {', '.join(contributing_agents)}")
        
        # Create decision dictionary
        decision = {
            "agent_name": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "interval": self.interval,
            "signal": final_signal,
            "confidence": final_confidence,
            "directional_confidence": total_signal_confidence,
            "reasoning": self._generate_reasoning(final_signal, final_confidence, contributing_agents),
            "contributing_agents": contributing_agents,
            "conflict_score": 0,  # TODO: Calculate conflict score
        }
        
        return decision
        
    def _make_liquidity_based_decision(self, liquidity_analysis: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Make a decision based on liquidity analysis only.
        
        Args:
            liquidity_analysis: Dictionary with liquidity analysis
            symbol: Trading symbol
            
        Returns:
            Decision dictionary
        """
        # Extract signal and confidence
        signal = liquidity_analysis.get("signal", "NEUTRAL")
        confidence = liquidity_analysis.get("confidence", 50)
        
        # Convert NEUTRAL to HOLD for final action
        final_signal = "HOLD" if signal == "NEUTRAL" else signal
        
        # Create decision dictionary
        decision = {
            "agent_name": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "interval": self.interval,
            "signal": final_signal,
            "confidence": confidence,
            "directional_confidence": confidence,
            "reasoning": f"Liquidity analysis indicates {signal} with {confidence}% confidence",
            "contributing_agents": ["LiquidityAnalystAgent"],
            "conflict_score": 0,
        }
        
        return decision
        
    def _make_llm_decision(self, analyses: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Make a decision using LLM to synthesize multiple analyses.
        
        Args:
            analyses: Dictionary of agent analyses
            symbol: Trading symbol
            
        Returns:
            Decision dictionary
        """
        # Default decision if LLM is not available
        if self.llm_client is None:
            return self._create_safe_decision(
                action="HOLD",
                pair=symbol,
                confidence=50,
                reason="LLM decision making not available, using cautious approach",
                error=False
            )
            
        # TODO: Implement LLM-based decision making
        # For now, use a simple fallback approach
        
        # Collect all signals and confidences
        signals = []
        confidences = []
        agent_names = []
        
        for agent_type, analysis in analyses.items():
            if isinstance(analysis, dict) and "signal" in analysis and "confidence" in analysis:
                signals.append(analysis.get("signal", "NEUTRAL"))
                confidences.append(analysis.get("confidence", 0))
                agent_names.append(analysis.get("agent_name", agent_type))
                
        # If no valid signals, return HOLD
        if not signals:
            return self._create_safe_decision(
                action="HOLD",
                pair=symbol,
                confidence=50,
                reason="No valid signals available",
                error=False
            )
            
        # Find the most common signal
        signal_counts = {}
        for signal in signals:
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
        max_count = 0
        max_signal = "NEUTRAL"
        for signal, count in signal_counts.items():
            if count > max_count:
                max_count = count
                max_signal = signal
                
        # Convert NEUTRAL to HOLD for final action
        final_signal = "HOLD" if max_signal == "NEUTRAL" else max_signal
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 50
        
        # Create decision dictionary
        decision = {
            "agent_name": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "interval": self.interval,
            "signal": final_signal,
            "confidence": avg_confidence,
            "directional_confidence": avg_confidence,
            "reasoning": f"Majority of agents ({max_count}/{len(signals)}) indicate {max_signal}",
            "contributing_agents": agent_names,
            "conflict_score": 1 - (max_count / len(signals)) if signals else 0,
        }
        
        return decision
        
    def _handle_decision_error(self, error: Exception, symbol: str, error_type: str = "Decision Error") -> Dict[str, Any]:
        """
        Handle errors during decision making.
        
        Args:
            error: Exception that occurred
            symbol: Trading symbol
            error_type: Type of error
            
        Returns:
            Error decision dictionary
        """
        # Create error decision
        decision = {
            "agent_name": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "interval": self.interval,
            "signal": "HOLD",
            "confidence": 0,
            "directional_confidence": 0,
            "reasoning": f"Error during decision making: {str(error)}",
            "contributing_agents": [],
            "conflict_score": 0,
            "error": True,
            "error_type": error_type,
            "error_message": str(error)
        }
        
        return decision
        
    def _generate_reasoning(self, signal: str, confidence: float, contributing_agents: List[str]) -> str:
        """
        Generate reasoning text for a decision.
        
        Args:
            signal: Trading signal
            confidence: Confidence percentage
            contributing_agents: List of contributing agent names
            
        Returns:
            Reasoning text
        """
        if signal == "HOLD" and confidence < self.min_confidence_threshold:
            return f"Confidence below threshold ({confidence:.2f}% < {self.min_confidence_threshold}%)"
            
        if not contributing_agents:
            return "No contributing agents"
            
        if len(contributing_agents) == 1:
            return f"{contributing_agents[0]} recommends {signal}"
            
        return ", ".join([f"{agent} recommends {signal}" for agent in contributing_agents])
"""
Decision Agent Module

This agent integrates analysis from other specialized agents and produces
a final trading decision with confidence score and reasoning.

The decision agent evaluates different inputs, weights their importance,
and applies decision rules to output a structured trading decision.
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

# Define decorator for handling LLM errors
def handle_llm_errors(func: Callable) -> Callable:
    """
    Decorator to handle LLM-related errors with graceful degradation.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get logger from instance if available (assuming self is first argument)
            logger = getattr(args[0], 'logger', logging.getLogger('decision_agent'))
            
            # Log error
            logger.error(f"LLM error in {func.__name__}: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Default symbol from kwargs or 'UNKNOWN'
            symbol = kwargs.get('symbol', 'UNKNOWN')
            
            # Return a safe fallback decision
            return {
                "action": "HOLD",
                "pair": symbol,
                "confidence": 0,
                "reason": f"LLM processing error: {str(e)}",
                "error": True,
                "error_type": "LLM Error",
                "decision_method": "fallback"
            }
    
    return wrapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=os.path.join(parent_dir, "logs/agent_output.log")
)
logger = logging.getLogger("decision_agent")

# Add console handler for debugging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Load configuration
def load_config(config_path: str = "config/settings.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    config_path = os.path.join(parent_dir, config_path)
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        # Return default config
        return {
            "agents": {
                "decision": {
                    "confidence_threshold": 70  # Minimum confidence to take action
                }
            },
            "trading": {
                "default_pair": "BTC/USDT",
                "default_interval": "1h"
            }
        }

class DecisionAgent:
    """
    Decision Agent that integrates analyses from specialized agents.
    
    This agent:
    - Receives analysis inputs from specialized agents
    - Evaluates and weighs different signals
    - Uses LLM to synthesize complex inputs
    - Produces a final structured trading decision
    """
    
    def __init__(self, allow_conflict_state: bool = True):
        """
        Initialize the Decision Agent.
        
        Args:
            allow_conflict_state: Whether to allow returning "CONFLICTED" state when there are strong opposing signals
        """
        self.logger = logging.getLogger("decision_agent")
        
        # Load configuration
        self.config = load_config()
        self.agent_config = self.config.get("agents", {}).get("decision", {})
        self.trading_config = self.config.get("trading", {})
        
        # Load agent weights and check for missing weights
        all_agents = [
            "TechnicalAnalystAgent", 
            "SentimentAnalystAgent", 
            "SentimentAggregatorAgent",
            "LiquidityAnalystAgent", 
            "OpenInterestAnalystAgent", 
            "FundingRateAnalystAgent"
        ]
        
        self.agent_weights = self.config.get("agent_weights", {})
        
        # Check for missing agent weights and log warnings
        missing_weights = []
        for agent in all_agents:
            if agent not in self.agent_weights:
                missing_weights.append(agent)
                # Set default weights by agent type
                default_weight = 1.0
                # Assign specific default weights for certain agents
                if agent == "SentimentAggregatorAgent":
                    default_weight = 0.8
                
                # Only initialize with default weight and log a warning
                self.logger.warning(f"⚠️ Missing weight for {agent}. Using default value {default_weight}. Please update settings.yaml.")
                self.agent_weights[agent] = default_weight
        
        # Log a summary warning if any weights were missing
        if missing_weights:
            self.logger.warning(f"⚠️ Missing weights detected for {len(missing_weights)} agents. Agent weighing may not be optimal.")
            self.logger.warning(f"Please update settings.yaml to include weights for: {', '.join(missing_weights)}")
        
        self.logger.info(f"Using agent weights: {self.agent_weights}")
        
        # Initialize LLM client with agent-specific configuration
        # Decision agent uses regular Mistral, not Grok
        self.llm_client = LLMClient(agent_name="decision_agent")
        
        # Set default parameters
        self.default_symbol = self.trading_config.get("default_pair", "BTC/USDT")
        self.default_interval = self.trading_config.get("default_interval", "1h")
        self.interval = self.default_interval  # Ensure interval attribute is always defined
        self.confidence_threshold = self.agent_config.get("confidence_threshold", 70)
        
        # Set conflict state handling flag
        self.allow_conflict_state = allow_conflict_state
        self.high_confidence_threshold = 80  # Threshold to consider a signal "high confidence"
        
        # Storage for analyst results (for compatibility with BaseDecisionAgent)
        self.analyst_results = {}
        
        # Symbol and price state
        self.symbol = None
        self.current_price = None
        
        self.logger.info(f"Decision Agent initialized with confidence threshold={self.confidence_threshold}, allow_conflict_state={self.allow_conflict_state}")
    
    def add_analyst_result(self, analysis_type: str, result: Dict[str, Any]) -> None:
        """
        Add an analyst result to be considered in decision making.
        
        Args:
            analysis_type: Type of analysis (e.g., 'technical_analysis', 'sentiment_analysis')
            result: Dictionary with analysis results
        """
        if not result:
            self.logger.warning(f"Received empty {analysis_type} result")
            return
        
        # Create a copy of the result to avoid modifying the original
        processed_result = result.copy()
        
        # Check for required fields and attempt to fix missing ones
        required_fields = ['signal', 'confidence', 'reasoning']
        missing_fields = []
        
        for field in required_fields:
            if field not in processed_result:
                missing_fields.append(field)
        
        # If fields are missing, try to fix them with reasonable defaults
        if missing_fields:
            self.logger.warning(f"{analysis_type} result missing required fields: {', '.join(missing_fields)}")
            
            # If signal is missing, default to NEUTRAL
            if 'signal' not in processed_result:
                processed_result['signal'] = 'NEUTRAL'
                self.logger.warning(f"Added default 'signal' (NEUTRAL) to {analysis_type} result")
            
            # If confidence is missing, default to 50%
            if 'confidence' not in processed_result:
                processed_result['confidence'] = 50
                self.logger.warning(f"Added default 'confidence' (50%) to {analysis_type} result")
            
            # If reasoning is missing, try to generate one from available data
            if 'reasoning' not in processed_result:
                # Check for alternative fields that might have reasoning
                reason = None
                for alt_field in ['reason', 'description', 'explanation', 'analysis', 'summary']:
                    if alt_field in processed_result and processed_result[alt_field]:
                        reason = processed_result[alt_field]
                        self.logger.info(f"Using '{alt_field}' as reasoning for {analysis_type}")
                        break
                
                # If no alternative field found, generate a basic reasoning
                if not reason:
                    signal = processed_result['signal']
                    confidence = processed_result['confidence']
                    reason = f"{analysis_type.replace('_', ' ').title()} indicates {signal} with {confidence}% confidence"
                    self.logger.warning(f"Generated basic reasoning for {analysis_type}")
                
                processed_result['reasoning'] = reason
        
        # Store the processed result
        self.analyst_results[analysis_type] = processed_result
        self.logger.info(f"Added {analysis_type} result with signal: {processed_result['signal']}, confidence: {processed_result['confidence']}")
    
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
            
            # Filter out analyses with errors
            valid_analyses = {}
            for key, analysis in agent_analyses.items():
                if not isinstance(analysis, dict) or not analysis.get("error"):
                    valid_analyses[key] = analysis
                    
            # Check if we have any valid analyses left after filtering
            if not valid_analyses:
                self.logger.warning("All agent analyses contain errors")
                return self._create_safe_decision(
                    action="HOLD",
                    pair=display_symbol,
                    confidence=0,
                    reason="All agent analyses contain errors",
                    error=True,
                    error_type="Invalid Data"
                )
            
            # Log the analyses we're working with
            self.logger.info(f"Making decision with analyses from: {', '.join(valid_analyses.keys())}")
            
            # If we have enough agent data, try to make a weighted decision first
            if len(valid_analyses) >= 2:
                weighted_decision = self._make_weighted_decision(valid_analyses, str(display_symbol), agent_weights)
                if weighted_decision:
                    return weighted_decision
            
            # Rule-based decision if only liquidity analysis is available
            if "liquidity_analysis" in valid_analyses and len(valid_analyses) == 1:
                return self._make_liquidity_based_decision(valid_analyses["liquidity_analysis"], str(display_symbol))
            
            # If we have analyses, use LLM to synthesize
            return self._make_llm_decision(valid_analyses, str(display_symbol))
            
        except ValidationError as e:
            # Handle validation errors
            self.logger.error(f"Validation error in decision making: {e}")
            return self._handle_decision_error(e, symbol or self.default_symbol, "Validation Error")
            
        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error in decision making: {e}")
            self.logger.error(traceback.format_exc())
            return self._handle_decision_error(e, symbol or self.default_symbol, "Unexpected Error")
        
    def _get_agent_name_from_analysis_key(self, analysis_key: str) -> str:
        """
        Extract agent name from analysis key.
        
        Args:
            analysis_key: The key used in the agent_analyses dictionary
            
        Returns:
            The agent name for weight lookup
        """
        # Map from analysis key to agent name
        agent_name_map = {
            "liquidity_analysis": "LiquidityAnalystAgent",
            "technical_analysis": "TechnicalAnalystAgent",
            "sentiment_analysis": "SentimentAnalystAgent",
            "sentiment_aggregator": "SentimentAggregatorAgent",
            "sentiment_aggregator_analysis": "SentimentAggregatorAgent",  # Added for both naming conventions
            "fundamental_analysis": "FundamentalAnalystAgent",
            "funding_rate_analysis": "FundingRateAnalystAgent",
            "open_interest_analysis": "OpenInterestAnalystAgent"
        }
        
        return agent_name_map.get(analysis_key, analysis_key)
        
    def _get_most_common_signal(self, 
                             agent_contributions: Dict[str, Dict[str, Any]], 
                             weighted: bool = True) -> tuple[str, float, Dict[str, int]]:
        """
        Determine the most common signal/action by voting, with optional weighting.
        
        Args:
            agent_contributions: Dictionary of agent contributions with actions and weights
            weighted: Whether to use weighted voting
            
        Returns:
            Tuple of (most_common_action, agreement_percentage, signal_counts)
        """
        # Count signals
        signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
        weighted_counts = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        total_weight = 0.0
        total_agents = 0
        
        # Count each agent's signal
        for agent_name, contribution in agent_contributions.items():
            action = contribution.get("action")
            if action is not None and action in signal_counts:
                # For simple counting
                signal_counts[action] += 1
                total_agents += 1
                
                # For weighted counting
                weight = contribution.get("weight", 1.0)
                confidence = contribution.get("confidence", 50.0)
                
                # Skip signals with very low confidence
                if confidence < 10:
                    continue
                    
                # Weight can be combined with confidence for a more nuanced approach
                if weighted:
                    # Use a combination of weight and confidence
                    # Normalize confidence to 0-1 range
                    norm_confidence = confidence / 100.0
                    # Adjusted weight is the product of agent weight and confidence
                    adjusted_weight = weight * norm_confidence
                    weighted_counts[action] += adjusted_weight
                    total_weight += adjusted_weight
                else:
                    # Just count the agents
                    weighted_counts[action] += weight
                    total_weight += weight
        
        # Determine most common signal
        if weighted:
            # Find the action with highest weighted count
            most_common_action = max(weighted_counts.items(), key=lambda x: x[1])
            action = most_common_action[0]
            
            # Calculate agreement percentage
            agreement_percentage = 0.0
            if total_weight > 0:
                agreement_percentage = (weighted_counts[action] / total_weight) * 100
        else:
            # Find the action with highest count
            most_common_action = max(signal_counts.items(), key=lambda x: x[1])
            action = most_common_action[0]
            
            # Calculate agreement percentage
            if total_agents > 0:
                agreement_percentage = (signal_counts[action] / total_agents) * 100
            else:
                agreement_percentage = 0.0
                
        # Default to HOLD if no action has votes
        if total_weight == 0 and weighted:
            action = "HOLD"
            agreement_percentage = 0.0
        elif total_agents == 0 and not weighted:
            action = "HOLD"
            agreement_percentage = 0.0
            
        return action, agreement_percentage, signal_counts
    
    def _calculate_confidence(self, action: str, confidence: float, status: str, error_type: Optional[str] = None) -> float:
        """
        Calculate adjusted confidence based on signal quality and error state.
        
        Args:
            action: The action or signal (BUY, SELL, HOLD, NEUTRAL, UNKNOWN)
            confidence: The raw confidence value 
            status: The status of the analysis ("success", "error", etc.)
            error_type: Type of error if status is "error"
            
        Returns:
            Adjusted confidence value (0-100)
        """
        # Start with the provided confidence
        adjusted_confidence = confidence
        
        # If action is UNKNOWN, confidence should be very low
        if action == "UNKNOWN":
            adjusted_confidence = min(adjusted_confidence, 10)  # Cap at 10% for UNKNOWN signals
            
        # If this is an error response, reduce confidence based on error type
        if status == "error":
            if error_type == "INSUFFICIENT_DATA":
                # Insufficient data is common, keep some confidence but reduce it
                adjusted_confidence = min(adjusted_confidence, 30)
            elif error_type == "DATA_FETCHER_MISSING":
                # Configuration issue, very low confidence
                adjusted_confidence = 0
            elif error_type == "API_ERROR" or error_type == "API_KEY_ERROR":
                # API errors might be temporary, keep minimal confidence
                adjusted_confidence = min(adjusted_confidence, 10)
            else:
                # General errors get very low confidence
                adjusted_confidence = min(adjusted_confidence, 5)
                
        # For HOLD/NEUTRAL actions with low confidence, ensure a baseline level
        if (action in ["HOLD", "NEUTRAL"]) and adjusted_confidence < 30 and status == "success":
            # Provide a baseline confidence for non-directional signals
            # to prevent being completely ignored in the weighted average,
            # but not so high as to dilute directional signals
            adjusted_confidence = max(adjusted_confidence, 30)
            
        # For BUY/SELL actions, ensure they have a reasonable confidence level
        # to be considered in the directional decision
        if action in ["BUY", "SELL"] and adjusted_confidence < 15 and status == "success":
            # Very low confidence directional signals should be slightly boosted
            # to ensure they're not completely ignored in directional calculations
            adjusted_confidence = max(adjusted_confidence, 15)
            
        # Ensure the final confidence is in the valid range
        return max(0, min(100, adjusted_confidence))
    
    def _make_weighted_decision(self, 
                              agent_analyses: Dict[str, Any], 
                              symbol: str,
                              agent_weights: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Make a decision using weighted confidence scores from multiple agents.
        
        Args:
            agent_analyses: Dictionary containing analyses from all agents
            symbol: Trading symbol
            agent_weights: Dictionary of agent weights
            
        Returns:
            Dictionary with trading decision or None if weighted decision couldn't be made
        """
        self.logger.info("Attempting weighted decision from multiple analyses")
        
        try:
            # Group agent outputs by signal type
            votes_by_signal = {
                "BUY": [],  # Will contain tuples of (agent_name, confidence, weight)
                "SELL": [],
                "HOLD": [],
                "NEUTRAL": []
            }
            
            # Track agent contributions
            agent_contributions = {}
            
            # Track weights used
            weights_used = {}
            
            # Track agents with insufficient data
            insufficient_data_agents = []
            
            # Process each agent's analysis
            for analysis_key, analysis_data in agent_analyses.items():
                agent_name = self._get_agent_name_from_analysis_key(analysis_key)
                
                # Get agent's weight (default to 1.0 if not specified)
                agent_weight = agent_weights.get(agent_name, 1.0)
                if agent_name not in agent_weights:
                    self.logger.warning(f"No weight configured for {agent_name}, using default weight of 1.0")
                
                # Extract the agent's action and confidence
                action = None
                confidence = 0
                status = "success"
                error_type = None
                
                # Check for error status
                if isinstance(analysis_data, dict):
                    status = analysis_data.get("status", "success")
                    if status == "error":
                        error_type = analysis_data.get("error_type")
                        # If it's an insufficient data error, track it specially
                        if error_type == "INSUFFICIENT_DATA":
                            insufficient_data_agents.append(agent_name)
                
                # Different agents may have different output formats
                if "recommendation" in analysis_data:
                    action = analysis_data["recommendation"].get("action")
                    confidence = analysis_data["recommendation"].get("confidence", 50)
                elif "decision" in analysis_data:
                    action = analysis_data["decision"].get("action")
                    confidence = analysis_data["decision"].get("confidence", 50)
                elif "action" in analysis_data:
                    action = analysis_data.get("action")
                    confidence = analysis_data.get("confidence", 50)
                elif "analysis" in analysis_data:
                    # Handle sentiment analysis format
                    action = analysis_data["analysis"].get("action")
                    confidence = analysis_data["analysis"].get("confidence", 50)
                elif "signal" in analysis_data:
                    # Handle signal from analyst agents
                    signal = analysis_data.get("signal")
                    # Map signals to actions
                    if signal == "BUY":
                        action = "BUY"
                    elif signal == "SELL":
                        action = "SELL"
                    elif signal == "NEUTRAL":
                        action = "NEUTRAL"
                    elif signal in ["HOLD", "UNKNOWN"]:
                        # Map HOLD and UNKNOWN to HOLD action but with different confidence
                        action = "HOLD"
                        if signal == "UNKNOWN" and confidence > 30:
                            # UNKNOWN signals should have lower confidence
                            confidence = 30
                    confidence = analysis_data.get("confidence", 50)
                
                # If the action is missing but we have error status, use HOLD
                if not action and status == "error":
                    action = "HOLD"  # Default to HOLD for error cases
                
                # Skip if we couldn't extract a valid action
                if not action or action not in votes_by_signal:
                    self.logger.warning(f"Couldn't extract valid action from {agent_name} analysis, skipping")
                    continue
                
                # Calculate adjusted confidence based on action and status
                adjusted_confidence = self._calculate_confidence(action, confidence, status, error_type)
                
                # Calculate weighted confidence
                weighted_confidence = adjusted_confidence * agent_weight
                
                # Group the vote by signal type
                votes_by_signal[action].append((agent_name, adjusted_confidence, agent_weight, weighted_confidence))
                
                # Track agent contribution
                agent_contributions[agent_name] = {
                    "action": action,
                    "confidence": adjusted_confidence,
                    "raw_confidence": confidence,  # Store original confidence for reference
                    "status": status,
                    "weight": agent_weight,
                    "weighted_confidence": weighted_confidence
                }
                
                # Track weights used
                weights_used[agent_name] = agent_weight
                
                self.logger.info(f"{agent_name}: {action} with confidence {adjusted_confidence}, weight {agent_weight}, weighted score {weighted_confidence}")
            
            # If we don't have enough data, return None to fall back to other methods
            if not agent_contributions:
                self.logger.warning("Not enough valid agent inputs for weighted decision")
                return None
            
            # Compute total weighted confidence by signal
            total_confidence = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0, "NEUTRAL": 0.0}
            signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "NEUTRAL": 0}
            total_directional_weight = 0.0
            
            for signal, votes in votes_by_signal.items():
                for _, _, weight, weighted_conf in votes:
                    total_confidence[signal] += weighted_conf
                    signal_counts[signal] += 1
                    
                    # Track total directional weights (BUY/SELL only)
                    if signal in ["BUY", "SELL"]:
                        total_directional_weight += weight
            
            # Get signal with highest weighted confidence
            dominant_signal = max(total_confidence.items(), key=lambda x: x[1])
            final_signal = dominant_signal[0]
            weighted_score = dominant_signal[1]
            
            # Log the breakdown by signal type
            self.logger.info(f"Signal breakdown:")
            for signal, votes in votes_by_signal.items():
                if votes:
                    avg_confidence = sum(conf for _, conf, _, _ in votes) / len(votes)
                    self.logger.info(f"  {signal}: {len(votes)} agents (avg {avg_confidence:.1f}%, weighted score: {total_confidence[signal]:.1f})")
                else:
                    self.logger.info(f"  {signal}: 0 agents")
            
            # Check for conflicting signals with high confidence
            high_confidence_signals = {action: [] for action in ["BUY", "SELL"]}
            has_conflict = False
            
            for signal in ["BUY", "SELL"]:
                for agent_name, confidence, _, _ in votes_by_signal[signal]:
                    if confidence >= self.high_confidence_threshold:
                        high_confidence_signals[signal].append((agent_name, confidence))
            
            # Check if we have high confidence signals in opposing directions
            has_buy_signals = len(high_confidence_signals["BUY"]) > 0
            has_sell_signals = len(high_confidence_signals["SELL"]) > 0
            conflict_reason = ""
            
            if has_buy_signals and has_sell_signals:
                has_conflict = True
                # Generate conflict reason with details
                conflict_parts = []
                
                for signal, agents in high_confidence_signals.items():
                    if agents:
                        agent_details = ", ".join([f"{name} ({conf:.0f}%)" for name, conf in agents])
                        conflict_parts.append(f"{signal}: {agent_details}")
                
                conflict_reason = f"Conflicting high-confidence signals: {'; '.join(conflict_parts)}"
                self.logger.warning(conflict_reason)
            
            # Calculate different confidence metrics
            # 1. Directional confidence - only for BUY/SELL signals
            directional_confidence = 0
            if final_signal in ["BUY", "SELL"] and total_directional_weight > 0:
                # Calculate the directional confidence (considers only BUY/SELL signals)
                total_directional_confidence = total_confidence["BUY"] + total_confidence["SELL"]
                
                if total_directional_confidence > 0:
                    # Use the proportion of this signal's confidence to the total directional confidence
                    directional_confidence = (total_confidence[final_signal] / total_directional_confidence) * 100
                else:
                    # If no directional confidence, use the confidence relative to weight
                    directional_confidence = (total_confidence[final_signal] / total_directional_weight) * 100
                    
                # Cap the directional confidence at 100%
                directional_confidence = min(directional_confidence, 100)
            
            # 2. Overall normalized confidence (percentage of total weighted confidence)
            total_weighted_confidence = sum(total_confidence.values())
            normalized_confidence = 0
            if total_weighted_confidence > 0:
                normalized_confidence = (weighted_score / total_weighted_confidence) * 100
                # Cap the normalized confidence at 100%
                normalized_confidence = min(normalized_confidence, 100)
            
            # Use directional confidence for BUY/SELL signals; otherwise use normalized
            final_confidence = directional_confidence if final_signal in ["BUY", "SELL"] else normalized_confidence
            
            # Calculate conflict score between top two signals
            conflict_score = 0
            if sum(signal_counts.values()) >= 2:
                # Sort signals by weighted confidence (descending)
                sorted_signals = sorted(total_confidence.items(), key=lambda x: x[1], reverse=True)
                if len(sorted_signals) >= 2 and sorted_signals[1][1] > 0:
                    top_score = sorted_signals[0][1]
                    second_score = sorted_signals[1][1]
                    
                    if total_weighted_confidence > 0:
                        conflict_score = (top_score - second_score) / total_weighted_confidence * 100
                    
                    # Invert the conflict score so higher means more conflict
                    conflict_score = 100 - conflict_score
            
            # Handle action determination with conflict state
            if has_conflict and self.allow_conflict_state:
                # Use CONFLICTED state when there are strong opposing signals
                action = "CONFLICTED"  # For tests, use CONFLICTED action
                final_signal = "CONFLICTED"  # Also set final_signal for new consumers
                reason = conflict_reason
                final_confidence = max(80, normalized_confidence)  # Set higher confidence for conflict state
                self.logger.warning(f"⚠️ CONFLICTED decision due to high-confidence opposing signals")
                self.logger.info(f"CONFLICT DETECTED: Decision set to CONFLICTED, confidence {final_confidence}")
                
                # Create agent scores for conflict logging
                agent_scores = {}
                for agent_name, contribution in agent_contributions.items():
                    agent_scores[agent_name] = {
                        "signal": contribution["action"],
                        "confidence": contribution["confidence"],
                        "weight": contribution["weight"]
                    }
                
                # Log the conflict for analysis using the conflict logger
                try:
                    # Use proper symbol formatting for display
                    display_symbol = symbol.replace('/', '') if '/' in symbol else symbol
                    
                    # Ensure we have a valid interval
                    local_interval = getattr(self, 'interval', self.default_interval)
                    
                    # Non-blocking conflict logging
                    log_conflict(
                        symbol=display_symbol,
                        interval=local_interval,
                        final_signal=final_signal,
                        confidence=final_confidence,
                        reasoning=reason,
                        agent_scores=agent_scores,
                        metadata={
                            "conflict_score": conflict_score,
                            "high_confidence_signals": high_confidence_signals,
                            "normalized_confidence": normalized_confidence,
                            "directional_confidence": directional_confidence,
                            "signal_counts": signal_counts,
                            "total_confidence": {k: float(v) for k, v in total_confidence.items()}
                        }
                    )
                    self.logger.info(f"Logged CONFLICTED decision for analysis")
                except Exception as e:
                    # Non-blocking, so just log the error and continue
                    self.logger.error(f"Error logging conflict: {str(e)}")
                
                # No need to apply confidence threshold, as conflict is a high-confidence state
            # Apply confidence threshold for directional signals
            elif final_signal in ["BUY", "SELL"] and final_confidence < self.confidence_threshold:
                original_signal = final_signal
                original_confidence = final_confidence
                action = "HOLD"  # Action is HOLD when below threshold
                final_signal = "HOLD"  # Final signal is also HOLD
                reason = f"Confidence below threshold ({original_confidence:.2f}% < {self.confidence_threshold}%)"
                final_confidence = min(final_confidence, 65)  # Cap confidence for forced HOLD
                self.logger.info(f"Signal {original_signal} was converted to HOLD due to low confidence ({original_confidence:.2f}%)")
            else:
                # Set action same as final signal
                action = final_signal
                
                # Convert NEUTRAL to HOLD for final action and final signal
                if action == "NEUTRAL":
                    action = "HOLD"
                    final_signal = "HOLD"  # Also update final_signal for consistency
                    self.logger.info(f"Converting NEUTRAL to HOLD for final action and final signal")
                
                # Create reason based on agent contributions
                reason_parts = []
                for agent_name, contribution in agent_contributions.items():
                    agent_action = contribution["action"]
                    if agent_action == final_signal or (final_signal == "HOLD" and agent_action == "NEUTRAL"):
                        reason_parts.append(f"{agent_name} recommends {agent_action}")
                
                if reason_parts:
                    reason = ", ".join(reason_parts)
                else:
                    reason = f"Weighted analysis suggests {action} is the best course of action"
                
                # Add information about insufficient data if relevant
                if insufficient_data_agents:
                    data_warning = f"Note: Insufficient data from {', '.join(insufficient_data_agents)}"
                    reason = f"{reason}. {data_warning}"
                
                # Add conflict information if relevant but not handling as CONFLICTED state
                if has_conflict and not self.allow_conflict_state:
                    conflict_warning = f"Note: Conflicting signals detected, but {action} has predominant consensus"
                    reason = f"{reason}. {conflict_warning}"
            
            # Prepare summary of contributing agents to the chosen signal
            contributing_agents = []
            if final_signal != "CONFLICTED":
                for signal in ["BUY", "SELL", "HOLD", "NEUTRAL"]:
                    if signal == final_signal or (final_signal == "HOLD" and signal == "NEUTRAL"):
                        contributing_agents.extend([agent for agent, _, _, _ in votes_by_signal[signal]])
            
            # Create action scores map for backward compatibility
            action_scores = {
                "BUY": total_confidence["BUY"],
                "SELL": total_confidence["SELL"],
                "HOLD": total_confidence["HOLD"] + total_confidence["NEUTRAL"]  # Combine HOLD and NEUTRAL
            }
            
            # Create decision object
            decision = {
                "action": action,
                "final_signal": final_signal,
                "pair": symbol,
                "confidence": final_confidence,
                "reasoning": reason,  # Primary reason field used by external systems
                "reason": reason,     # Keep for backward compatibility
                "agent_contributions": agent_contributions,
                "action_scores": action_scores,
                "weights_used": weights_used,
                "decision_method": "weighted_directional",  # Updated method name
                "insufficient_data_agents": insufficient_data_agents if insufficient_data_agents else [],
                # Add new confidence metrics
                "final_signal_confidence": final_confidence,
                "directional_confidence": directional_confidence,
                "normalized_confidence": normalized_confidence,
                "conflict_score": conflict_score,
                "has_conflict": has_conflict,
                "signal_counts": signal_counts,
                "contributing_agents": contributing_agents
            }
            
            # Log the final decision with more details
            self.logger.info(f"Final signal: {final_signal}, confidence: {final_confidence:.1f}%, directional confidence: {directional_confidence:.1f}%")
            if contributing_agents:
                self.logger.info(f"Contributing agents: {', '.join(contributing_agents)}")
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error making weighted decision: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def _make_liquidity_based_decision(self, 
                                     liquidity_analysis: Dict[str, Any], 
                                     symbol: str) -> Dict[str, Any]:
        """
        Make a decision based only on liquidity analysis.
        
        Args:
            liquidity_analysis: Liquidity analysis results
            symbol: Trading symbol
            
        Returns:
            Dictionary with trading decision
        """
        self.logger.info("Making liquidity-based decision")
        
        # Default decision (conservative)
        decision = {
            "action": "HOLD",
            "pair": symbol,
            "confidence": 50,
            "reason": "Neutral liquidity conditions",
            "agent_contributions": {
                "LiquidityAnalystAgent": {
                    "action": "HOLD",
                    "confidence": 50,
                    "weight": self.agent_weights.get("LiquidityAnalystAgent", 1.0),
                    "weighted_confidence": 50 * self.agent_weights.get("LiquidityAnalystAgent", 1.0)
                }
            },
            "decision_method": "liquidity_based"
        }
        
        try:
            # Extract LLM analysis if available
            llm_analysis = liquidity_analysis.get("llm_analysis", {})
            
            if "analysis" in llm_analysis:
                analysis = llm_analysis["analysis"]
                
                # Extract liquidity score
                liquidity_score = analysis.get("liquidity_score", 50)
                
                # Extract overall liquidity assessment
                overall_liquidity = analysis.get("overall_liquidity", "medium")
                
                # Extract bid/ask imbalance
                bid_ask_imbalance = analysis.get("bid_ask_imbalance", "balanced")
                
                # Decision logic based on liquidity factors
                # Determine the action based on liquidity factors
                action = "HOLD"
                confidence = min(liquidity_score, 65)  # Default capped confidence
                reason = llm_analysis.get("interpretation", "Current liquidity conditions do not signal a clear direction")
                
                if overall_liquidity == "high" and bid_ask_imbalance == "bid-heavy" and liquidity_score > self.confidence_threshold:
                    action = "BUY"
                    confidence = liquidity_score
                    reason = llm_analysis.get("interpretation", "Strong buy-side liquidity detected")
                elif overall_liquidity == "high" and bid_ask_imbalance == "ask-heavy" and liquidity_score > self.confidence_threshold:
                    action = "SELL"
                    confidence = liquidity_score
                    reason = llm_analysis.get("interpretation", "Strong sell-side liquidity detected")
                
                # Update agent contributions
                agent_weight = self.agent_weights.get("LiquidityAnalystAgent", 1.0)
                agent_contributions = {
                    "LiquidityAnalystAgent": {
                        "action": action,
                        "confidence": confidence,
                        "weight": agent_weight,
                        "weighted_confidence": confidence * agent_weight
                    }
                }
                
                # Create decision
                decision = {
                    "action": action,
                    "final_signal": action,  # Explicitly set final_signal to match action
                    "pair": symbol,
                    "confidence": confidence,
                    "reasoning": reason,  # Add reasoning field for consistency 
                    "reason": reason,     # Keep original reason field for backward compatibility
                    "agent_contributions": agent_contributions,
                    "decision_method": "liquidity_based"
                }
            
            # If LLM analysis not available, use rule-based analysis
            else:
                rule_analysis = liquidity_analysis.get("rule_analysis", {})
                indicators = rule_analysis.get("liquidity_indicators", {})
                
                # Determine the action based on indicators
                action = "HOLD"
                confidence = 60
                reason = "Market liquidity conditions are neutral or mixed"
                
                if indicators.get("bid_ask_imbalance") == "bid-heavy" and indicators.get("overall_depth") == "high":
                    action = "BUY"
                    confidence = 75
                    reason = "Strong buying pressure and high market depth"
                elif indicators.get("bid_ask_imbalance") == "ask-heavy" and indicators.get("overall_depth") == "high":
                    action = "SELL"
                    confidence = 75
                    reason = "Strong selling pressure and high market depth"
                
                # Update agent contributions
                agent_weight = self.agent_weights.get("LiquidityAnalystAgent", 1.0)
                agent_contributions = {
                    "LiquidityAnalystAgent": {
                        "action": action,
                        "confidence": confidence,
                        "weight": agent_weight,
                        "weighted_confidence": confidence * agent_weight
                    }
                }
                
                # Create decision
                decision = {
                    "action": action,
                    "final_signal": action,  # Explicitly set final_signal to match action
                    "pair": symbol,
                    "confidence": confidence,
                    "reasoning": reason,  # Add reasoning field for consistency
                    "reason": reason,     # Keep original reason field for backward compatibility
                    "agent_contributions": agent_contributions,
                    "decision_method": "rule_based"
                }
        
        except Exception as e:
            self.logger.error(f"Error making liquidity-based decision: {e}")
            agent_weight = self.agent_weights.get("LiquidityAnalystAgent", 1.0)
            confidence = 30
            decision = {
                "action": "HOLD",
                "final_signal": "HOLD",
                "pair": symbol,
                "confidence": confidence,
                "reasoning": f"Error analyzing liquidity data: {str(e)}",
                "reason": f"Error analyzing liquidity data: {str(e)}",
                "agent_contributions": {
                    "LiquidityAnalystAgent": {
                        "action": "HOLD",
                        "confidence": confidence,
                        "weight": agent_weight,
                        "weighted_confidence": confidence * agent_weight
                    }
                },
                "decision_method": "error_fallback"
            }
        
        return decision
    
    def _create_safe_decision(
        self,
        action: str = "HOLD",
        pair: str = "UNKNOWN",
        confidence: float = 0.0,
        reason: str = "Default safe decision",
        error: bool = False,
        error_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a safe decision with default values.
        
        Args:
            action: Trading action (default HOLD)
            pair: Trading pair
            confidence: Confidence level (0-100)
            reason: Reason for the decision
            error: Whether this is an error response
            error_type: Type of error if any
            
        Returns:
            Standardized decision dictionary
        """
        # Ensure action is valid
        valid_actions = ["BUY", "SELL", "HOLD", "CONFLICTED"]
        if action not in valid_actions:
            self.logger.warning(f"Invalid action '{action}', defaulting to HOLD")
            action = "HOLD"
            
        # Ensure confidence is in valid range
        if not isinstance(confidence, (int, float)):
            confidence = 0
        confidence = max(0, min(100, confidence))
        
        # Build decision object
        decision = {
            "action": action,
            "final_signal": action,  # Explicitly set final_signal to match action
            "pair": pair,
            "confidence": confidence,
            "reasoning": reason,  # Add reasoning field for consistency
            "reason": reason,     # Keep original reason field for backward compatibility
            "timestamp": datetime.now().isoformat(),
            "agent_contributions": {},
            "decision_method": "fallback" if error else "simple"
        }
        
        # Add error information if this is an error response
        if error:
            decision["error"] = True
            if error_type:
                decision["error_type"] = error_type
        
        return decision
    
    def _handle_decision_error(
        self,
        error: Exception,
        symbol: str,
        error_type: str = "General Error"
    ) -> Dict[str, Any]:
        """
        Handle errors in the decision making process.
        
        Args:
            error: The exception that occurred
            symbol: Trading symbol
            error_type: Type of error for categorization
            
        Returns:
            Safe decision dictionary with error information
        """
        error_msg = str(error)
        self.logger.error(f"{error_type} in decision making: {error_msg}")
        
        # Return safe HOLD decision with error details
        return self._create_safe_decision(
            action="HOLD",
            pair=symbol,
            confidence=0,
            reason=f"Decision error: {error_msg}",
            error=True,
            error_type=error_type
        )
    
    @handle_llm_errors
    def _make_llm_decision(self, 
                         agent_analyses: Dict[str, Any], 
                         symbol: str) -> Dict[str, Any]:
        """
        Make a decision using LLM to synthesize multiple analyses.
        
        Args:
            agent_analyses: Dictionary containing analyses from all agents
            symbol: Trading symbol
            
        Returns:
            Dictionary with trading decision
        """
        self.logger.info("Making LLM-based decision from multiple analyses")
        
        # Prepare agent contributions
        agent_contributions = {}
        for analysis_key in agent_analyses.keys():
            agent_name = self._get_agent_name_from_analysis_key(analysis_key)
            agent_weight = self.agent_weights.get(agent_name, 1.0)
            if agent_name not in self.agent_weights:
                self.logger.warning(f"No weight configured for {agent_name}, using default weight of 1.0")
            
            agent_contributions[agent_name] = {
                "action": "UNKNOWN",  # Will be filled in by LLM
                "confidence": 50,     # Default
                "weight": agent_weight,
                "weighted_confidence": 50 * agent_weight
            }
        
        # Default decision (conservative)
        decision = {
            "action": "HOLD",
            "final_signal": "HOLD",
            "pair": symbol,
            "confidence": 50,
            "reasoning": "Waiting for clearer signals",
            "reason": "Waiting for clearer signals",
            "agent_contributions": agent_contributions,
            "decision_method": "llm_based"
        }
        
        try:
            # Prepare prompt for LLM
            prompt = f"""
            As a trading decision agent, analyze the following inputs from specialized agents:
            
            {json.dumps(agent_analyses, indent=2)}
            
            Based on this analysis, make a trading decision for {symbol} with one of these actions: BUY, SELL, or HOLD.
            
            Assign a confidence score (0-100) to your decision, considering:
            - The quality and consistency of the data
            - Agreement or disagreement between different analyses
            - Strength of the signals
            
            Format your response as a JSON object with the following structure:
            {{
                "action": "[BUY/SELL/HOLD]",
                "pair": "{symbol}",
                "confidence": [0-100],
                "reason": "[concise explanation of decision]"
            }}
            
            Only return a valid JSON object, nothing else.
            """
            
            # Get decision from LLM
            response = self.llm_client.generate(prompt)
            
            # Parse response
            try:
                # Try to extract JSON if response contains other text
                if "{" in response and "}" in response:
                    import re
                    json_match = re.search(r'({.*})', response.replace('\n', ' '), re.DOTALL)
                    if json_match:
                        response = json_match.group(1)
                
                llm_decision = json.loads(response)
                
                # Validate decision
                if "action" in llm_decision and "confidence" in llm_decision and "reason" in llm_decision:
                    # Normalize action to uppercase
                    llm_decision["action"] = llm_decision["action"].upper()
                    
                    # Ensure action is valid
                    if llm_decision["action"] not in ["BUY", "SELL", "HOLD"]:
                        llm_decision["action"] = "HOLD"
                        llm_decision["reason"] = "Invalid action detected, defaulting to HOLD. " + llm_decision.get("reason", "")
                    
                    # Ensure confidence is in range
                    if not isinstance(llm_decision["confidence"], (int, float)):
                        llm_decision["confidence"] = 50
                    else:
                        llm_decision["confidence"] = max(0, min(100, llm_decision["confidence"]))
                    
                    # Apply confidence threshold for actions
                    if llm_decision["action"] in ["BUY", "SELL"] and llm_decision["confidence"] < self.confidence_threshold:
                        llm_decision["action"] = "HOLD"
                        llm_decision["reason"] = f"Confidence below threshold ({llm_decision['confidence']} < {self.confidence_threshold}). " + llm_decision.get("reason", "")
                        llm_decision["confidence"] = min(llm_decision["confidence"], 65)  # Cap confidence for forced HOLD
                    
                    # Preserve agent contributions but update with LLM decision
                    agent_contributions_backup = decision.get("agent_contributions", {})
                    decision_method = decision.get("decision_method", "llm_based")
                    
                    # Create new decision with all required fields
                    action = llm_decision.get("action", "HOLD").upper()
                    reason = llm_decision.get("reason", "LLM decision")
                    confidence = llm_decision.get("confidence", 50)
                    
                    decision = {
                        "action": action,
                        "final_signal": action,  # Explicitly set final_signal to match action
                        "pair": symbol,
                        "confidence": confidence,
                        "reasoning": reason,  # Primary reason field
                        "reason": reason,     # Original reason field for backward compatibility
                        "agent_contributions": agent_contributions_backup,
                        "decision_method": decision_method
                    }
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response as JSON: {e}")
                # Keep existing agent contributions
                agent_contributions_backup = decision.get("agent_contributions", {})
                confidence = 30
                decision = {
                    "action": "HOLD",
                    "final_signal": "HOLD",
                    "pair": symbol,
                    "confidence": confidence,
                    "reasoning": "Error parsing decision data",
                    "reason": "Error parsing decision data",
                    "agent_contributions": agent_contributions_backup,
                    "decision_method": "error_fallback"
                }
        
        except Exception as e:
            self.logger.error(f"Error making LLM-based decision: {e}")
            # Keep existing agent contributions
            agent_contributions_backup = decision.get("agent_contributions", {})
            confidence = 30
            decision = {
                "action": "HOLD",
                "final_signal": "HOLD",
                "pair": symbol,
                "confidence": confidence,
                "reasoning": f"Error synthesizing analyses: {str(e)}",
                "reason": f"Error synthesizing analyses: {str(e)}",
                "agent_contributions": agent_contributions_backup,
                "decision_method": "error_fallback"
            }
        
        return decision
    
    def log_decision(self, decision: Dict[str, Any]) -> None:
        """
        Log a trading decision.
        
        Args:
            decision: Trading decision dictionary
        """
        action = decision.get('action', 'UNKNOWN')
        final_signal = decision.get('final_signal', action)
        confidence = decision.get('confidence', 0)
        reason = decision.get('reasoning') or decision.get('reason', 'No reason provided')
        
        # Include final_signal in log if it differs from action
        if final_signal != action:
            self.logger.info(f"Decision: {action} (Signal: {final_signal}) {decision.get('pair', 'UNKNOWN')} (Confidence: {confidence})")
        else:
            self.logger.info(f"Decision: {action} {decision.get('pair', 'UNKNOWN')} (Confidence: {confidence})")
            
        # Special handling for CONFLICTED state
        if final_signal == "CONFLICTED":
            self.logger.warning(f"⚠️ CONFLICTED decision: {reason}")
        else:
            self.logger.info(f"Reason: {reason}")
        
        # Log conflict metrics if available
        if decision.get('has_conflict', False):
            self.logger.info(f"Conflict Score: {decision.get('conflict_score', 'N/A')}")
            
        # TODO: Log to database or file for record-keeping
        # This would be implemented in future versions

# Example usage (for demonstration)
if __name__ == "__main__":
    # Create agent
    agent = DecisionAgent()
    
    # Example liquidity analysis
    liquidity_analysis = {
        "llm_analysis": {
            "analysis": {
                "overall_liquidity": "high",
                "bid_ask_imbalance": "bid-heavy",
                "volume_profile": "above average",
                "depth_analysis": "Large buy walls observed at key support levels",
                "funding_rate_impact": "neutral to slightly positive",
                "liquidity_score": 87
            },
            "interpretation": "Market shows strong liquidity with buy-side dominance. Volume concentration at key price levels suggests institutional interest.",
            "recommendation": "Current liquidity conditions are favorable for buying with minimal slippage."
        }
    }
    
    # Make decision
    decision = agent.make_decision({"liquidity_analysis": liquidity_analysis}, "BTC/USDT")
    
    # Log decision
    agent.log_decision(decision)
    
    # Print result
    print(json.dumps(decision, indent=2))
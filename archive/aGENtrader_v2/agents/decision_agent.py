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
try:
    from utils.error_handler import (
        ValidationError as BaseValidationError,
        DataFetchingError as BaseDataFetchingError,
        retry_with_backoff as base_retry_with_backoff,
        handle_api_errors as base_handle_api_errors,
        check_api_keys as base_check_api_keys,
        request_api_key as base_request_api_key
    )
    
    # Alias imported error classes to avoid name conflicts
    ValidationError = BaseValidationError
    DataFetchingError = BaseDataFetchingError
    retry_with_backoff = base_retry_with_backoff
    handle_api_errors = base_handle_api_errors
    check_api_keys = base_check_api_keys
    request_api_key = base_request_api_key
    
except ImportError:
    # Define local error classes if imports fail (fallback)
    class ValidationError(Exception): pass
    class DataFetchingError(Exception): pass
    
    # Define local decorators
    def retry_with_backoff(*args, **kwargs): 
        def decorator(func): return func
        return decorator
        
    def handle_api_errors(func): return func
    
    # Define local utility functions
    def check_api_keys(*args, **kwargs): return False
    def request_api_key(*args, **kwargs): pass

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
    
    def __init__(self):
        """Initialize the Decision Agent."""
        self.logger = logging.getLogger("decision_agent")
        
        # Load configuration
        self.config = load_config()
        self.agent_config = self.config.get("agents", {}).get("decision", {})
        self.trading_config = self.config.get("trading", {})
        
        # Load agent weights
        self.agent_weights = self.config.get("agent_weights", {})
        self.logger.info(f"Loaded agent weights: {self.agent_weights}")
        
        # Initialize LLM client
        self.llm_client = LLMClient()
        
        # Set default parameters
        self.default_symbol = self.trading_config.get("default_pair", "BTC/USDT")
        self.default_interval = self.trading_config.get("default_interval", "1h")
        self.confidence_threshold = self.agent_config.get("confidence_threshold", 70)
        
        self.logger.info(f"Decision Agent initialized with confidence threshold={self.confidence_threshold}")
    
    def make_decision(self, 
                     agent_analyses: Dict[str, Any], 
                     symbol: Optional[str] = None,
                     interval: Optional[str] = None,
                     agent_weights_override: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Make a trading decision based on agent analyses.
        
        Args:
            agent_analyses: Dictionary containing analyses from specialized agents
            symbol: Trading symbol (default from config)
            interval: Time interval (default from config)
            agent_weights_override: Optional dictionary to override default agent weights
            
        Returns:
            Dictionary with trading decision
        """
        try:
            # Validate inputs
            if not isinstance(agent_analyses, dict):
                raise ValidationError(f"agent_analyses must be a dictionary, got {type(agent_analyses)}")
                
            symbol = symbol or self.default_symbol
            interval = interval or self.default_interval
            
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
            "fundamental_analysis": "FundamentalAnalystAgent"
        }
        
        return agent_name_map.get(analysis_key, analysis_key)
        
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
            # Initialize action confidence scores
            action_scores = {
                "BUY": 0.0,
                "SELL": 0.0,
                "HOLD": 0.0
            }
            
            # Track agent contributions
            agent_contributions = {}
            
            # Track weights used
            total_weight = 0.0
            weights_used = {}
            
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
                    
                # Skip if we couldn't extract a valid action
                if not action or action not in action_scores:
                    self.logger.warning(f"Couldn't extract valid action from {agent_name} analysis, skipping")
                    continue
                
                # Normalize confidence to 0-100 range
                if not isinstance(confidence, (int, float)):
                    confidence = 50
                confidence = max(0, min(100, confidence))
                
                # Calculate weighted confidence
                weighted_confidence = confidence * agent_weight
                
                # Add to action scores
                action_scores[action] += weighted_confidence
                
                # Track agent contribution
                agent_contributions[agent_name] = {
                    "action": action,
                    "confidence": confidence,
                    "weight": agent_weight,
                    "weighted_confidence": weighted_confidence
                }
                
                # Update total weight
                total_weight += agent_weight
                weights_used[agent_name] = agent_weight
                
                self.logger.info(f"{agent_name}: {action} with confidence {confidence}, weight {agent_weight}, weighted score {weighted_confidence}")
            
            # If we don't have enough data, return None to fall back to other methods
            if not agent_contributions or total_weight == 0:
                self.logger.warning("Not enough valid agent inputs for weighted decision")
                return None
            
            # Determine the highest scoring action
            chosen_action = max(action_scores.items(), key=lambda x: x[1])
            action = chosen_action[0]
            weighted_score = chosen_action[1]
            
            # Calculate normalized confidence (as percentage of total weighted confidence)
            total_weighted_confidence = sum(action_scores.values())
            normalized_confidence = 0
            if total_weighted_confidence > 0:
                normalized_confidence = (weighted_score / total_weighted_confidence) * 100
            
            # Calculate final confidence as percentage of max possible confidence
            final_confidence = (weighted_score / total_weight) if total_weight > 0 else 0
            
            # Apply confidence threshold for actions
            if action in ["BUY", "SELL"] and final_confidence < self.confidence_threshold:
                original_action = action
                original_confidence = final_confidence
                action = "HOLD"
                reason = f"Confidence below threshold ({original_confidence:.2f} < {self.confidence_threshold})"
                final_confidence = min(final_confidence, 65)  # Cap confidence for forced HOLD
            else:
                # Create reason based on agent contributions
                reason_parts = []
                for agent_name, contribution in agent_contributions.items():
                    if contribution["action"] == action:
                        reason_parts.append(f"{agent_name} recommends {action}")
                
                if reason_parts:
                    reason = ", ".join(reason_parts)
                else:
                    reason = f"Weighted analysis suggests {action} is the best course of action"
            
            # Create decision object
            decision = {
                "action": action,
                "pair": symbol,
                "confidence": final_confidence,
                "reason": reason,
                "agent_contributions": agent_contributions,
                "action_scores": action_scores,
                "weights_used": weights_used,
                "decision_method": "weighted"
            }
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error making weighted decision: {e}")
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
                    "pair": symbol,
                    "confidence": confidence,
                    "reason": reason,
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
                    "pair": symbol,
                    "confidence": confidence,
                    "reason": reason,
                    "agent_contributions": agent_contributions,
                    "decision_method": "rule_based"
                }
        
        except Exception as e:
            self.logger.error(f"Error making liquidity-based decision: {e}")
            agent_weight = self.agent_weights.get("LiquidityAnalystAgent", 1.0)
            confidence = 30
            decision = {
                "action": "HOLD",
                "pair": symbol,
                "confidence": confidence,
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
        valid_actions = ["BUY", "SELL", "HOLD"]
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
            "pair": pair,
            "confidence": confidence,
            "reason": reason,
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
            "pair": symbol,
            "confidence": 50,
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
                    
                    decision = llm_decision
                    decision["pair"] = symbol  # Ensure correct symbol
                    decision["agent_contributions"] = agent_contributions_backup
                    decision["decision_method"] = decision_method
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response as JSON: {e}")
                # Keep existing agent contributions
                agent_contributions_backup = decision.get("agent_contributions", {})
                confidence = 30
                decision = {
                    "action": "HOLD",
                    "pair": symbol,
                    "confidence": confidence,
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
                "pair": symbol,
                "confidence": confidence,
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
        self.logger.info(f"Decision: {decision['action']} {decision['pair']} (Confidence: {decision['confidence']})")
        self.logger.info(f"Reason: {decision['reason']}")
        
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
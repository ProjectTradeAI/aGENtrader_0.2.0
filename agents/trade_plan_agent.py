"""
aGENtrader v2 Trade Plan Agent

This module provides a trading plan generation agent that extends the base decision agent
to create detailed trade plans including entry, stop-loss, take-profit levels, and position sizing.

The TradePlanAgent generates comprehensive trade plans with enhanced features:
- Explainability summaries
- Volatility-aware entry, stop-loss and take-profit levels
- Time-based validity periods
- Trade type classification
- Risk assessment metrics
- Fallback handling for less precise calculations
"""

import os
import logging
import time
import json
import math
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum

from agents.base_agent import BaseAgent
from agents.base_decision_agent import BaseDecisionAgent

# Configure logging
logger = logging.getLogger(__name__)

def create_trade_plan_agent(config: Optional[Dict[str, Any]] = None, **kwargs) -> 'TradePlanAgent':
    """
    Create a TradePlanAgent with the specified configuration.
    
    This factory function creates a new TradePlanAgent instance with 
    the provided configuration parameters, allowing for easy creation
    and configuration of trade plan agents.
    
    Args:
        config: Optional configuration dictionary with parameters like
               risk_reward_ratio, portfolio_risk_per_trade, etc.
        **kwargs: Additional keyword arguments that will be added to config
               
    Returns:
        Configured TradePlanAgent instance
    """
    # Handle legacy calls with data_provider parameter
    if 'data_provider' in kwargs and config is None:
        config = {'data_provider': kwargs['data_provider']}
    elif 'data_provider' in kwargs:
        if config is None:
            config = {}
        config['data_provider'] = kwargs['data_provider']
    
    # Create a new config dict if None was provided
    if config is None:
        config = {}
    
    # Add any other kwargs to config
    for key, value in kwargs.items():
        if key != 'data_provider':  # Skip data_provider since we already handled it
            config[key] = value
    
    trade_plan_agent = TradePlanAgent(config)
    logger.info(f"Created enhanced TradePlanAgent with config parameters: {list(config.keys()) if config else 'default'}")
    return trade_plan_agent

class TradeType(Enum):
    """Enum for trade type classification"""
    SCALP = "scalp"  # Very short term (minutes to hours)
    SWING = "swing"  # Short to medium term (hours to days)
    TREND_FOLLOWING = "trend_following"  # Medium to long term following a trend
    MEAN_REVERSION = "mean_reversion"  # Betting on return to average
    UNKNOWN = "unknown"  # Default when not enough information
    
    def __str__(self):
        return self.value

class TradePlanAgent(BaseDecisionAgent):
    """
    Agent that generates comprehensive trade plans.
    
    This agent processes decisions from the DecisionAgent and creates a structured 
    trade execution plan with entry prices, stop-loss, take-profit, and position sizing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the trade plan agent.
        
        Args:
            config: Optional configuration parameters
        """
        super().__init__()
        self.name = "TradePlanAgent"
        self._description = "Generates detailed trade execution plans"
        self.agent_name = "trade_plan_agent"
        
        # Load configuration or use defaults
        self.config = config or {}
        
        # Load risk parameters from config or use defaults
        self.risk_reward_ratio = self.config.get("risk_reward_ratio", 1.5)
        self.max_position_size = self.config.get("max_position_size", 1.0)
        self.min_position_size = self.config.get("min_position_size", 0.1)
        self.portfolio_risk_per_trade = self.config.get("portfolio_risk_per_trade", 0.02)  # 2% risk per trade
        
        # Default validity durations in minutes by timeframe
        self.validity_durations = self.config.get("validity_durations", {
            "1m": 15,      # 15 minutes
            "5m": 45,      # 45 minutes
            "15m": 120,    # 2 hours
            "30m": 240,    # 4 hours
            "1h": 480,     # 8 hours
            "4h": 1440,    # 24 hours
            "1d": 4320,    # 3 days
            "1w": 20160,   # 14 days
            "default": 60  # 1 hour default
        })
        
        # Volatility multipliers for stop-loss/take-profit calculations
        self.volatility_multipliers = self.config.get("volatility_multipliers", {
            "atr_sl": 1.5,      # ATR multiplier for stop-loss
            "atr_tp": 3.0,      # ATR multiplier for take-profit
            "stdev_sl": 2.0,    # Standard deviation multiplier for stop-loss
            "stdev_tp": 4.0,    # Standard deviation multiplier for take-profit
            "candle_body_sl": 1.5,  # Recent candle body multiplier for stop-loss
            "candle_body_tp": 3.0   # Recent candle body multiplier for take-profit
        })
        
        # Confidence thresholds for position sizing
        self.confidence_tiers = {
            "low": self.config.get("low_confidence_threshold", 50),
            "medium": self.config.get("medium_confidence_threshold", 70),
            "high": self.config.get("high_confidence_threshold", 85)
        }
        
        # Position size multipliers for each confidence tier
        self.position_size_multipliers = {
            "low": self.config.get("low_confidence_size", 0.3),
            "medium": self.config.get("medium_confidence_size", 0.6),
            "high": self.config.get("high_confidence_size", 1.0)
        }
            
        # Logging configuration
        self.detailed_logging = self.config.get("detailed_logging", False)
        self.test_mode = self.config.get("test_mode", False)
        
        # Create logs directory for trade plans if it doesn't exist
        self.log_dir = os.path.join("logs", "trade_plans")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
        
        # Trade type thresholds for classification
        self.trade_type_thresholds = self.config.get("trade_type_thresholds", {
            "min_swing_validity_minutes": 240,  # 4 hours
            "min_trend_validity_minutes": 1440, # 24 hours
            "min_swing_confidence": 65,
            "min_trend_confidence": 80
        })
        
        # Time-based validity settings
        self.default_validity_minutes = self.config.get("default_validity_minutes", 60)
        
        # Tags for grouping and analysis
        self.default_tags = self.config.get("default_tags", [])
        
        # Logging configuration
        self.detailed_logging = self.config.get("detailed_logging", False)
        self.test_mode = self.config.get("test_mode", False)
        
        # Create logs directory for trade plans if it doesn't exist
        self.log_dir = os.path.join("logs", "trade_plans")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
        
        logger.info(f"Trade plan agent initialized with risk:reward ratio {self.risk_reward_ratio}")
    
    def generate_trade_plan(
        self, 
        decision: Dict[str, Any], 
        market_data: Dict[str, Any],
        analyst_outputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a detailed trade plan based on the decision and market data.
        
        Args:
            decision: Decision from the DecisionAgent including signal and confidence
            market_data: Current market data including price and symbol
            analyst_outputs: Results from various analyst agents
            
        Returns:
            Complete trade plan with entry, SL, TP and position size
        """
        start_time = time.time()
        logger.info(f"Generating trade plan for {decision.get('signal')} decision")
        
        # Extract the trading signal and confidence
        signal = decision.get('signal', 'NEUTRAL')
        original_signal = signal  # Keep the original signal for reference
        confidence = decision.get('confidence', 0)
        
        # Check for CONFLICTED status (either in signal or final_signal)
        is_conflicted = signal == "CONFLICTED" or decision.get('final_signal') == "CONFLICTED"
        
        # Initialize conflict flag
        conflict_flag = False
        
        # If conflicted, we'll still generate a plan but with additional caution
        if is_conflicted:
            conflict_flag = True
            logger.warning(f"CONFLICTED signal detected. Generating cautious trade plan with reduced risk.")
            
            # Check if we need to override a CONFLICTED signal based on agent contributions
            override_signal = None
            override_reason = None
            
            # First check for directional bias if available
            if decision.get('directional_bias') in ["BUY", "SELL"]:
                override_signal = decision.get('directional_bias')
                override_reason = "Using directional bias from decision agent"
            
            # If no directional bias, try to analyze agent contributions
            elif "agent_contributions" in decision and isinstance(decision["agent_contributions"], dict):
                # Count signal types and their confidences
                signal_counts = {}
                signal_total_confidences = {}
                signal_weighted_scores = {}
                
                for agent, data in decision.get('agent_contributions', {}).items():
                    if isinstance(data, dict) and 'signal' in data:
                        agent_signal = data.get('signal')
                        agent_confidence = data.get('confidence', 50)
                        agent_weight = 1.0  # Default weight
                        
                        # Assign weights based on agent type (can be customized)
                        if "Technical" in agent:
                            agent_weight = 1.2
                        elif "Sentiment" in agent:
                            agent_weight = 0.8
                        
                        if agent_signal not in signal_counts:
                            signal_counts[agent_signal] = 0
                            signal_total_confidences[agent_signal] = 0
                            signal_weighted_scores[agent_signal] = 0
                        
                        signal_counts[agent_signal] += 1
                        signal_total_confidences[agent_signal] += agent_confidence
                        signal_weighted_scores[agent_signal] += agent_confidence * agent_weight
                
                # Only consider BUY and SELL signals for override
                actionable_signals = {s: count for s, count in signal_counts.items() if s in ["BUY", "SELL"]}
                
                # Find the dominant actionable signal (if any)
                if actionable_signals:
                    # Get the signal with highest weighted score or count if tied
                    dominant_signal = max(actionable_signals.keys(), 
                                         key=lambda s: (signal_weighted_scores.get(s, 0), signal_counts.get(s, 0)))
                    dominant_count = signal_counts[dominant_signal]
                    total_agents = sum(signal_counts.values())
                    
                    # If the dominant signal represents at least 50% of actionable agents or
                    # at least 2 agents and has higher weight than any other single signal
                    if (dominant_count / total_agents >= 0.5 or 
                       (dominant_count >= 2 and dominant_count > max([count for sig, count in signal_counts.items() 
                                                                   if sig != dominant_signal], default=0))):
                        
                        override_signal = dominant_signal
                        avg_confidence = signal_total_confidences[override_signal] / dominant_count
                        
                        # Set the reason for the override
                        override_reason = (f"{override_signal} signals had dominant weight "
                                          f"({dominant_count}/{total_agents} agents, avg conf: {avg_confidence:.1f}%) "
                                          f"despite conflict.")
            
            # Apply override if determined
            if override_signal and override_signal in ["BUY", "SELL"]:
                logger.warning(f"Overriding CONFLICTED signal to {override_signal}")
                logger.info(f"Override reason: {override_reason}")
                signal = override_signal
            
            # Reduce confidence for conflicted signals
            original_confidence = confidence
            confidence = confidence * 0.85  # Reduce confidence by 15%
            logger.info(f"Reduced confidence from {original_confidence} to {confidence} due to conflict")
        
        # Determine if this is an actionable signal
        is_actionable = signal in ["BUY", "SELL"]
        
        # Get the interval from market data or use default
        interval = market_data.get('interval', '1h')
        
        # If no actionable signal, return a minimal plan
        if not is_actionable:
            logger.info(f"Non-actionable signal {signal}, generating minimal plan")
            
            # Create minimal plan with additional conflict information if needed
            minimal_plan = {
                "signal": signal,
                "original_signal": original_signal,  # Preserve the original signal
                "confidence": confidence,
                "entry_price": None,
                "stop_loss": None,
                "take_profit": None,
                "position_size": 0,
                "reasoning": "No actionable signal generated",
                "timestamp": datetime.now().isoformat(),
                "execution_time_seconds": time.time() - start_time,
                "symbol": market_data.get('symbol', 'UNKNOWN'),
                "interval": interval
            }
            
            # Add conflict flag and fallback information for CONFLICTED signals
            if is_conflicted:
                minimal_plan["conflict_flag"] = True
                minimal_plan["fallback_plan"] = {
                    "conflict": {
                        "detected": True,
                        "reason": "⚠️ Conflicted signal detected - applying reduced position sizing and increased caution",
                        "original_signal": original_signal,
                        "applied_signal": signal,
                        "confidence_reduction": "15%"
                    }
                }
                minimal_plan["tags"] = ["conflicted"]
                
                # Add warning to plan digest for conflicted signals
                warning_message = "⚠️ CONFLICT DETECTED: Signal conflict among analyst agents. Using reduced position sizing (50%). Exercise caution."
                minimal_plan["plan_digest"] = warning_message
            
            return minimal_plan
        
        # Extract current price from market data
        symbol = market_data.get('symbol', 'UNKNOWN')
        current_price = self._get_current_price(market_data)
        
        if current_price is None:
            logger.warning(f"Could not determine current price for {symbol}")
            return self.build_error_response(
                "INSUFFICIENT_DATA",
                f"Could not determine current price for {symbol}"
            )
        
        # Extract historical data for volatility calculations if available
        historical_data = self._extract_historical_data(market_data)
        
        # Get liquidity analysis if available
        liquidity_analysis = None
        if analyst_outputs and "liquidity_analysis" in analyst_outputs:
            liquidity_analysis = analyst_outputs["liquidity_analysis"]
        
        # Determine entry, stop-loss, and take-profit levels with volatility awareness
        entry_price, stop_loss, take_profit, used_fallback = self._determine_trade_levels(
            signal=signal, 
            current_price=current_price,
            liquidity_analysis=liquidity_analysis,
            historical_data=historical_data,
            interval=interval
        )
        
        # Extract conflict score if available
        conflict_score = None
        if isinstance(decision.get('agent_contributions'), dict):
            # Count agents by signal type
            signal_counts = {}
            for agent, data in decision.get('agent_contributions', {}).items():
                if isinstance(data, dict) and 'signal' in data:
                    sig = data['signal']
                    if sig not in signal_counts:
                        signal_counts[sig] = 0
                    signal_counts[sig] += 1
            
            # Conflict score is higher when there are more opposing signals
            if len(signal_counts) > 1:
                conflict_score = (len(signal_counts) - 1) / len(decision.get('agent_contributions', {}))
                conflict_score = min(1.0, max(0.0, conflict_score))
                conflict_score = round(conflict_score * 100)  # As percentage
                logger.info(f"Calculated conflict score: {conflict_score}% based on {len(signal_counts)} different signals")
                
        # Calculate position size based on confidence, conflict score, and conflict flag
        position_size = self._calculate_position_size(confidence, conflict_score, is_conflicted)
        
        # Generate reason summary
        structured_reason_summary = self._generate_reason_summary(decision, analyst_outputs)
        
        # Determine validity period
        valid_until = self._calculate_validity_period(interval, confidence, historical_data)
        
        # Classify trade type
        trade_type = self._classify_trade_type(
            signal, confidence, valid_until, historical_data, interval
        )
        
        # Calculate risk metrics
        risk_snapshot = self._calculate_risk_snapshot(
            signal, entry_price, stop_loss, take_profit, position_size, current_price
        )
        
        # Get custom tags or use defaults
        tags = self.default_tags.copy()
        if "tags" in decision:
            tags.extend(decision["tags"])
        
        # Filter out any "UnknownAgent" entries from contributing_agents
        contributing_agents = [agent for agent in decision.get('contributing_agents', []) 
                              if agent != "UnknownAgent"]
        
        # Check if decision was CONFLICTED but we're recommending a trade
        override_decision = False
        override_reason = None
        
        if decision.get('final_signal') == "CONFLICTED" and signal in ["BUY", "SELL"]:
            override_decision = True
            if signal == "BUY":
                override_reason = "BUY agents had dominant weight despite conflict."
            else:  # SELL
                override_reason = "SELL agents had dominant weight despite conflict."
                
        # Version metadata for the trade plan
        plan_metadata = {
            "plan_version": "1.1.0",
            "agent_version": getattr(self, "version", "0.2.0"),
            "strategy_context": "standard"
        }
        
        # Normalize confidence to standard scale
        normalized_confidence = min(100, max(0, int(confidence)))
        
        # Determine fallback usage details with enhanced structure and reasons
        fallback_plan = {
            "entry": {
                "used": entry_price == current_price,  # True if default entry price was used
                "reason": "Default current price used as entry" if entry_price == current_price else ""
            },
            "stop_loss": {
                "used": False,
                "reason": ""
            },
            "take_profit": {
                "used": False,
                "reason": ""
            }
        }
        
        # Add conflict information to fallback plan if applicable
        if is_conflicted:
            fallback_plan["conflict"] = {
                "detected": True,
                "reason": "⚠️ Conflicted signal detected - applying reduced position sizing and increased caution",
                "original_signal": original_signal,
                "applied_signal": signal,
                "confidence_reduction": "15%"
            }
        
        # Check if liquidity data was used
        if liquidity_analysis and isinstance(liquidity_analysis, dict):
            # For entry
            suggested_entry = liquidity_analysis.get("suggested_entry")
            if suggested_entry is not None and abs(entry_price - suggested_entry) < 0.001 * entry_price:
                fallback_plan["entry"]["used"] = False  # Not a fallback - used liquidity data
                fallback_plan["entry"]["reason"] = ""
                
            # For stop loss
            suggested_stop_loss = liquidity_analysis.get("suggested_stop_loss")
            if suggested_stop_loss is not None and stop_loss is not None and abs(stop_loss - suggested_stop_loss) < 0.001 * entry_price:
                fallback_plan["stop_loss"]["used"] = False
                fallback_plan["stop_loss"]["reason"] = ""
        
        # Check if ATR was used for stop_loss or take_profit
        atr_used = False
        atr_method_used = None
        
        if historical_data and len(historical_data) >= 14:
            atr_value = self._calculate_atr(historical_data, period=14)
            if atr_value is not None:
                # Compare the actual values with what ATR would have given
                atr_sl_multiplier = self.volatility_multipliers.get("atr_sl", 1.5)
                expected_atr_sl = None
                if signal == "BUY":
                    expected_atr_sl = entry_price - (atr_value * atr_sl_multiplier)
                else:  # SELL
                    expected_atr_sl = entry_price + (atr_value * atr_sl_multiplier)
                
                if expected_atr_sl is not None:
                    # If the stop_loss is very close to the expected ATR-based value, ATR was likely used
                    if stop_loss is not None and abs(stop_loss - expected_atr_sl) < 0.001 * entry_price:  # Within 0.1% margin
                        fallback_plan["stop_loss"]["used"] = True
                        fallback_plan["stop_loss"]["reason"] = f"ATR-based stop-loss with {atr_sl_multiplier}x multiplier"
                        atr_used = True
                        atr_method_used = "stop_loss"
                
                # Similar check for take_profit
                atr_tp_multiplier = self.volatility_multipliers.get("atr_tp", 3.0)
                expected_atr_tp = None
                if signal == "BUY":
                    expected_atr_tp = entry_price + (atr_value * atr_tp_multiplier)
                else:  # SELL
                    expected_atr_tp = entry_price - (atr_value * atr_tp_multiplier)
                
                if expected_atr_tp is not None:
                    # If the take_profit is very close to the expected ATR-based value, ATR was likely used
                    if take_profit is not None and abs(take_profit - expected_atr_tp) < 0.001 * entry_price:  # Within 0.1% margin
                        fallback_plan["take_profit"]["used"] = True
                        fallback_plan["take_profit"]["reason"] = f"ATR-based take-profit with {atr_tp_multiplier}x multiplier"
                        if not atr_used:  # Only set these if not already set
                            atr_used = True
                            atr_method_used = "take_profit"
        
        # Check for standard deviation based fallbacks
        if historical_data and len(historical_data) >= 5 and not atr_used:
            # Calculate recent volatility as standard deviation of close prices
            recent_prices = [candle.get('close', 0) for candle in historical_data[-20:] 
                            if isinstance(candle.get('close'), (int, float))]
            
            if len(recent_prices) >= 5:
                volatility = self._calculate_stdev(recent_prices)
                
                if volatility is not None:
                    # Check stop loss
                    stdev_multiplier = self.volatility_multipliers.get("stdev_sl", 2.0)
                    expected_stdev_sl = None
                    
                    if signal == "BUY":
                        expected_stdev_sl = entry_price - (volatility * stdev_multiplier)
                    else:  # SELL
                        expected_stdev_sl = entry_price + (volatility * stdev_multiplier)
                    
                    if expected_stdev_sl is not None and stop_loss is not None and abs(stop_loss - expected_stdev_sl) < 0.001 * entry_price:
                        if not fallback_plan["stop_loss"]["used"]:  # Don't overwrite ATR reason
                            fallback_plan["stop_loss"]["used"] = True
                            fallback_plan["stop_loss"]["reason"] = f"Standard deviation based stop-loss with {stdev_multiplier}x multiplier"
                    
                    # Check take profit
                    stdev_tp_multiplier = self.volatility_multipliers.get("stdev_tp", 4.0)
                    expected_stdev_tp = None
                    
                    if signal == "BUY":
                        expected_stdev_tp = entry_price + (volatility * stdev_tp_multiplier)
                    else:  # SELL
                        expected_stdev_tp = entry_price - (volatility * stdev_tp_multiplier)
                    
                    if expected_stdev_tp is not None and take_profit is not None and abs(take_profit - expected_stdev_tp) < 0.001 * entry_price:
                        if not fallback_plan["take_profit"]["used"]:  # Don't overwrite ATR reason
                            fallback_plan["take_profit"]["used"] = True
                            fallback_plan["take_profit"]["reason"] = f"Standard deviation based take-profit with {stdev_tp_multiplier}x multiplier"
        
        # If fallbacks still not identified, check for percentage-based fallbacks
        if not fallback_plan["stop_loss"]["used"] and not fallback_plan["take_profit"]["used"]:
            # Default percentage checks
            default_stop_percent = 0.01  # 1%
            expected_percent_sl = entry_price * (1 - default_stop_percent if signal == "BUY" else 1 + default_stop_percent)
            
            if stop_loss is not None and abs(stop_loss - expected_percent_sl) < 0.001 * entry_price:
                fallback_plan["stop_loss"]["used"] = True
                fallback_plan["stop_loss"]["reason"] = f"Default {default_stop_percent*100}% stop-loss calculation"
            
            r_r_ratio = self.risk_reward_ratio
            if stop_loss is not None:
                risk = abs(entry_price - stop_loss)
                expected_percent_tp = entry_price + (risk * r_r_ratio) if signal == "BUY" else entry_price - (risk * r_r_ratio)
                
                if take_profit is not None and abs(take_profit - expected_percent_tp) < 0.001 * entry_price:
                    fallback_plan["take_profit"]["used"] = True
                    fallback_plan["take_profit"]["reason"] = f"Risk-reward ratio based take-profit ({r_r_ratio}:1)"
        
        # Auto-tagging based on logic
        auto_tags = []
        
        # Add 'conflicted' tag if signal was CONFLICTED
        if is_conflicted:
            auto_tags.append("conflicted")
        
        # Check for high conflict tag
        agent_signals = {}
        if isinstance(decision.get('agent_contributions'), dict):
            for agent, data in decision.get('agent_contributions', {}).items():
                if isinstance(data, dict) and 'signal' in data and 'confidence' in data:
                    # Only consider strong signals (confidence >= 70)
                    if data['confidence'] >= 70:
                        signal = data['signal']
                        if signal not in agent_signals:
                            agent_signals[signal] = 0
                        agent_signals[signal] += 1
        
        # If there are multiple strong opposing signals, add high_conflict tag
        opposing_signals = 0
        for sig in ["BUY", "SELL", "HOLD"]:
            if sig in agent_signals and agent_signals[sig] > 0:
                opposing_signals += 1
        
        if opposing_signals >= 2:
            auto_tags.append("high_conflict")
        
        # Check for liquidity-based entry
        if liquidity_analysis and isinstance(liquidity_analysis, dict) and liquidity_analysis.get("suggested_entry") is not None:
            auto_tags.append("liquidity_based_entry")
        
        # Check for ATR-based stop loss or take profit
        if atr_used:
            auto_tags.append("ATR_SL")
        
        # Combine with existing tags
        tags.extend(auto_tags)
        
        # Remove duplicates while preserving order
        unique_tags = []
        for tag in tags:
            if tag not in unique_tags:
                unique_tags.append(tag)
        
        # Calculate summary confidence metrics
        weighted_confidence = decision.get('weighted_confidence', confidence)
        directional_confidence = decision.get('directional_confidence', 0)
        
        summary_confidence = {
            "average": confidence,
            "weighted": weighted_confidence,
            "directional": directional_confidence
        }
        
        # Generate a human-readable plan digest
        plan_digest = self._generate_plan_digest(
            signal=signal,
            confidence=confidence,
            liquidity_used="liquidity_based_entry" in unique_tags,
            high_conflict="high_conflict" in unique_tags,
            trade_type=trade_type,
            risk_snapshot=risk_snapshot,
            reason_summary=structured_reason_summary,
            tags=unique_tags,
            agent_contributions=decision.get('agent_contributions', {}),
            is_conflicted=is_conflicted  # Pass the conflict flag
        )
        
        # Prepare decision trace object for transparency and future learning
        decision_trace = {
            "signals": {},  # Signal counts and confidences
            "weights": {},  # Agent weights used
            "scores": {}    # Weighted scores
        }
        
        # Extract signal information from decision if available
        if isinstance(decision.get('agent_contributions'), dict):
            for agent, data in decision.get('agent_contributions', {}).items():
                if isinstance(data, dict) and 'signal' in data and 'confidence' in data:
                    signal_key = data['signal']
                    if signal_key not in decision_trace["signals"]:
                        decision_trace["signals"][signal_key] = []
                    
                    decision_trace["signals"][signal_key].append({
                        "agent": agent,
                        "confidence": data['confidence']
                    })
        
        # Include agent weights if available
        if 'agent_weights' in decision and isinstance(decision['agent_weights'], dict):
            decision_trace["weights"] = decision['agent_weights'].copy()
        
        # Include score information if available
        if 'weighted_scores' in decision:
            decision_trace["scores"] = decision['weighted_scores']
        
        # Add a performance metrics placeholder for future backtest feedback
        performance_metrics = {
            "executed": False,
            "result": None,
            "pnl": None,
            "duration": None,
            "exit_price": None,
            "exit_time": None,
            "trade_id": None
        }
        
        # Add trade type to tags
        trade_type_tag = str(trade_type).lower()
        if trade_type_tag not in unique_tags:
            unique_tags.append(trade_type_tag)
        
        # Add volatility-based tags
        if atr_used:
            if "atr_volatility" not in unique_tags:
                unique_tags.append("atr_volatility")
        elif "low_volatility" not in unique_tags and "high_volatility" not in unique_tags:
            # Simple volatility classification based on risk:reward
            r_r = risk_snapshot.get("risk_reward_ratio", 0)
            if r_r > 3.0:
                unique_tags.append("low_volatility")
            elif r_r < 1.5:
                unique_tags.append("high_volatility")
        
        # Prepare comprehensive trade plan with enhanced details
        trade_plan = {
            # Plan metadata
            **plan_metadata,
            
            # Symbol and interval information
            "symbol": symbol,
            "interval": interval,
            
            # Core signal and pricing
            "signal": signal,
            "original_signal": original_signal,
            "confidence": confidence,
            "normalized_confidence": normalized_confidence,
            "summary_confidence": summary_confidence,
            "conflict_score": conflict_score,
            "conflict_flag": is_conflicted,  # Explicit flag for conflict detection
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_size": position_size,
            
            # Analysis and reasoning
            "reasoning": decision.get('reasoning', 'No reasoning provided'),
            "reason_summary": structured_reason_summary,  # Now using structured format
            "contributing_agents": contributing_agents,
            
            # Trade context and classification
            "valid_until": valid_until,
            "trade_type": str(trade_type),
            "risk_snapshot": risk_snapshot,
            "fallback_plan": fallback_plan,
            "tags": unique_tags,
            
            # Human-readable summary and tracing
            "plan_digest": plan_digest,
            "decision_trace": decision_trace,
            "performance": performance_metrics,
            
            # Timestamps and metadata
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": time.time() - start_time,
            "version": "1.0.0",
            "agent_version": "0.2.0"
        }
        
        # Add override information if applicable
        if override_decision:
            trade_plan["override_decision"] = True
            trade_plan["override_reason"] = override_reason
        
        logger.info(f"Trade plan generated for {signal} {symbol} with position size {position_size}")
        
        # Log the trade plan summary if it's an actionable signal or if detailed logging is enabled
        if is_actionable or self.detailed_logging or self.test_mode:
            self.log_trade_plan_summary(trade_plan)
        else:
            logger.info(f"Non-actionable signal {signal}, minimal trade plan generated")
            
        return trade_plan
    
    def make_decision(self, symbol: str = "UNKNOWN", interval: str = "1h", analyst_results: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Override the base make_decision method to generate a trade plan.
        This method is compatible with the BaseDecisionAgent interface.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            interval: Trading interval (e.g., '1h', '4h')
            analyst_results: Dictionary of analysis results from analyst agents
            **kwargs: Additional keyword arguments
            
        Returns:
            Trade plan dictionary
        """
        # Initialize variables
        data_dict = kwargs.get('data_dict', {})
        analyses = []
        
        # Use analyst_results if provided directly, or extract from kwargs
        if analyst_results:
            analyses = list(analyst_results.values()) if isinstance(analyst_results, dict) else analyst_results
        elif 'analyses' in data_dict:
            analyses = data_dict.get('analyses', [])
        
        logger.info(f"TradePlanAgent generating plan for {symbol} at {interval} interval")
        
        # Process each analyst's output
        signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "NEUTRAL": 0}
        signal_confidences = {"BUY": [], "SELL": [], "HOLD": [], "NEUTRAL": []}
        contributing_agents = []
        
        # Simple decision algorithm - count signals and average confidences
        for analysis in analyses:
            # Skip if empty, not a dict, or has errors
            if not analysis or not isinstance(analysis, dict) or 'error' in analysis:
                continue
                
            signal = analysis.get('signal', 'NEUTRAL')
            confidence = analysis.get('confidence', 50)
            agent_name = analysis.get('agent', 'UnknownAgent')
            
            # Normalize NEUTRAL to HOLD for consistency
            if signal == "NEUTRAL":
                signal = "HOLD"
                
            # Count this signal
            signal_counts[signal] += 1
            signal_confidences[signal].append(confidence)
            
            # Track contributing agents for strong signals
            if signal in ["BUY", "SELL"] and confidence >= 65:
                contributing_agents.append(agent_name)
        
        # Determine the final signal based on counts
        final_signal = "HOLD"  # Default
        max_count = signal_counts["HOLD"]
        
        if signal_counts["BUY"] > max_count:
            final_signal = "BUY"
            max_count = signal_counts["BUY"]
            
        if signal_counts["SELL"] > max_count:
            final_signal = "SELL"
            
        # Calculate average confidence for the final signal
        confidences = signal_confidences[final_signal]
        final_confidence = sum(confidences) / len(confidences) if confidences else 50
        
        # Create the decision
        decision = {
            "signal": final_signal,
            "confidence": round(final_confidence, 1),
            "contributing_agents": contributing_agents,
            "reasoning": f"Signal based on {len(analyses)} analyst inputs with {final_signal} having the most votes"
        }
        
        # Extract market data from data_dict or analyses
        market_data = data_dict.get('market_data', {})
        if not market_data:
            # Try to extract from analyses
            for analysis in analyses:
                if isinstance(analysis, dict):
                    if 'market_data' in analysis:
                        market_data = analysis['market_data']
                        break
                    elif 'current_price' in analysis:
                        market_data = {'current_price': analysis['current_price'], 'symbol': symbol}
                        break
        
        # If market data is still missing, create a minimal version
        if not market_data:
            market_data = {'symbol': symbol, 'interval': interval}
        
        # Prepare analyst_outputs for generate_trade_plan
        analyst_outputs = {}
        for analysis in analyses:
            if isinstance(analysis, dict):
                agent_name = analysis.get('agent', '')
                if agent_name:
                    analyst_outputs[agent_name] = analysis
        
        # Generate trade plan based on the decision
        logger.info(f"Generating trade plan for {final_signal} decision with {round(final_confidence, 1)}% confidence")
        trade_plan = self.generate_trade_plan(
            decision=decision,
            market_data=market_data,
            analyst_outputs=analyst_outputs
        )
        
        # Return the combined output if trade_plan is valid
        if trade_plan and isinstance(trade_plan, dict):
            combined_plan = {**decision, **trade_plan}
            
            # Log the combined plan if it's not already logged
            if not self.detailed_logging and not self.test_mode and final_signal in ["BUY", "SELL"]:
                self.log_trade_plan_summary(combined_plan)
                
            return combined_plan
        else:
            # Return basic decision with error info if trade plan generation failed
            error_response = self.build_error_response(
                "TRADE_PLAN_GENERATION_FAILED",
                "Failed to generate trade plan due to insufficient data"
            )
            logger.warning("Failed to generate trade plan due to insufficient data")
            return {**decision, **error_response}
    
    def _get_current_price(self, market_data: Dict[str, Any]) -> Optional[float]:
        """
        Extract the current price from market data.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Current price as float or None if not available
        """
        # Try multiple possible locations for price data
        price = None
        
        # Direct price field
        if "current_price" in market_data:
            price = market_data["current_price"]
        elif "price" in market_data:
            price = market_data["price"]
        
        # Check in OHLCV data
        elif "ohlcv" in market_data and market_data["ohlcv"]:
            ohlcv = market_data["ohlcv"]
            if isinstance(ohlcv, list) and ohlcv:
                last_candle = ohlcv[-1]
                if isinstance(last_candle, dict) and "close" in last_candle:
                    price = last_candle["close"]
                elif isinstance(last_candle, list) and len(last_candle) >= 5:
                    # Assuming [timestamp, open, high, low, close] format
                    price = last_candle[4]
        
        # Try to fetch from data provider if available
        elif "data_provider" in market_data and market_data["data_provider"]:
            data_provider = market_data["data_provider"]
            symbol = market_data.get("symbol", "")
            
            if symbol and hasattr(data_provider, "get_current_price"):
                try:
                    # Clean symbol format if needed
                    clean_symbol = symbol.replace("/", "")
                    price = data_provider.get_current_price(clean_symbol)
                except Exception as e:
                    logger.warning(f"Error fetching price from data provider: {str(e)}")
        
        # Convert to float if not None
        if price is not None:
            try:
                return float(price)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert price {price} to float")
                return None
        
        return None
    
    def _determine_trade_levels(
        self, 
        signal: str, 
        current_price: float,
        liquidity_analysis: Optional[Dict[str, Any]] = None,
        historical_data: Optional[List[Dict[str, Any]]] = None,
        interval: str = '1h'
    ) -> Tuple[float, float, float, bool]:
        """
        Determine entry, stop-loss, and take-profit levels with volatility awareness.
        
        Args:
            signal: Trading signal (BUY or SELL)
            current_price: Current market price
            liquidity_analysis: Optional liquidity analysis results
            historical_data: Optional historical price data for volatility calcs
            interval: Trading interval (e.g., '1h', '4h')
            
        Returns:
            Tuple of (entry_price, stop_loss, take_profit, used_fallback)
        """
        entry_price = current_price
        stop_loss = None
        take_profit = None
        used_fallback = False
        
        # Try to use liquidity analysis for optimal levels if available
        if liquidity_analysis and isinstance(liquidity_analysis, dict):
            # Check for suggested entry and stop loss from liquidity analysis
            suggested_entry = liquidity_analysis.get("suggested_entry")
            suggested_stop_loss = liquidity_analysis.get("suggested_stop_loss")
            
            if suggested_entry is not None:
                entry_price = suggested_entry
                
            if suggested_stop_loss is not None:
                stop_loss = suggested_stop_loss
        
        # Try to calculate volatility from historical data
        volatility = None
        atr_value = None
        recent_candle_range = None
        
        if historical_data and len(historical_data) >= 14:
            # Calculate ATR if sufficient data
            atr_value = self._calculate_atr(historical_data, period=14)
            
            # Calculate recent volatility as standard deviation of close prices
            recent_prices = [candle.get('close', 0) for candle in historical_data[-20:] 
                            if isinstance(candle.get('close'), (int, float))]
            if len(recent_prices) >= 5:
                volatility = self._calculate_stdev(recent_prices)
            
            # Get most recent candle range
            latest_candle = historical_data[-1]
            if isinstance(latest_candle, dict):
                high = latest_candle.get('high')
                low = latest_candle.get('low')
                if high is not None and low is not None:
                    recent_candle_range = float(high) - float(low)
        
        # Determine stop loss using volatility if available, otherwise use liquidity analysis or default
        if stop_loss is None:
            used_fallback = True
            
            if atr_value is not None:
                # Use ATR for stop loss
                atr_multiplier = self.volatility_multipliers.get("atr_sl", 1.5)
                if signal == "BUY":
                    stop_loss = entry_price - (atr_value * atr_multiplier)
                else:  # SELL
                    stop_loss = entry_price + (atr_value * atr_multiplier)
            elif volatility is not None:
                # Use price standard deviation for stop loss
                stdev_multiplier = self.volatility_multipliers.get("stdev_sl", 2.0)
                if signal == "BUY":
                    stop_loss = entry_price - (volatility * stdev_multiplier)
                else:  # SELL
                    stop_loss = entry_price + (volatility * stdev_multiplier)
            elif recent_candle_range is not None:
                # Use recent candle range for stop loss
                candle_multiplier = self.volatility_multipliers.get("candle_body_sl", 1.5)
                if signal == "BUY":
                    stop_loss = entry_price - (recent_candle_range * candle_multiplier)
                else:  # SELL
                    stop_loss = entry_price + (recent_candle_range * candle_multiplier)
            else:
                # Fall back to default percentage-based stop loss
                default_stop_percent = 0.01  # 1%
                if signal == "BUY":
                    stop_loss = entry_price * (1 - default_stop_percent)
                else:  # SELL
                    stop_loss = entry_price * (1 + default_stop_percent)
        
        # Calculate risk (distance from entry to stop)
        risk = abs(entry_price - stop_loss)
        
        # Determine take profit using the optimal approach available
        if atr_value is not None:
            # Use ATR for take profit
            atr_multiplier = self.volatility_multipliers.get("atr_tp", 3.0)
            if signal == "BUY":
                take_profit = entry_price + (atr_value * atr_multiplier)
            else:  # SELL
                take_profit = entry_price - (atr_value * atr_multiplier)
        elif volatility is not None:
            # Use price standard deviation for take profit
            stdev_multiplier = self.volatility_multipliers.get("stdev_tp", 4.0)
            if signal == "BUY":
                take_profit = entry_price + (volatility * stdev_multiplier)
            else:  # SELL
                take_profit = entry_price - (volatility * stdev_multiplier)
        else:
            # Fall back to risk:reward ratio-based take profit
            if signal == "BUY":
                take_profit = entry_price + (risk * self.risk_reward_ratio)
            else:  # SELL
                take_profit = entry_price - (risk * self.risk_reward_ratio)
        
        # Round values to avoid excessive precision
        entry_precision = self._estimate_price_precision(current_price)
        entry_price = round(entry_price, entry_precision)
        stop_loss = round(stop_loss, entry_precision)
        take_profit = round(take_profit, entry_precision)
        
        return entry_price, stop_loss, take_profit, used_fallback
    
    def _calculate_position_size(self, confidence: float, conflict_score: Optional[int] = None, is_conflicted: bool = False) -> float:
        """
        Calculate position size based on confidence level and conflict score.
        
        Args:
            confidence: Decision confidence percentage
            conflict_score: Optional conflict score (0-100) indicating level of disagreement between agents
            is_conflicted: Boolean flag indicating if the signal is explicitly CONFLICTED
            
        Returns:
            Position size multiplier (0.0 to 1.0)
        """
        # Determine confidence tier
        if confidence >= self.confidence_tiers["high"]:
            tier = "high"
        elif confidence >= self.confidence_tiers["medium"]:
            tier = "medium"
        elif confidence >= self.confidence_tiers["low"]:
            tier = "low"
        else:
            # Below minimum confidence threshold
            return 0.0
        
        # Get position size multiplier for the tier
        position_size = self.position_size_multipliers[tier]
        
        # Apply stronger conflict reduction for explicit CONFLICTED signals
        if is_conflicted:
            # For explicit CONFLICTED signals, apply a fixed 50% reduction
            original_size = position_size
            position_size = position_size * 0.5  # 50% reduction
            logger.warning(f"Applying 50% position reduction for CONFLICTED signal: {original_size:.2f} → {position_size:.2f}")
        
        # Apply conflict risk reduction if conflict score is provided
        elif conflict_score is not None and conflict_score > 0:
            # Calculate conflict reduction factor (higher conflict = smaller position)
            # At max conflict (100%), reduce position by up to 70%
            max_conflict_reduction = 0.7
            conflict_reduction = (conflict_score / 100) * max_conflict_reduction
            
            # Apply reduction
            original_size = position_size
            position_size = position_size * (1 - conflict_reduction)
            
            logger.info(f"Applying conflict-based position reduction: {conflict_score}% conflict score reduces position from {original_size:.2f} to {position_size:.2f}")
        
        # Ensure position size is within limits
        position_size = max(min(position_size, self.max_position_size), self.min_position_size)
        
        return position_size

    def _extract_historical_data(self, market_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Extract historical OHLCV data from market data.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            List of historical candles or None if not available
        """
        # Try multiple possible locations for historical data
        if "ohlcv" in market_data and market_data["ohlcv"]:
            return market_data["ohlcv"]
        elif "historical_data" in market_data and market_data["historical_data"]:
            return market_data["historical_data"]
        elif "candles" in market_data and market_data["candles"]:
            return market_data["candles"]
        
        return None
    
    def _calculate_atr(self, historical_data: List[Dict[str, Any]], period: int = 14) -> Optional[float]:
        """
        Calculate Average True Range (ATR) from historical data.
        
        Args:
            historical_data: List of historical OHLCV candles
            period: ATR period (default 14)
            
        Returns:
            ATR value or None if calculation failed
        """
        if len(historical_data) < period + 1:
            return None
        
        true_ranges = []
        
        # Process each candle to calculate TR
        for i in range(1, len(historical_data)):
            prev_candle = historical_data[i-1]
            curr_candle = historical_data[i]
            
            # Extract OHLC values, handling different data formats
            if isinstance(curr_candle, dict):
                curr_high = float(curr_candle.get('high', 0))
                curr_low = float(curr_candle.get('low', 0))
                curr_close = float(curr_candle.get('close', 0))
                prev_close = float(prev_candle.get('close', 0))
            elif isinstance(curr_candle, list) and len(curr_candle) >= 5:
                # Assuming [timestamp, open, high, low, close] format
                # Convert numeric indices to string indices for LSP
                curr_high = float(curr_candle[2] if len(curr_candle) > 2 else 0)
                curr_low = float(curr_candle[3] if len(curr_candle) > 3 else 0)
                curr_close = float(curr_candle[4] if len(curr_candle) > 4 else 0)
                prev_close = float(prev_candle[4] if len(prev_candle) > 4 else 0)
            else:
                continue
            
            # Calculate true range
            tr1 = curr_high - curr_low
            tr2 = abs(curr_high - prev_close)
            tr3 = abs(curr_low - prev_close)
            true_range = max(tr1, tr2, tr3)
            
            true_ranges.append(true_range)
        
        # Use simple moving average for ATR
        if len(true_ranges) >= period:
            recent_trs = true_ranges[-period:]
            return sum(recent_trs) / period
        
        return None
    
    def _calculate_stdev(self, values: List[float]) -> float:
        """
        Calculate standard deviation of a list of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Standard deviation
        """
        if not values:
            return 0
            
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        return math.sqrt(variance)
    
    def _estimate_price_precision(self, price: float) -> int:
        """
        Estimate appropriate decimal precision for a price.
        
        Args:
            price: Price value
            
        Returns:
            Number of decimal places to round to
        """
        # Higher precision for lower-valued assets
        if price < 0.1:
            return 8
        elif price < 1:
            return 6
        elif price < 10:
            return 5
        elif price < 100:
            return 4
        elif price < 1000:
            return 3
        elif price < 10000:
            return 2
        else:
            return 1
    
    def _format_agent_contributions(
        self,
        decision: Dict[str, Any],
        analyst_outputs: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Format agent contributions into a structured list for easy display.
        
        Args:
            decision: Decision dictionary from DecisionAgent
            analyst_outputs: Optional dictionary of analyst agent outputs
            
        Returns:
            List of dictionaries containing structured agent contributions
        """
        structured_contributions = []
        
        # First check if we have agent_contributions in the decision
        agent_contributions = decision.get('agent_contributions', {})
        contributing_agents = decision.get('contributing_agents', [])
        
        # Process agent_contributions if available
        if agent_contributions and isinstance(agent_contributions, dict):
            for agent_name, contribution in agent_contributions.items():
                if agent_name == "UnknownAgent":
                    continue
                    
                if isinstance(contribution, dict):
                    agent_item = {
                        'agent': agent_name,
                        'action': contribution.get('signal', 'UNKNOWN'),
                        'confidence': contribution.get('confidence', 0),
                        'reason': ''  # Default empty reason
                    }
                    
                    # Get reasoning from contribution if available
                    if 'reasoning' in contribution:
                        agent_item['reason'] = contribution['reasoning']
                    
                    # Try to get detailed reasoning from analyst_outputs
                    if analyst_outputs and isinstance(analyst_outputs, dict) and agent_name in analyst_outputs:
                        analyst_data = analyst_outputs[agent_name]
                        if isinstance(analyst_data, dict):
                            # Get the full reasoning and truncate if needed
                            full_reason = analyst_data.get('reasoning', '')
                            # Take first sentence or truncate to 100 chars
                            if full_reason:
                                short_reason = full_reason.split('.')[0]
                                if len(short_reason) > 100:
                                    short_reason = short_reason[:97] + "..."
                                agent_item['reason'] = short_reason
                    
                    structured_contributions.append(agent_item)
        
        # If no agent_contributions but we have analyst_outputs, extract from there
        elif analyst_outputs and isinstance(analyst_outputs, dict):
            for agent_name, agent_data in analyst_outputs.items():
                if not isinstance(agent_data, dict):
                    continue
                
                agent_signal = agent_data.get('signal', '')
                agent_confidence = agent_data.get('confidence', 0)
                
                # Get reasoning - try multiple possible fields
                agent_reason = ''
                if 'reasoning' in agent_data:
                    agent_reason = agent_data['reasoning']
                elif 'reason' in agent_data:
                    agent_reason = agent_data['reason']
                
                # Truncate long reasons
                if agent_reason and len(agent_reason) > 100:
                    agent_reason = agent_reason.split('.')[0]
                    if len(agent_reason) > 100:
                        agent_reason = agent_reason[:97] + "..."
                
                # Add to structured contributions
                structured_contributions.append({
                    'agent': agent_name,
                    'action': agent_signal,
                    'confidence': agent_confidence,
                    'reason': agent_reason
                })
        
        # If nothing else, try to extract from contributing_agents
        elif contributing_agents:
            signal = decision.get('signal', 'UNKNOWN')
            confidence = decision.get('confidence', 0)
            reasoning = decision.get('reasoning', '')
            
            for agent_name in contributing_agents:
                structured_contributions.append({
                    'agent': agent_name,
                    'action': signal,  # Use decision signal as fallback
                    'confidence': confidence,  # Use decision confidence as fallback
                    'reason': reasoning if agent_name == contributing_agents[0] else ''
                })
        
        # Sort by confidence (descending)
        structured_contributions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return structured_contributions
    
    def _generate_reason_summary(
        self, 
        decision: Dict[str, Any], 
        analyst_outputs: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a detailed reason summary from decision and analyst outputs.
        
        Args:
            decision: Decision dictionary from DecisionAgent
            analyst_outputs: Optional dictionary of analyst agent outputs
            
        Returns:
            List of dictionaries containing structured agent contributions
        """
        # Use the new _format_agent_contributions method to get structured agent data
        return self._format_agent_contributions(decision, analyst_outputs)
    
    def _calculate_validity_period(
        self, 
        interval: str, 
        confidence: float,
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Calculate the validity period for a trade plan.
        
        Args:
            interval: Trading interval (e.g., '1h', '4h')
            confidence: Decision confidence
            historical_data: Optional historical data for volatility adjustment
            
        Returns:
            ISO format timestamp for validity expiration
        """
        # Get base validity in minutes from interval
        validity_minutes = self.validity_durations.get(
            interval, self.validity_durations.get('default', 60)
        )
        
        # Adjust validity based on confidence
        # Higher confidence = longer validity
        if confidence >= 85:
            validity_minutes *= 1.5  # 50% longer for high confidence
        elif confidence <= 55:
            validity_minutes *= 0.7  # 30% shorter for low confidence
        
        # Calculate expiration time
        now = datetime.now()
        expiration = now + timedelta(minutes=validity_minutes)
        
        return expiration.isoformat()
    
    def _classify_trade_type(
        self,
        signal: str,
        confidence: float,
        valid_until: str,
        historical_data: Optional[List[Dict[str, Any]]] = None,
        interval: str = '1h'
    ) -> TradeType:
        """
        Classify the trade type based on signal, confidence, and validity.
        
        Args:
            signal: Trading signal
            confidence: Decision confidence
            valid_until: Validity timestamp
            historical_data: Optional historical data
            interval: Trading interval
            
        Returns:
            TradeType classification
        """
        # Calculate validity duration in minutes
        now = datetime.now()
        try:
            valid_datetime = datetime.fromisoformat(valid_until)
            validity_minutes = (valid_datetime - now).total_seconds() / 60
        except (ValueError, TypeError):
            # Fall back to default if datetime parsing fails
            validity_minutes = self.validity_durations.get(interval, 60)
        
        # Define thresholds from config
        min_swing_minutes = self.trade_type_thresholds.get("min_swing_validity_minutes", 240)
        min_trend_minutes = self.trade_type_thresholds.get("min_trend_validity_minutes", 1440)
        min_swing_confidence = self.trade_type_thresholds.get("min_swing_confidence", 65)
        min_trend_confidence = self.trade_type_thresholds.get("min_trend_confidence", 80)
        
        # Check for mean reversion pattern in historical data
        is_mean_reversion = False
        if historical_data and len(historical_data) >= 20:
            # Simple mean reversion check: price is significantly away from moving average
            try:
                recent_closes = [float(candle.get('close', 0)) for candle in historical_data[-20:] 
                                if isinstance(candle.get('close'), (int, float))]
                if recent_closes:
                    sma20 = sum(recent_closes) / len(recent_closes)
                    latest_price = recent_closes[-1]
                    price_deviation = abs(latest_price - sma20) / sma20
                    
                    # If price is more than 5% away from SMA and the signal is toward the mean
                    is_mean_reversion = (price_deviation > 0.05 and 
                                        ((signal == "BUY" and latest_price < sma20) or 
                                         (signal == "SELL" and latest_price > sma20)))
            except (IndexError, ZeroDivisionError, TypeError):
                pass
        
        # Classify based on criteria
        if is_mean_reversion:
            return TradeType.MEAN_REVERSION
        elif validity_minutes >= min_trend_minutes and confidence >= min_trend_confidence:
            return TradeType.TREND_FOLLOWING
        elif validity_minutes >= min_swing_minutes and confidence >= min_swing_confidence:
            return TradeType.SWING
        else:
            return TradeType.SCALP
    
    def _calculate_risk_snapshot(
        self,
        signal: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        current_price: float
    ) -> Dict[str, Any]:
        """
        Calculate risk metrics for the trade plan.
        
        Args:
            signal: Trading signal
            entry_price: Entry price
            stop_loss: Stop-loss price
            take_profit: Take-profit price
            position_size: Position size multiplier (0.0 to 1.0)
            current_price: Current market price
            
        Returns:
            Dictionary of risk metrics
        """
        # Calculate risk metrics
        risk_per_unit = abs(entry_price - stop_loss)
        reward_per_unit = abs(entry_price - take_profit)
        
        # Avoid division by zero
        risk_reward_ratio = reward_per_unit / risk_per_unit if risk_per_unit > 0 else 0
        
        # Calculate percentage risk
        risk_percent = (risk_per_unit / entry_price) * 100
        
        # Calculate portfolio risk based on position size and per-trade risk
        portfolio_risk = position_size * self.portfolio_risk_per_trade * 100
        
        # Calculate exposure
        exposure = position_size * 100  # Full position would be 100% exposure
        
        # Create the risk snapshot
        risk_snapshot = {
            "risk_per_unit": round(risk_per_unit, 2),
            "reward_per_unit": round(reward_per_unit, 2),
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "risk_percent": round(risk_percent, 2),
            "portfolio_risk_percent": round(portfolio_risk, 2),
            "portfolio_exposure_percent": round(exposure, 2)
        }
        
        return risk_snapshot
    
    def _generate_plan_digest(
        self,
        signal: str,
        confidence: float,
        liquidity_used: bool,
        high_conflict: bool,
        trade_type: TradeType,
        risk_snapshot: Dict[str, Any],
        reason_summary: List[Dict[str, Any]] = None,
        tags: List[str] = None,
        agent_contributions: Dict[str, Any] = None,
        is_conflicted: bool = False  # New parameter to track conflict state
    ) -> str:
        """
        Generate a human-readable digest of the trade plan.
        
        Args:
            signal: Trading signal (BUY/SELL/HOLD)
            confidence: Decision confidence
            liquidity_used: Whether liquidity data was used for entry
            high_conflict: Whether there was high conflict in agent recommendations
            trade_type: The type of trade (scalp, swing, etc.)
            risk_snapshot: Risk metrics for the trade
            reason_summary: Optional list of agent contribution summaries
            tags: Optional list of tags associated with the trade plan
            agent_contributions: Optional dictionary of agent contributions
            
        Returns:
            Human-readable plan digest with enhanced insights from agent contributions and tags
        """
        # Don't generate detailed digest for HOLD signals
        if signal == "HOLD" or signal == "NEUTRAL":
            return "No clear directional edge. Monitor for better setup."
        
        # Add conflict warning prefix if this is a conflicted signal
        conflict_prefix = ""
        if is_conflicted:
            conflict_prefix = "⚠️ CONFLICTED SIGNAL: Trading with reduced position size and increased caution. "
            # Reflect the confidence reduction in the rest of the digest
            confidence = max(0, confidence - 15)
        
        # Check for 'conflicted' in tags as a backup
        if not is_conflicted and tags and 'conflicted' in tags:
            conflict_prefix = "⚠️ CONFLICTED SIGNAL: Trading with reduced position size and increased caution. "
            confidence = max(0, confidence - 15)
            
        # Core market assessment with more natural, confident tone
        if signal == "BUY":
            if confidence >= 85:
                core = "Strong bullish momentum"
            elif confidence >= 70:
                core = "Bullish bias developing"
            elif confidence >= 55:
                core = "Cautious bullish opportunity"
            else:
                core = "Potential bullish reversal"
        else:  # SELL
            if confidence >= 85:
                core = "Strong bearish pressure"
            elif confidence >= 70:
                core = "Bearish trend forming"
            elif confidence >= 55:
                core = "Cautious selling opportunity"
            else:
                core = "Potential bearish reversal"
        
        # Contributing factors
        factors = []
        
        if liquidity_used:
            if signal == "BUY":
                factors.append("key support confirmed")
            else:
                factors.append("key resistance validated")
        
        # Analyze signal conflict in more detail
        if high_conflict:
            # Check for opposing directional signals (BUY vs SELL)
            has_buy_signals = False
            has_sell_signals = False
            buy_agents = []
            sell_agents = []
            
            if agent_contributions:
                for agent_name, data in agent_contributions.items():
                    if isinstance(data, dict) and 'signal' in data:
                        if data['signal'] == 'BUY':
                            has_buy_signals = True
                            buy_agents.append(agent_name.replace('Agent', ''))
                        elif data['signal'] == 'SELL':
                            has_sell_signals = True
                            sell_agents.append(agent_name.replace('Agent', ''))
            
            if has_buy_signals and has_sell_signals:
                # Direct conflict between BUY and SELL signals
                buy_str = ", ".join(buy_agents[:2])  # Limit to 2 agents for brevity
                sell_str = ", ".join(sell_agents[:2])
                
                if len(buy_agents) > 2:
                    buy_str += f" and {len(buy_agents) - 2} others"
                if len(sell_agents) > 2:
                    sell_str += f" and {len(sell_agents) - 2} others"
                
                factors.append(f"conflicting signals ({buy_str} vs {sell_str})")
            else:
                # More general conflict without direct BUY vs SELL opposition
                factors.append("mixed signals with no clear consensus")
        else:
            # No significant conflict detected
            if confidence >= 70:
                factors.append("strong analyst consensus")
            elif confidence >= 55:
                factors.append("moderate analyst consensus")
            
        # Build core statement with factors
        digest = core
        if factors:
            digest += " with " + " and ".join(factors)
        digest += "."
        
        # Add trade context
        if trade_type == TradeType.SCALP:
            if confidence >= 70:
                digest += " Quick in-and-out scalp"
            else:
                digest += " Higher-risk scalp entry"
        elif trade_type == TradeType.SWING:
            if confidence >= 70:
                digest += " Multi-day swing setup"
            else:
                digest += " Potential swing position"
        elif trade_type == TradeType.TREND_FOLLOWING:
            digest += " Trend continuation confirmed"
        elif trade_type == TradeType.MEAN_REVERSION:
            digest += " Counter-trend reversion play"
        
        # Add agent insights if available
        agent_insights = []
        
        # Extract technical signals from reason_summary
        if reason_summary and isinstance(reason_summary, list):
            technical_agent = None
            sentiment_agent = None
            liquidity_agent = None
            
            # Find relevant agents in reason_summary
            for agent_data in reason_summary:
                if not isinstance(agent_data, dict):
                    continue
                    
                agent_name = agent_data.get('agent', '')
                agent_reason = agent_data.get('reason', '')
                
                if 'Technical' in agent_name and agent_reason:
                    technical_agent = agent_data
                elif 'Sentiment' in agent_name and agent_reason:
                    sentiment_agent = agent_data
                elif 'Liquidity' in agent_name and agent_reason:
                    liquidity_agent = agent_data
            
            # Add technical insight
            if technical_agent:
                if 'RSI' in technical_agent.get('reason', ''):
                    if 'oversold' in technical_agent.get('reason', '').lower():
                        agent_insights.append('RSI oversold')
                    elif 'overbought' in technical_agent.get('reason', '').lower():
                        agent_insights.append('RSI overbought')
                
                if 'MACD' in technical_agent.get('reason', ''):
                    if 'cross' in technical_agent.get('reason', '').lower():
                        agent_insights.append('MACD crossover')
            
            # Add sentiment insight
            if sentiment_agent:
                if 'bullish' in sentiment_agent.get('reason', '').lower():
                    agent_insights.append('sentiment bullish')
                elif 'bearish' in sentiment_agent.get('reason', '').lower():
                    agent_insights.append('sentiment bearish')
            
            # Add liquidity insight
            if liquidity_agent:
                if 'support' in liquidity_agent.get('reason', '').lower():
                    agent_insights.append('liquidity support strong')
                elif 'resistance' in liquidity_agent.get('reason', '').lower():
                    agent_insights.append('resistance overhead')
        
        # Add tag-based insights
        if tags and isinstance(tags, list):
            if 'breakout' in tags:
                agent_insights.append('breakout confirmed')
            if 'trend_continuation' in tags:
                agent_insights.append('trend aligned')
            if 'tight_range' in tags:
                agent_insights.append('low volatility setup')
        
        # Add agent insights to digest
        if agent_insights:
            digest += f" {', '.join(agent_insights[:2])}."  # Limit to top 2 insights
        
        # Add risk assessment in a more concise format
        if risk_snapshot:
            r_r_ratio = risk_snapshot.get("risk_reward_ratio")
            if r_r_ratio:
                if r_r_ratio >= 3.0:
                    digest += f" Favors strong {r_r_ratio:.1f}:1 {trade_type} play."
                elif r_r_ratio >= 2.0:
                    digest += f" Favorable {r_r_ratio:.1f}:1 {trade_type} setup."
                elif r_r_ratio >= 1.5:
                    digest += f" Acceptable {r_r_ratio:.1f}:1 {trade_type} opportunity."
                else:
                    digest += f" Tight {r_r_ratio:.1f}:1 {trade_type} with caution."
            else:
                digest += f" Consider {trade_type} approach."  # End with period if no R:R available
        
        # Add conflict prefix if necessary
        return conflict_prefix + digest

    def log_trade_plan_summary(self, trade_plan: Dict[str, Any]) -> None:
        """
        Log a formatted, human-readable summary of the trade plan.
        
        This method prints a well-structured summary of the trade plan, highlighting
        key information and formatting it for easy reading in terminal logs.
        
        Args:
            trade_plan: The complete trade plan dictionary
        """
        if not trade_plan:
            logger.info("❌ No valid trade plan to log")
            return
            
        # Get trade_type and convert to string if it's an enum
        trade_type = trade_plan.get('trade_type')
        if trade_type is not None and hasattr(trade_type, 'value'):  # Check if it's an enum
            trade_type = trade_type.value
            
        # Format symbol if available
        symbol = trade_plan.get('symbol', 'UNKNOWN')
        interval = trade_plan.get('interval', '1h')
        symbol_display = f"{symbol} ({interval})" if interval else symbol
        
        # Get signal and confidence
        signal = trade_plan.get('signal', 'UNKNOWN')
        confidence = trade_plan.get('confidence', 0)
        normalized_confidence = trade_plan.get('normalized_confidence', confidence)
        
        # Calculate price distances if possible
        entry_price = trade_plan.get('entry_price')
        stop_loss = trade_plan.get('stop_loss')
        take_profit = trade_plan.get('take_profit')
        
        sl_distance = ""
        tp_distance = ""
        
        if entry_price and entry_price > 0:
            # Format stop loss with distance percentage
            if stop_loss and stop_loss > 0:
                sl_percent = ((stop_loss - entry_price) / entry_price) * 100
                sl_direction = "↓" if sl_percent < 0 else "↑"
                sl_distance = f" ({sl_direction} {sl_percent:.2f}%)"
                
            # Format take profit with distance percentage
            if take_profit and take_profit > 0:
                tp_percent = ((take_profit - entry_price) / entry_price) * 100
                tp_direction = "↑" if tp_percent > 0 else "↓"
                tp_distance = f" ({tp_direction} {tp_percent:.2f}%)"
        
        # Get fallback information
        fallback_plan = trade_plan.get('fallback_plan', {})
        entry_fallback = fallback_plan.get('entry', {}).get('used', False) if isinstance(fallback_plan, dict) else False
        sl_fallback = fallback_plan.get('stop_loss', {}).get('used', False) if isinstance(fallback_plan, dict) else False
        tp_fallback = fallback_plan.get('take_profit', {}).get('used', False) if isinstance(fallback_plan, dict) else False
        
        # Format entry_fallback_reason
        entry_fallback_reason = fallback_plan.get('entry', {}).get('reason', '') if isinstance(fallback_plan, dict) else ''
        sl_fallback_reason = fallback_plan.get('stop_loss', {}).get('reason', '') if isinstance(fallback_plan, dict) else ''
        tp_fallback_reason = fallback_plan.get('take_profit', {}).get('reason', '') if isinstance(fallback_plan, dict) else ''
        
        # Get risk metrics
        risk_snapshot = trade_plan.get('risk_snapshot', {})
        rr_ratio = risk_snapshot.get('risk_reward_ratio', 0) if isinstance(risk_snapshot, dict) else 0
        portfolio_risk = risk_snapshot.get('portfolio_risk_percent', 0) if isinstance(risk_snapshot, dict) else 0
        
        # Get other details
        position_size = trade_plan.get('position_size', 0)
        valid_until = trade_plan.get('valid_until', '')
        plan_digest = trade_plan.get('plan_digest', '')
        conflict_score = trade_plan.get('conflict_score', 0)
        
        # Format tags
        tags = trade_plan.get('tags', [])
        tags_str = f"{tags}" if tags else "None"
        
        # Get contributing agents
        contributing_agents = trade_plan.get('contributing_agents', [])
        
        # Get reason summary
        reason_summary = trade_plan.get('reason_summary', [])
        
        # Format top 3 contributors by confidence
        top_contributors = []
        if isinstance(reason_summary, list):
            # Sort by confidence descending
            sorted_contributors = sorted(reason_summary, 
                                      key=lambda x: x.get('confidence', 0) if isinstance(x, dict) else 0, 
                                      reverse=True)
            top_contributors = sorted_contributors[:3]  # Take top 3
        
        # Start building the output
        logger.info(f"✅ Trade Plan Summary — {symbol_display}")
        logger.info("")
        
        # Core trade details
        logger.info(f"- Signal:        {signal} (Confidence: {normalized_confidence}%)")
        
        # Price levels
        if entry_price:
            logger.info(f"- Entry:         {entry_price:.2f}")
        else:
            logger.info(f"- Entry:         Not specified")
            
        if stop_loss:
            logger.info(f"- Stop-Loss:     {stop_loss:.2f}{sl_distance}")
        else:
            logger.info(f"- Stop-Loss:     Not specified")
            
        if take_profit:
            logger.info(f"- Take-Profit:   {take_profit:.2f}{tp_distance}")
        else:
            logger.info(f"- Take-Profit:   Not specified")
        
        # Risk metrics
        logger.info(f"- R:R Ratio:     {rr_ratio:.2f}")
        logger.info(f"- Portfolio Risk: {portfolio_risk:.1f}%")
        logger.info(f"- Position Size:  {position_size:.4f}")
        
        # Trade info
        if trade_type:
            logger.info(f"- Trade Type:     {trade_type}")
        
        logger.info(f"- Tags:          {tags_str}")
        
        if valid_until:
            logger.info(f"- Valid Until:   {valid_until}")
            
        logger.info("")
        
        # Agent consensus section
        logger.info("📊 Agent Consensus:")
        if top_contributors:
            for contributor in top_contributors:
                if isinstance(contributor, dict):
                    agent = contributor.get('agent', 'Unknown')
                    action = contributor.get('action', 'UNKNOWN')
                    conf = contributor.get('confidence', 0)
                    reason = contributor.get('reason', '')
                    
                    reason_display = f" → \"{reason}\"" if reason else ""
                    logger.info(f"- {agent:<25} → {action} ({conf}%){reason_display}")
        else:
            logger.info("- No agent details available")
            
        logger.info("")
        
        # Warning for conflict or low confidence
        if conflict_score and conflict_score > 0:
            if conflict_score > 50:
                logger.info(f"⚠️ Conflict Score: {conflict_score}% (HIGH divergence, position size reduced by {int(conflict_score * 0.7)}%)")
            elif conflict_score > 30:
                logger.info(f"⚠️ Conflict Score: {conflict_score}% (moderate divergence, position size reduced by {int(conflict_score * 0.7)}%)")
            else:
                logger.info(f"ℹ️ Conflict Score: {conflict_score}% (minor divergence, position size reduced by {int(conflict_score * 0.7)}%)")
            
            # Show conflicting agents
            opposing_signals = {}
            if isinstance(reason_summary, list):
                for agent_data in reason_summary:
                    if isinstance(agent_data, dict):
                        action = agent_data.get('action')
                        if action and action != signal:  # Different from final signal
                            if action not in opposing_signals:
                                opposing_signals[action] = []
                            opposing_signals[action].append(agent_data)
                
                # Show top opposing agent for each signal
                for oppose_signal, agents in opposing_signals.items():
                    if agents:
                        # Take highest confidence agent for this signal
                        top_agent = max(agents, key=lambda x: x.get('confidence', 0) if isinstance(x, dict) else 0)
                        agent_name = top_agent.get('agent', 'Unknown')
                        confidence = top_agent.get('confidence', 0)
                        logger.info(f"  {agent_name} suggests {oppose_signal} ({confidence}%)")
                        
        elif normalized_confidence and normalized_confidence < 60:
            logger.info(f"⚠️ Low Confidence Plan: {normalized_confidence}%")
            logger.info("  Consider skipping or reducing position size")
        
        # Fallback heuristics used
        logger.info(f"📌 Fallback Heuristics Used:")
        if entry_fallback or sl_fallback or tp_fallback:
            if entry_fallback:
                logger.info(f"  Entry: Yes - {entry_fallback_reason}")
            if sl_fallback:
                logger.info(f"  Stop-Loss: Yes - {sl_fallback_reason}")
            if tp_fallback:
                logger.info(f"  Take-Profit: Yes - {tp_fallback_reason}")
        else:
            logger.info("  No")
        
        # Execution and version details
        logger.info("")
        logger.info(f"⚙️ Execution Details:")
        logger.info(f"  Execution Time: {trade_plan.get('execution_time_seconds', 0):.4f} seconds")
        logger.info(f"  Plan Version: {trade_plan.get('version', '1.0.0')}")
        logger.info(f"  Agent Version: {self.__class__.__name__} v{trade_plan.get('agent_version', '0.2.0')}")
        
        # Trade type rationale
        trade_type = trade_plan.get('trade_type')
        if trade_type:
            logger.info("")
            logger.info(f"🔍 Trade Type: {trade_type}")
            confidence = trade_plan.get('confidence', 0)
            
            # Add rationale for trade type classification
            if trade_type == TradeType.SCALP.value:
                logger.info(f"  Classified as scalp due to short timeframe and/or high volatility")
            elif trade_type == TradeType.SWING.value:
                logger.info(f"  Classified as swing trade with medium-term horizon (confidence: {confidence}%)")
            elif trade_type == TradeType.TREND_FOLLOWING.value:
                logger.info(f"  Classified as trend-following based on high confidence ({confidence}%) and aligned indicators")
            elif trade_type == TradeType.MEAN_REVERSION.value:
                logger.info(f"  Classified as mean-reversion based on overextended metrics and reversal signals")
            
        # Plan digest if available
        if plan_digest:
            logger.info(f"\n💡 {plan_digest}")
            
        logger.info("\n" + "-" * 50)
        
        # If detailed logging is enabled, log full calculation steps
        if self.detailed_logging or self.test_mode:
            self._log_detailed_calculations(trade_plan)
            
        # Write to log file in logs/trade_plans directory
        self._write_trade_plan_log(trade_plan)
            
    def _log_detailed_calculations(self, trade_plan: Dict[str, Any]) -> None:
        """
        Log detailed calculation steps for debugging and analysis.
        Only used when detailed_logging=True or test_mode=True.
        
        Args:
            trade_plan: The complete trade plan dictionary
        """
        if not (self.detailed_logging or self.test_mode):
            return
            
        logger.info("\n🔍 DETAILED CALCULATION STEPS:")
        
        # Log entry price determination
        entry_price = trade_plan.get('entry_price')
        fallback_plan = trade_plan.get('fallback_plan', {})
        
        if entry_price:
            logger.info(f"Entry Price Determination:")
            entry_fallback = fallback_plan.get('entry', {}).get('used', False) if isinstance(fallback_plan, dict) else False
            entry_reason = fallback_plan.get('entry', {}).get('reason', '') if isinstance(fallback_plan, dict) else ''
            
            if entry_fallback:
                logger.info(f"  → Used fallback: {entry_reason}")
            else:
                logger.info("  → Used primary method (liquidity-based or custom)")
        
        # Log stop loss calculation
        stop_loss = trade_plan.get('stop_loss')
        if stop_loss:
            logger.info(f"Stop Loss Determination:")
            sl_fallback = fallback_plan.get('stop_loss', {}).get('used', False) if isinstance(fallback_plan, dict) else False
            sl_reason = fallback_plan.get('stop_loss', {}).get('reason', '') if isinstance(fallback_plan, dict) else ''
            
            if sl_fallback:
                logger.info(f"  → Used fallback: {sl_reason}")
            else:
                logger.info("  → Used primary method (liquidity-based or custom)")
                
        # Log take profit calculation
        take_profit = trade_plan.get('take_profit')
        if take_profit:
            logger.info(f"Take Profit Determination:")
            tp_fallback = fallback_plan.get('take_profit', {}).get('used', False) if isinstance(fallback_plan, dict) else False
            tp_reason = fallback_plan.get('take_profit', {}).get('reason', '') if isinstance(fallback_plan, dict) else ''
            
            if tp_fallback:
                logger.info(f"  → Used fallback: {tp_reason}")
            else:
                logger.info("  → Used primary method (liquidity-based or custom)")
                
        # Log position sizing calculation
        position_size = trade_plan.get('position_size')
        if position_size:
            logger.info(f"Position Sizing:")
            confidence = trade_plan.get('confidence', 0)
            
            # Determine tier that would have been used
            tier = "low"
            if confidence >= self.confidence_tiers["high"]:
                tier = "high"
            elif confidence >= self.confidence_tiers["medium"]:
                tier = "medium"
                
            tier_multiplier = self.position_size_multipliers.get(tier, 0)
            logger.info(f"  → Confidence: {confidence}% (Tier: {tier}, Multiplier: {tier_multiplier})")
            
            # Check if conflict reduction was applied
            conflict_score = trade_plan.get('conflict_score')
            if conflict_score and conflict_score > 0:
                # Calculate original position size before conflict reduction
                max_reduction = 0.7  # Same as in _calculate_position_size
                reduction_pct = (conflict_score / 100) * max_reduction
                # Reverse the calculation to get original position size
                estimated_original = position_size / (1 - reduction_pct)
                logger.info(f"  → Conflict reduction: {conflict_score}% conflict score reduced position by {reduction_pct:.2%}")
                logger.info(f"  → Pre-conflict position: {estimated_original:.4f} → Post-conflict: {position_size:.4f}")
            else:
                logger.info(f"  → Final position size: {position_size}")
            
        # Log agent weight calculations if available
        decision_trace = trade_plan.get('decision_trace', {})
        if decision_trace and isinstance(decision_trace, dict):
            logger.info(f"Agent Weight Distribution:")
            weights = decision_trace.get('weights', {})
            if weights and isinstance(weights, dict):
                for agent, weight in weights.items():
                    logger.info(f"  → {agent}: {weight}")
            
            logger.info(f"Signal Scores:")
            scores = decision_trace.get('scores', {})
            if scores and isinstance(scores, dict):
                for signal, score in scores.items():
                    logger.info(f"  → {signal}: {score}")
                    
    def _write_trade_plan_log(self, trade_plan: Dict[str, Any]) -> None:
        """
        Write trade plan details to a log file for persistent review.
        
        Args:
            trade_plan: The complete trade plan dictionary
        """
        if not trade_plan:
            return
            
        try:
            # Create a unique filename with timestamp and symbol
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            symbol = trade_plan.get('symbol', 'UNKNOWN').replace('/', '_')
            filename = f"{timestamp}_{symbol}_plan.log"
            log_path = os.path.join(self.log_dir, filename)
            
            # Format the content similar to the terminal output
            with open(log_path, 'w') as f:
                # Use the same format as terminal output but write to file
                f.write(f"Trade Plan Summary — {symbol}\n\n")
                
                # Core trade details
                f.write(f"Signal: {trade_plan.get('signal')} (Confidence: {trade_plan.get('normalized_confidence', 0)}%)\n")
                f.write(f"Entry: {trade_plan.get('entry_price')}\n")
                f.write(f"Stop-Loss: {trade_plan.get('stop_loss')}\n")
                f.write(f"Take-Profit: {trade_plan.get('take_profit')}\n")
                
                # Risk metrics
                risk_snapshot = trade_plan.get('risk_snapshot', {})
                f.write(f"R:R Ratio: {risk_snapshot.get('risk_reward_ratio', 0) if isinstance(risk_snapshot, dict) else 0}\n")
                f.write(f"Portfolio Risk: {risk_snapshot.get('portfolio_risk_percent', 0) if isinstance(risk_snapshot, dict) else 0}%\n")
                f.write(f"Position Size: {trade_plan.get('position_size', 0)}\n\n")
                
                # Add raw trade plan JSON for reference
                f.write("Raw Trade Plan:\n")
                f.write(json.dumps(trade_plan, indent=2))
                
                # Add execution metrics
                execution_time = trade_plan.get('execution_time_seconds', 0)
                if execution_time:
                    f.write(f"\n\nExecution Time: {execution_time:.4f} seconds")
                    f.write(f"\nPlan Version: {trade_plan.get('version', '1.0.0')}")
                    f.write(f"\nAgent Version: {self.__class__.__name__} v{trade_plan.get('agent_version', '0.2.0')}")
                
            logger.debug(f"Trade plan log written to {log_path}")
        except Exception as e:
            logger.warning(f"Failed to write trade plan log: {str(e)}")
            
    def build_error_response(self, error_type: str, message: str) -> Dict[str, Any]:
        """
        Build a standardized error response.
        
        Args:
            error_type: Type of error
            message: Error message
            
        Returns:
            Error response dictionary
        """
        # Create a structured fallback plan object
        fallback_plan = {
            "entry": False,
            "stop_loss": False,
            "take_profit": False
        }
        
        # Create an empty summary confidence object
        summary_confidence = {
            "average": 0,
            "weighted": 0,
            "directional": 0
        }
        
        return {
            "status": "error",
            "error": True,
            "error_type": error_type or "UNKNOWN_ERROR",
            "message": message,
            "error_message": message,
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "signal": "UNKNOWN" if error_type == "INSUFFICIENT_DATA" else "HOLD",
            "action": "HOLD",
            "confidence": 0,
            "summary_confidence": summary_confidence,
            "fallback_plan": fallback_plan,
            "plan_digest": f"Error: {message}"
        }


# Note: This factory function is implemented at the module level to avoid name conflicts
# with the method defined inside the TradeType enum class.
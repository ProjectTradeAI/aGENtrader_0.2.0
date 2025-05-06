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

class TradePlanAgent(\1):
    """TradePlanAgent for aGENtrader v0.2.2"""
\2def __init__(self\3):\4    self.version = "v0.2.2"
        super().__init__()
        self.name = "TradePlanAgent"
        self._description = "Generates detailed trade execution plans"
        self.agent_name = "trade_plan_agent"
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Load configuration or use defaults
        self.config = config or {}
        
        # Load risk parameters from config or use defaults
        self.risk_reward_ratio = self.config.get("risk_reward_ratio", 1.5)
        self.max_position_size = self.config.get("max_position_size", 1.0)
        self.min_position_size = self.config.get("min_position_size", 0.1)
        self.portfolio_risk_per_trade = self.config.get("portfolio_risk_per_trade", 0.02)  # 2% risk per trade
        
        # Portfolio Manager integration
        self.portfolio_manager = None
        self.portfolio_info = None  # Will store portfolio state when retrieved
        self.use_portfolio_manager = self.config.get("use_portfolio_manager", True)
        
        # Initialize portfolio manager if enabled
        if self.use_portfolio_manager:
            self._init_portfolio_manager()
        
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
        
        # Decision consistency configuration
        self.allow_fallback_on_hold = self.config.get("allow_fallback_on_hold", False)
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
        
        # Initialize portfolio manager if enabled
        if self.use_portfolio_manager:
            self._init_portfolio_manager()
        
        logger.info(f"Trade plan agent initialized with risk:reward ratio {self.risk_reward_ratio}")
        
    def _init_portfolio_manager(self):
        """
        Initialize the portfolio manager agent for portfolio-aware trade planning.
        """
        try:
            from agents.portfolio_manager_agent import PortfolioManagerAgent
            self.portfolio_manager = PortfolioManagerAgent()
            self.logger.info("Portfolio manager initialized successfully for trade planning")
        except Exception as e:
            self.logger.warning(f"Could not initialize portfolio manager: {str(e)}")
            self.portfolio_manager = None
            
    def _get_portfolio_state(self) -> Dict[str, Any]:
        """
        Get the current portfolio state from the portfolio manager.
        
        Returns:
            Dictionary containing portfolio information including:
            - total_value: Portfolio total value
            - available_cash: Available cash for new positions
            - total_exposure_pct: Current portfolio exposure percentage
            - asset_exposures: Dictionary of asset-specific exposure percentages
            - open_positions: List of current open positions
            - max_total_exposure_pct: Maximum allowed total exposure
            - max_per_asset_exposure_pct: Maximum allowed exposure per asset
            - position_limits: Position sizing limits
        """
        if self.portfolio_manager is None:
            return {}
            
        try:
            # Get portfolio summary
            portfolio_summary = self.portfolio_manager.get_portfolio_summary()
            
            # Extract key metrics for trade planning
            summary = {
                "total_value": portfolio_summary.get("total_value", 0),
                "available_cash": portfolio_summary.get("available_cash", 0),
                "total_exposure_pct": portfolio_summary.get("total_exposure_pct", 0),
                "asset_exposures": {},
                "open_positions": [],
                "max_total_exposure_pct": getattr(self.portfolio_manager, "max_total_exposure_pct", 80),
                "max_per_asset_exposure_pct": getattr(self.portfolio_manager, "max_per_asset_exposure_pct", 20),
                "position_limits": {
                    "max_concentration": getattr(self.portfolio_manager, "max_concentration", 0.3),
                    "max_positions": getattr(self.portfolio_manager, "max_positions", 10),
                    "active_positions": len(portfolio_summary.get("positions", [])),
                }
            }
            
            # Calculated values for position sizing
            summary["available_exposure_pct"] = summary["max_total_exposure_pct"] - summary["total_exposure_pct"]
            
            # Extract asset exposures
            positions = portfolio_summary.get("positions", [])
            for position in positions:
                if isinstance(position, dict):
                    asset = position.get("symbol", "").split("/")[0] if "/" in position.get("symbol", "") else position.get("symbol", "")
                    exposure_pct = position.get("exposure_pct", 0)
                    
                    if asset:
                        summary["asset_exposures"][asset] = exposure_pct
                        summary["open_positions"].append(position)
            
            # Add allocation statistics
            summary["allocation_stats"] = {
                "total_positions": len(summary["open_positions"]),
                "exposure_distribution": {
                    "high": sum(1 for pct in summary["asset_exposures"].values() if pct > 10),
                    "medium": sum(1 for pct in summary["asset_exposures"].values() if 5 <= pct <= 10),
                    "low": sum(1 for pct in summary["asset_exposures"].values() if pct < 5)
                }
            }
            
            # Log summary for debugging
            self.logger.info(f"Portfolio summary: total value={summary['total_value']:.2f}, " +
                           f"exposure={summary['total_exposure_pct']:.2f}%, " +
                           f"available={summary['available_exposure_pct']:.2f}%, " +
                           f"positions={len(summary['open_positions'])}")
            
            return summary
        except Exception as e:
            self.logger.warning(f"Error getting portfolio state: {str(e)}")
            return {}
    
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
        # Always prioritize final_signal if it exists
        final_decision_signal = decision.get('final_signal', signal)
        # Use final_decision_signal as the primary signal
        signal = final_decision_signal
        confidence = decision.get('confidence', 0)
        
        # Track decision consistency
        decision_consistency = True  # Default to true, will set to false if we override
        
        # Check for HOLD signal explicitly coming from final_signal (strict HOLD policy)
        if final_decision_signal == "HOLD":
            if not self.allow_fallback_on_hold:
                logger.info(f"DecisionAgent returned explicit HOLD. Respecting this decision and not generating a trade plan.")
                signal = "HOLD"  # Enforce HOLD signal
                # Will later generate a minimal plan with position_size = 0
            else:
                # Allow fallback when configured to do so
                logger.info(f"DecisionAgent returned HOLD but allow_fallback_on_hold=True. Will attempt to extract actionable signal.")
                
                # Look for directional bias from decision
                if decision.get('directional_bias') in ["BUY", "SELL"]:
                    logger.info(f"Found directional bias: {decision.get('directional_bias')}")
                    signal = decision.get('directional_bias')
                    decision_consistency = False
                    logger.warning(f"Decision consistency: FALSE - TradePlanAgent overrode DecisionAgent HOLD with {signal}")
                # Otherwise check agent contributions for strong signals
                elif isinstance(decision.get('agent_contributions'), dict):
                    # Collect strong BUY or SELL signals
                    strong_signals = {}
                    for agent, data in decision.get('agent_contributions', {}).items():
                        if isinstance(data, dict) and data.get('signal') in ["BUY", "SELL"] and data.get('confidence', 0) >= 75:
                            signal_type = data.get('signal')
                            if signal_type not in strong_signals:
                                strong_signals[signal_type] = []
                            strong_signals[signal_type].append((agent, data.get('confidence', 0)))
                    
                    # If we have some strong signals
                    if strong_signals:
                        # Find the signal with the most support
                        if len(strong_signals.get("BUY", [])) > len(strong_signals.get("SELL", [])):
                            signal = "BUY"
                        elif len(strong_signals.get("SELL", [])) > len(strong_signals.get("BUY", [])):
                            signal = "SELL"
                        # If tied, use highest confidence
                        elif strong_signals.get("BUY") and strong_signals.get("SELL"):
                            max_buy = max(strong_signals["BUY"], key=lambda x: x[1])
                            max_sell = max(strong_signals["SELL"], key=lambda x: x[1])
                            signal = "BUY" if max_buy[1] > max_sell[1] else "SELL"
                            
                        logger.info(f"Strong {signal} signals found despite HOLD. Using {signal} as fallback signal.")
                        decision_consistency = False
                        logger.warning(f"Decision consistency: FALSE - TradePlanAgent overrode DecisionAgent HOLD with {signal}")
        
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
            
            # Apply override if determined AND we're not enforcing a HOLD from final decision
            if override_signal and override_signal in ["BUY", "SELL"] and signal != "HOLD":
                logger.warning(f"Overriding CONFLICTED signal to {override_signal}")
                logger.info(f"Override reason: {override_reason}")
                signal = override_signal
                
                # Mark decision consistency as false if we're overriding DecisionAgent's final signal
                if signal != final_decision_signal and final_decision_signal != "CONFLICTED":
                    decision_consistency = False
                    logger.warning(f"Decision consistency mismatch: TradePlanAgent {signal} vs DecisionAgent {final_decision_signal}")
                
                # Special check: if DecisionAgent returned CONFLICTED and we kept that signal,
                # ensure decision_consistency is True to reflect that we respected the decision
                # Initialize plan_signal to avoid "unbound" error
                plan_signal = signal
                if final_decision_signal == "CONFLICTED" and plan_signal == "CONFLICTED":
                    decision_consistency = True
                    logger.info("Decision consistency TRUE - TradePlanAgent respecting DecisionAgent's CONFLICTED signal")
            
            # Reduce confidence for conflicted signals
            original_confidence = confidence
            confidence = confidence * 0.85  # Reduce confidence by 15%
            logger.info(f"Reduced confidence from {original_confidence} to {confidence} due to conflict")
        
        # Determine if this is an actionable signal
        is_actionable = signal in ["BUY", "SELL"]
        
        # Get the interval from market data or use default
        interval = market_data.get('interval', '1h')
        
        # Initialize plan_signal at the beginning of the method to avoid unbound variable issues
        plan_signal = signal
        
        # If no actionable signal, return a minimal plan
        if not is_actionable:
            logger.info(f"Non-actionable signal {signal}, generating minimal plan")
            
            # Create minimal plan with additional conflict information if needed
            # Extract symbol from market_data or decision for better reliability
            minimal_symbol = market_data.get('symbol') or decision.get('pair') or decision.get('symbol') or 'UNKNOWN'

            # Calculate summary confidence metrics for minimal plan
            weighted_confidence = decision.get('weighted_confidence', confidence)
            
            # Get directional confidence with proper fallbacks
            directional_confidence_from_decision = decision.get('directional_confidence', 0)
            # Ensure we use the _directional_confidence attribute if it was set earlier in the method
            if hasattr(self, '_directional_confidence') and self._directional_confidence is not None:
                directional_confidence = self._directional_confidence
            else:
                directional_confidence = directional_confidence_from_decision
            
            # Store it for consistent access throughout the class
            self._directional_confidence = directional_confidence
                
            summary_confidence = {
                "average": confidence,
                "weighted": weighted_confidence,
                "directional": directional_confidence
            }
            
            # Set enhanced reasoning for CONFLICTED signals or HOLD signals
            reasoning = "No actionable signal generated"
            
            if is_conflicted:
                if not self.allow_fallback_on_hold:
                    # Clear explanation for CONFLICTED signals converted to HOLD
                    reasoning = "Final action is HOLD due to a CONFLICTED signal. Position size set to 0 to mitigate indecision risk."
                    logger.info(reasoning)
                else:
                    # Explanation for preserved CONFLICTED signals
                    reasoning = "CONFLICTED signal detected. No actionable trade plan generated. Position size set to 0 to mitigate indecision risk."
                    logger.info(reasoning)
            elif signal == "HOLD" and final_decision_signal == "HOLD":
                # Explicit HOLD explanation for respecting DecisionAgent's HOLD signal
                reasoning = "DecisionAgent returned HOLD due to low directional confidence. No trade plan generated."
                logger.info(reasoning)
            
            # For CONFLICTED signals, we need to handle them based on the test expectations
            # If enforcing HOLD for CONFLICTED signals, convert to HOLD; otherwise, preserve CONFLICTED
            if original_signal == "CONFLICTED" or decision.get('final_signal') == "CONFLICTED":
                if not self.allow_fallback_on_hold:
                    # When we're enforcing strict HOLD policy, CONFLICTED should become HOLD
                    plan_signal = "HOLD"
                    logger.info("Converting CONFLICTED signal to HOLD (strict HOLD policy)")
                else:
                    # When allowing fallbacks, preserve CONFLICTED signal
                    plan_signal = "CONFLICTED"
                    logger.info("Preserving CONFLICTED signal (allow_fallback_on_hold=True)")
            else:
                plan_signal = signal
            
            # Extract liquidity information if available
            liquidity_info = None
            if analyst_outputs and "liquidity_analysis" in analyst_outputs:
                liquidity_data = analyst_outputs["liquidity_analysis"]
                if isinstance(liquidity_data, dict):
                    liquidity_info = {
                        "supports": liquidity_data.get("supports"),
                        "resistances": liquidity_data.get("resistances"),
                        "liquidity_zones": liquidity_data.get("liquidity_zones"),
                        "current_zone": liquidity_data.get("current_zone"),
                        "analysis": liquidity_data.get("analysis_summary")
                    }
                
            minimal_plan = {
                "signal": plan_signal,
                "original_signal": original_signal,  # Preserve the original signal
                "confidence": confidence,
                "entry_price": None,
                "stop_loss": None,
                "take_profit": None,
                "position_size": 0,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat(),
                "execution_time_seconds": time.time() - start_time,
                "symbol": minimal_symbol,
                "interval": interval,
                "summary_confidence": summary_confidence,  # Add summary confidence
                "decision_consistency": decision_consistency  # Track decision consistency
            }
            
            # Add liquidity information if available
            if liquidity_info:
                minimal_plan["liquidity_info"] = liquidity_info
            
            # Add conflict flag and fallback information for CONFLICTED signals
            if is_conflicted or original_signal == "CONFLICTED":
                minimal_plan["conflict_flag"] = True
                
                # For explicit CONFLICTED signals, add directional confidence information
                directional_confidence_value = getattr(self, '_directional_confidence', 0)
                directional_confidence_info = f" (directional confidence: {directional_confidence_value}%)"
                
                # Extract conflicting agents if available in the decision
                conflicting_agents = {}
                if isinstance(decision.get('agent_contributions'), dict):
                    for agent_name, data in decision.get('agent_contributions', {}).items():
                        if isinstance(data, dict) and 'signal' in data and 'confidence' in data:
                            # Only consider signals with confidence >= 70
                            if data['confidence'] >= 70:
                                signal_type = data['signal']
                                if signal_type in ["BUY", "SELL"]:  # Only focus on actionable signals
                                    if signal_type not in conflicting_agents:
                                        conflicting_agents[signal_type] = {}
                                    conflicting_agents[signal_type][agent_name] = data['confidence']
                
                # Add conflicting agents information if we have it
                if conflicting_agents and len(conflicting_agents) >= 2:
                    minimal_plan["conflicting_agents"] = conflicting_agents
                elif conflicting_agents:  # Add even with just one direction if it's CONFLICTED
                    minimal_plan["conflicting_agents"] = conflicting_agents
                
                # Always add risk_warning for CONFLICTED signals, even without BUY vs SELL conflict
                risk_warning = "No position opened due to high-confidence conflict between "
                
                if "BUY" in conflicting_agents and "SELL" in conflicting_agents:
                    risk_warning += "BUY and SELL signals. Market is indecisive."
                else:
                    # Generic fallback if we don't have clear BUY/SELL conflict
                    risk_warning = "No position opened due to high-confidence conflict between analyst agents. Market is indecisive."
                
                minimal_plan["risk_warning"] = risk_warning
                
                minimal_plan["fallback_plan"] = {
                    "conflict": {
                        "detected": True,
                        "type": "explicit_conflict",
                        "reason": f"⚠️ EXPLICIT CONFLICT DETECTED - applying aggressive 70% position reduction{directional_confidence_info}",
                        "original_signal": original_signal,
                        "applied_signal": signal,
                        "position_reduction": "70%",
                        "confidence_reduction": "15%",
                        "directional_confidence": getattr(self, '_directional_confidence', None)
                    }
                }
                minimal_plan["tags"] = ["conflicted", "position_reduced_70pct"]
                
                # Add warning to plan digest for conflicted signals
                warning_message = f"⚠️ EXPLICIT CONFLICT DETECTED: Strong disagreement among analyst agents. Using aggressive position reduction (70%). EXTREME CAUTION required{directional_confidence_info}."
                minimal_plan["plan_digest"] = warning_message
            
            return minimal_plan
        
        # Extract symbol from market_data or decision object for better reliability
        symbol = market_data.get('symbol') or decision.get('pair') or decision.get('symbol') or 'UNKNOWN'
        current_price = self._get_current_price(market_data)
        
        if current_price is None:
            logger.warning(f"Could not determine current price for {symbol}")
            return self.build_error_response(
                "INSUFFICIENT_DATA",
                f"Could not determine current price for {symbol}",
                symbol,
                interval
            )
        
        # Extract historical data for volatility calculations if available
        historical_data = self._extract_historical_data(market_data)
        
        # Get liquidity analysis if available
        liquidity_analysis = None
        if analyst_outputs and "liquidity_analysis" in analyst_outputs:
            liquidity_analysis = analyst_outputs["liquidity_analysis"]
        
        # Determine entry, stop-loss, and take-profit levels with volatility awareness
        # Cast signal to ensure it's a string for type checking
        entry_price, stop_loss, take_profit, used_fallback = self._determine_trade_levels(
            signal=str(signal), 
            current_price=current_price,
            liquidity_analysis=liquidity_analysis,
            historical_data=historical_data,
            interval=interval
        )
        
        # Extract conflict score if available in decision
        conflict_score = decision.get('conflict_score')
        
        # If not provided, calculate it from agent_contributions
        if conflict_score is None and isinstance(decision.get('agent_contributions'), dict):
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
        
        if conflict_score is not None and conflict_score > 0:
            logger.info(f"Using conflict score: {conflict_score}%")
        
        # Extract directional confidence from decision for position size calculation
        directional_confidence = decision.get('directional_confidence')
        if directional_confidence is not None:
            # Store directional confidence as instance attribute for use in _calculate_position_size
            self._directional_confidence = directional_confidence
            logger.info(f"Using directional confidence: {directional_confidence}%")
                
        # Auto-tagging based on logic
        auto_tags = []
        
        # Extract symbol from market data for portfolio-aware position sizing
        symbol = market_data.get('symbol', '')
        
        # Retrieve portfolio state if portfolio manager is enabled
        if self.use_portfolio_manager and self.portfolio_manager is not None:
            self.portfolio_info = self._get_portfolio_state()
            logger.info(f"Retrieved portfolio state for position sizing: {len(self.portfolio_info)} data points")
        else:
            self.portfolio_info = {}
        
        # Calculate position size based on confidence, conflict score, conflict flag, and symbol
        position_size, conflict_type, conflict_handling_applied, confidence_adjustment_reason, portfolio_risk_exceeded = self._calculate_position_size(
            confidence=confidence, 
            conflict_score=conflict_score, 
            is_conflicted=is_conflicted, 
            symbol=symbol
        )
        
        # Add conflict tag if applicable
        if conflict_type:
            auto_tags.append(conflict_type)
        
        # Generate reason summary
        structured_reason_summary = self._generate_reason_summary(decision, analyst_outputs)
        
        # Determine validity period
        valid_until = self._calculate_validity_period(interval, confidence, historical_data)
        
        # Classify trade type
        trade_type = self._classify_trade_type(
            str(signal), confidence, valid_until, historical_data, interval
        )
        
        # Position size is already a float value, not a tuple
        position_size_value = position_size
        
        # Calculate risk metrics
        risk_snapshot = self._calculate_risk_snapshot(
            str(signal), entry_price, stop_loss, take_profit, position_size_value, current_price
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
        if conflict_handling_applied:
            # New enhanced conflict handling
            if conflict_type == "conflicted":
                fallback_plan["conflict"] = {
                    "detected": True,
                    "type": "high_conflict",
                    "reason": "⚠️ HIGH CONFLICT DETECTED - reducing position size by 50% due to significant signal disagreement",
                    "original_signal": original_signal,
                    "applied_signal": signal,
                    "position_reduction": "50%",
                    "confidence_reduction": "15%",
                    "conflict_score": conflict_score
                }
            elif conflict_type == "soft_conflict":
                fallback_plan["conflict"] = {
                    "detected": True,
                    "type": "soft_conflict",
                    "reason": "⚠️ SOFT CONFLICT DETECTED - reducing position size by 20% due to moderate signal disagreement",
                    "original_signal": original_signal,
                    "applied_signal": signal,
                    "position_reduction": "20%",
                    "confidence_reduction": "10%",
                    "conflict_score": conflict_score
                }
        elif is_conflicted:
            # Enhanced conflict handling for explicit CONFLICTED signals
            directional_confidence_value = getattr(self, '_directional_confidence', 0)
            directional_confidence_info = f" (directional confidence: {directional_confidence_value}%)"
            
            fallback_plan["conflict"] = {
                "detected": True,
                "type": "explicit_conflict",
                "reason": f"⚠️ EXPLICIT CONFLICT DETECTED - applying aggressive 70% position reduction{directional_confidence_info}",
                "original_signal": original_signal,
                "applied_signal": signal,
                "position_reduction": "70%",
                "confidence_reduction": "20%",
                "conflict_score": conflict_score,
                "directional_confidence": getattr(self, '_directional_confidence', None)
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
        
        # Add appropriate conflict tags
        if conflict_handling_applied:
            if conflict_type == "conflicted":
                auto_tags.append("conflicted")  # Ensure the conflicted tag is always added
                auto_tags.append("high_conflict")
                auto_tags.append("position_reduced_50pct")
            elif conflict_type == "soft_conflict":
                auto_tags.append("soft_conflict")
                auto_tags.append("position_reduced_20pct")
        elif is_conflicted:
            # Legacy conflict handling
            auto_tags.append("conflicted")
            auto_tags.append("position_reduced_70pct")  # Add tag for aggressive 70% reduction
        
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
            
        # Add trade strategy tags based on market conditions (from analyst outputs)
        # Ensure signal is a valid string to avoid type errors
        signal_for_tags = signal if signal in ["BUY", "SELL", "HOLD"] else "HOLD"
        trade_strategy_tags = self._generate_strategy_tags(signal_for_tags, analyst_outputs, historical_data)
        auto_tags.extend(trade_strategy_tags)
        
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
        # Ensure we use the _directional_confidence attribute if it was set earlier in the method
        if hasattr(self, '_directional_confidence') and self._directional_confidence is not None:
            directional_confidence = self._directional_confidence
            
        summary_confidence = {
            "average": confidence,
            "weighted": weighted_confidence,
            "directional": directional_confidence
        }
        
        # Generate a human-readable plan digest
        # Store portfolio_info for access in other methods
        portfolio_info = getattr(self, 'portfolio_info', {})
        
        plan_digest = self._generate_plan_digest(
            signal=str(signal),  # Cast to string for type safety
            confidence=confidence,
            liquidity_used="liquidity_based_entry" in unique_tags,
            high_conflict="high_conflict" in unique_tags,
            trade_type=trade_type,
            risk_snapshot=risk_snapshot,
            reason_summary=structured_reason_summary,
            tags=unique_tags,
            agent_contributions=decision.get('agent_contributions', {}),
            is_conflicted=is_conflicted,  # Pass the conflict flag
            conflict_type=conflict_type,  # Pass the conflict type (soft_conflict or conflicted)
            conflict_handling_applied=conflict_handling_applied,  # Whether position size was adjusted
            conflict_score=conflict_score,  # Pass the specific conflict score percentage
            confidence_adjustment_reason=confidence_adjustment_reason,  # Include confidence adjustment reasoning
            portfolio_info=portfolio_info  # Include portfolio state information
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
        
        # Check for tag conflicts and generate mood clarification
        mood_clarification = self._detect_tag_conflicts()
        if mood_clarification:
            # If a mood clarification exists, log it
            logger.info(f"[MOOD CLARIFICATION] {mood_clarification}")
            
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
            "final_signal": plan_signal,  # The transformed signal after processing (e.g., CONFLICTED → HOLD)
            "confidence": confidence,
            "normalized_confidence": normalized_confidence,
            "summary_confidence": summary_confidence,
            "conflict_score": conflict_score,
            "conflict_flag": is_conflicted,  # Explicit flag for conflict detection
            "conflict_type": conflict_type,  # Type of conflict (soft_conflict, conflicted, etc.)
            "decision_consistency": decision_consistency,  # Track if we're consistent with DecisionAgent
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_size": position_size_value,
            "conflict_handling_applied": conflict_handling_applied,
            
            # Confidence adjustment reasoning (new)
            "confidence_adjustment_reason": confidence_adjustment_reason,
            
            # Analysis and reasoning
            "reasoning": decision.get('reasoning', 'No reasoning provided'),
            "reason_summary": structured_reason_summary,  # Now using structured format
            "contributing_agents": contributing_agents,
            
            # Add conflicting agents information if available
            "conflicting_agents": self._extract_conflicting_agents(decision) if is_conflicted or conflict_type in ["conflicted", "soft_conflict"] else {},
            
            # Add risk warning for conflicted scenarios
            "risk_warning": self._generate_risk_warning(is_conflicted, conflict_type, decision) if is_conflicted or conflict_type in ["conflicted", "soft_conflict"] else None,
            "risk_feedback": self._generate_risk_feedback(is_conflicted, conflict_type, position_size_value, portfolio_risk_exceeded),
            
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
            "mood_clarification": mood_clarification,  # Add mood tag conflict clarification
            
            # Portfolio information if available
            "portfolio_info": getattr(self, 'portfolio_info', {}),
            
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
            # Also update decision_consistency since we're overriding the DecisionAgent
            trade_plan["decision_consistency"] = False
            logger.warning(f"Decision consistency: FALSE - TradePlanAgent overrode DecisionAgent signal")
        
        logger.info(f"Trade plan generated for {signal} {symbol} with position size {position_size_value}")
        
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
    
    def _calculate_position_size(self, confidence: float, conflict_score: Optional[int] = None, 
                          is_conflicted: bool = False, symbol: str = "") -> Tuple[float, str, bool, Dict[str, Any], bool]:
        """
        Calculate position size based on confidence level, conflict score, and portfolio state.
        
        Args:
            confidence: Decision confidence percentage
            conflict_score: Optional conflict score (0-100) indicating level of disagreement between agents
            is_conflicted: Boolean flag indicating if the signal is explicitly CONFLICTED
            symbol: Trading symbol for portfolio-aware position sizing
            
        Returns:
            Tuple containing:
            - Position size multiplier (0.0 to 1.0)
            - Conflict type: None, "soft_conflict", or "conflicted"
            - Boolean indicating if conflict handling was applied
            - Dictionary containing confidence adjustment reasoning
            - Boolean indicating if portfolio risk limits were exceeded
        """
        # Initialize detailed reasoning dictionary
        confidence_adjustment_reason = {
            "base_position_tier": "",
            "base_size": 0.0,
            "original_position_size": 0.0,
            "adjusted_position_size": 0.0,
            "directional_adjustment": None,
            "conflict_adjustment": None,
            "final_size": 0.0,
            "explanation": "",
            "adjustment_factors": {},
            "agent_disagreements": []
        }
        
        # Determine confidence tier
        if confidence >= self.confidence_tiers["high"]:
            tier = "high"
        elif confidence >= self.confidence_tiers["medium"]:
            tier = "medium"
        elif confidence >= self.confidence_tiers["low"]:
            tier = "low"
        else:
            # Below minimum confidence threshold
            confidence_adjustment_reason.update({
                "explanation": "Confidence below minimum threshold, position size set to 0"
            })
            return 0.0, "", False, confidence_adjustment_reason, False
        
        # Get position size multiplier for the tier
        position_size = self.position_size_multipliers[tier]
        original_size = position_size
        conflict_type = ""
        conflict_handling_applied = False
        
        # Record base position info
        confidence_adjustment_reason.update({
            "base_position_tier": tier,
            "base_size": position_size,
            "original_position_size": position_size,
            "adjustment_factors": {
                "base_confidence": f"Base confidence ({confidence:.1f}%) → {tier} tier: {position_size:.2f}"
            }
        })
        
        # Apply enhanced stricter conflict reduction for explicit CONFLICTED signals
        if is_conflicted:
            # For explicit CONFLICTED signals, apply a more aggressive 70% reduction (only 30% of normal size)
            prev_size = position_size
            position_size = position_size * 0.3  # 70% reduction
            logger.warning(f"⚠️ Applying 70% position reduction for CONFLICTED signal: {prev_size:.2f} → {position_size:.2f}")
            conflict_type = "conflicted"
            conflict_handling_applied = True
            
            # Record conflict adjustment
            conflict_reason = f"CONFLICTED signal → 70% reduction"
            confidence_adjustment_reason["adjustment_factors"]["conflict"] = conflict_reason
            confidence_adjustment_reason["conflict_adjustment"] = {
                "conflict_type": "explicit_conflicted",
                "reduction_factor": 0.3,
                "before": prev_size,
                "after": position_size
            }
            
            # Apply directional confidence reduction if available
            directional_confidence = getattr(self, '_directional_confidence', None)
            if directional_confidence is not None and directional_confidence < 60:
                # Further reduce position for low directional confidence
                directional_factor = max(0.5, directional_confidence / 60.0)
                prev_size = position_size
                position_size = position_size * directional_factor
                logger.warning(f"🔻 Further reducing position due to low directional confidence ({directional_confidence}%): {prev_size:.2f} → {position_size:.2f}")
                
                # Record directional adjustment
                directional_reason = f"Low directional confidence ({directional_confidence:.1f}%) → additional {100 * (1-directional_factor):.1f}% reduction"
                confidence_adjustment_reason["adjustment_factors"]["directional"] = directional_reason
                confidence_adjustment_reason["directional_adjustment"] = {
                    "directional_confidence": directional_confidence,
                    "adjustment_factor": directional_factor,
                    "before": prev_size,
                    "after": position_size
                }
        
        # Apply conflict risk reduction based on conflict score thresholds
        elif conflict_score is not None and conflict_score > 0:
            if conflict_score >= 70:
                # Strong conflict: 50% reduction
                prev_size = position_size
                position_size = position_size * 0.5
                logger.warning(f"Applying 50% position reduction for high conflict score ({conflict_score}%): {prev_size:.2f} → {position_size:.2f}")
                conflict_type = "conflicted"
                conflict_handling_applied = True
                
                # Record conflict adjustment
                conflict_reason = f"High conflict score ({conflict_score}%) → 50% reduction"
                confidence_adjustment_reason["adjustment_factors"]["high_conflict"] = conflict_reason
                confidence_adjustment_reason["conflict_adjustment"] = {
                    "conflict_score": conflict_score,
                    "conflict_type": "high_conflict",
                    "reduction_factor": 0.5,
                    "before": prev_size,
                    "after": position_size
                }
                
            elif conflict_score >= 50:
                # Soft conflict: 20% reduction
                prev_size = position_size
                position_size = position_size * 0.8
                logger.info(f"Applying 20% position reduction for soft conflict score ({conflict_score}%): {prev_size:.2f} → {position_size:.2f}")
                conflict_type = "soft_conflict"
                conflict_handling_applied = True
                
                # Record conflict adjustment
                conflict_reason = f"Medium conflict score ({conflict_score}%) → 20% reduction"
                confidence_adjustment_reason["adjustment_factors"]["soft_conflict"] = conflict_reason
                confidence_adjustment_reason["conflict_adjustment"] = {
                    "conflict_score": conflict_score,
                    "conflict_type": "soft_conflict",
                    "reduction_factor": 0.8,
                    "before": prev_size,
                    "after": position_size
                }
                
            else:
                # Minor conflict: scaled reduction
                max_conflict_reduction = 0.7
                conflict_reduction = (conflict_score / 100) * max_conflict_reduction
                reduction_factor = 1 - conflict_reduction
                prev_size = position_size
                position_size = position_size * reduction_factor
                logger.info(f"Applying conflict-based position reduction: {conflict_score}% conflict score reduces position from {prev_size:.2f} to {position_size:.2f}")
                conflict_handling_applied = True
                
                # Record conflict adjustment
                conflict_reason = f"Minor conflict score ({conflict_score}%) → {conflict_reduction*100:.1f}% reduction"
                confidence_adjustment_reason["adjustment_factors"]["minor_conflict"] = conflict_reason
                confidence_adjustment_reason["conflict_adjustment"] = {
                    "conflict_score": conflict_score,
                    "conflict_type": "minor_conflict",
                    "reduction_factor": reduction_factor,
                    "before": prev_size,
                    "after": position_size
                }
        
        # Apply portfolio-based adjustments if portfolio manager is available
        portfolio_adjustment_applied = False
        portfolio_risk_exceeded = False  # New flag to track portfolio risk limits
        self.portfolio_info = {}  # Store as instance attribute for use in other methods
        
        if self.portfolio_manager is not None:
            try:
                # Get portfolio summary 
                portfolio_summary = self._get_portfolio_state()
                
                if portfolio_summary:
                    prev_size = position_size
                    
                    # Check total exposure limit
                    total_exposure = portfolio_summary.get("total_exposure_pct", 0)
                    max_exposure = self.portfolio_manager.max_total_exposure_pct
                    available_exposure = max_exposure - total_exposure
                    
                    # Extract asset name from symbol
                    asset = ""
                    if "/" in symbol:
                        asset = symbol.split("/")[0]
                    else:
                        # Try to extract using base currency
                        symbol_parts = symbol.replace("/", "").split(self.portfolio_manager.base_currency)
                        if len(symbol_parts) > 0:
                            asset = symbol_parts[0]
                    
                    # Store portfolio info for logging and later use
                    self.portfolio_info = {
                        "total_value": portfolio_summary.get("total_value", 0),
                        "available_cash": portfolio_summary.get("available_cash", 0),
                        "total_exposure_pct": total_exposure,
                        "max_exposure_pct": max_exposure,
                        "available_exposure_pct": available_exposure,
                        "asset": asset
                    }
                    
                    # Local reference for this method
                    portfolio_info = self.portfolio_info
                    
                    logger.info(f"Portfolio state: total value={portfolio_info['total_value']:.2f}, " +
                               f"available cash={portfolio_info['available_cash']:.2f}, " +
                               f"current exposure={total_exposure:.2f}%, max={max_exposure:.2f}%")
                    
                    # If we have a valid asset, check asset-specific exposure
                    if asset:
                        asset_exposure = portfolio_summary.get("asset_exposures", {}).get(asset, 0)
                        asset_max_exposure = self.portfolio_manager.max_per_asset_exposure_pct
                        available_asset_exposure = asset_max_exposure - asset_exposure
                        
                        # Add to portfolio info
                        portfolio_info.update({
                            "asset_exposure_pct": asset_exposure,
                            "asset_max_exposure_pct": asset_max_exposure,
                            "asset_available_exposure_pct": available_asset_exposure
                        })
                        
                        logger.info(f"Asset {asset} exposure: current={asset_exposure:.2f}%, " +
                                   f"max={asset_max_exposure:.2f}%, available={available_asset_exposure:.2f}%")
                        
                        # Choose the more restrictive limit
                        portfolio_max_size = min(available_exposure, available_asset_exposure) / 100
                        
                        # Apply portfolio limit if needed
                        if portfolio_max_size < position_size and portfolio_max_size > 0:
                            prev_position = position_size
                            position_size = min(position_size, portfolio_max_size)
                            portfolio_adjustment_applied = True
                            portfolio_risk_exceeded = True  # Set the portfolio risk exceeded flag
                            
                            adjustment_reason = f"Portfolio limit: {available_exposure:.1f}% total, {available_asset_exposure:.1f}% {asset}"
                            confidence_adjustment_reason["adjustment_factors"]["portfolio_limit"] = adjustment_reason
                            
                            # Add portfolio adjustment details
                            confidence_adjustment_reason["portfolio_adjustment"] = {
                                "type": "exposure_limit",
                                "before": prev_position,
                                "after": position_size,
                                "total_exposure_pct": total_exposure,
                                "max_exposure_pct": max_exposure,
                                "asset_exposure_pct": asset_exposure,
                                "asset_max_exposure_pct": asset_max_exposure,
                                "limiting_factor": "asset" if available_asset_exposure < available_exposure else "total"
                            }
                            
                            logger.warning(f"📊 Applied portfolio limit: reducing position from {prev_position:.2f} to {position_size:.2f} " +
                                          f"due to {portfolio_max_size*100:.1f}% available exposure")
                    else:
                        logger.info(f"Could not extract asset from symbol: {symbol}")
            except Exception as e:
                self.logger.warning(f"Error applying portfolio adjustments: {str(e)}")
        
        # Ensure position size is within limits
        prev_size = position_size
        position_size = max(min(position_size, self.max_position_size), self.min_position_size)
        
        # If position size was limited, record it
        if position_size != prev_size:
            if position_size == self.max_position_size:
                limit_reason = f"Maximum position limit ({self.max_position_size})"
                confidence_adjustment_reason["adjustment_factors"]["max_limit"] = limit_reason
            else:
                limit_reason = f"Minimum position limit ({self.min_position_size})"
                confidence_adjustment_reason["adjustment_factors"]["min_limit"] = limit_reason
        
        # Set adjusted position size
        confidence_adjustment_reason["adjusted_position_size"] = position_size
        
        # Final position size and explanation
        confidence_adjustment_reason["final_size"] = position_size
        confidence_adjustment_reason["explanation"] = " → ".join(confidence_adjustment_reason["adjustment_factors"].values())
        
        return position_size, conflict_type, conflict_handling_applied, confidence_adjustment_reason, portfolio_risk_exceeded

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
        
        Enhanced version that includes key insights and market mood tagging.
        
        Args:
            decision: Decision dictionary from DecisionAgent
            analyst_outputs: Optional dictionary of analyst outputs
            
        Returns:
            List of dictionaries containing structured agent contributions with insights
        """
        structured_contributions = []
        
        # Track signals by type to identify disagreements and market mood
        signals_by_type = {"BUY": [], "SELL": [], "NEUTRAL": [], "HOLD": []}
        market_mood_tags = set()
        
        # First check if we have agent_contributions in the decision
        agent_contributions = decision.get('agent_contributions', {})
        contributing_agents = decision.get('contributing_agents', [])
        
        # Standard mapping for analyst outputs keys
        analyst_key_map = {
            "TechnicalAnalystAgent": "technical_analysis",
            "SentimentAnalystAgent": "sentiment_analysis",
            "SentimentAggregatorAgent": "sentiment_aggregator",
            "LiquidityAnalystAgent": "liquidity_analysis",
            "FundingRateAnalystAgent": "funding_rate_analysis",
            "OpenInterestAnalystAgent": "open_interest_analysis"
        }
        
        # Process agent_contributions if available
        if agent_contributions and isinstance(agent_contributions, dict):
            for agent_name, contribution in agent_contributions.items():
                if agent_name == "UnknownAgent":
                    continue
                    
                if isinstance(contribution, dict):
                    # Extract core data with proper signal normalization
                    signal = contribution.get('signal', None)
                    
                    # Replace UNKNOWN with actual agent signal if possible
                    if signal is None or signal == 'UNKNOWN':
                        if 'action' in contribution:
                            signal = contribution.get('action')
                        elif agent_name in analyst_outputs and isinstance(analyst_outputs[agent_name], dict):
                            signal = analyst_outputs[agent_name].get('signal')
                    
                    # If still none/unknown, use a meaningful default based on agent type
                    if signal is None or signal == 'UNKNOWN':
                        if 'Technical' in agent_name:
                            signal = 'NEUTRAL'  # Default for technical analysis
                        elif 'Sentiment' in agent_name:
                            signal = 'NEUTRAL'  # Default for sentiment analysis
                        elif 'Liquidity' in agent_name:
                            signal = 'NEUTRAL'  # Default for liquidity analysis
                        else:
                            signal = 'NEUTRAL'  # General default
                    
                    confidence = contribution.get('confidence', 0)
                    
                    # Create agent contribution item
                    agent_item = {
                        'agent': agent_name,
                        'action': signal,
                        'confidence': confidence,
                        'reason': '',  # Default empty reason
                        'key_insight': ''  # New field for key insight
                    }
                    
                    # Get reasoning from contribution if available
                    if 'reasoning' in contribution:
                        agent_item['reason'] = contribution['reasoning']
                    
                    # Try to get more detailed data from analyst_outputs
                    analyst_output_key = analyst_key_map.get(agent_name, agent_name.lower().replace('agent', '').strip())
                    analyst_data = None
                    
                    if analyst_outputs and isinstance(analyst_outputs, dict):
                        # Safe dictionary access
                        if agent_name in analyst_outputs and analyst_outputs[agent_name] is not None:
                            analyst_data = analyst_outputs[agent_name]
                        elif analyst_output_key in analyst_outputs and analyst_outputs[analyst_output_key] is not None:
                            analyst_data = analyst_outputs[analyst_output_key]
                    
                    if isinstance(analyst_data, dict):
                        # Get the full reasoning and generate key insight
                        full_reason = analyst_data.get('reasoning', '')
                        if full_reason:
                            # Set full reasoning if available
                            agent_item['reason'] = full_reason
                            
                            # Extract key insight - first sentence or up to 100 chars
                            insight = full_reason.split('.')[0].strip()
                            if len(insight) > 100:
                                insight = insight[:97] + "..."
                            agent_item['key_insight'] = insight
                    
                    # Add to signal groups for disagreement analysis and market mood tagging
                    if signal in signals_by_type:
                        signals_by_type[signal].append({
                            'agent': agent_name,
                            'confidence': confidence,
                            'key_insight': agent_item.get('key_insight', '')
                        })
                    
                    # Generate agent-specific tags for market mood
                    agent_tags = self._generate_agent_specific_tags(agent_name, signal, confidence, agent_item.get('key_insight', ''))
                    if agent_tags:
                        market_mood_tags.update(agent_tags)
                        agent_item['tags'] = agent_tags
                    
                    structured_contributions.append(agent_item)
        
        # If no agent_contributions but we have analyst_outputs, extract from there
        elif analyst_outputs and isinstance(analyst_outputs, dict):
            for agent_key, agent_data in analyst_outputs.items():
                if not isinstance(agent_data, dict):
                    continue
                
                # Map back to agent name if possible
                agent_name = agent_key
                for full_name, short_key in analyst_key_map.items():
                    if short_key == agent_key:
                        agent_name = full_name
                        break
                
                agent_signal = agent_data.get('signal', '')
                agent_confidence = agent_data.get('confidence', 0)
                
                # Get reasoning - try multiple possible fields
                agent_reason = ''
                if 'reasoning' in agent_data:
                    agent_reason = agent_data['reasoning']
                elif 'reason' in agent_data:
                    agent_reason = agent_data['reason']
                
                # Extract key insight
                key_insight = ''
                if agent_reason:
                    key_insight = agent_reason.split('.')[0].strip()
                    if len(key_insight) > 100:
                        key_insight = key_insight[:97] + "..."
                
                # Generate agent-specific tags
                agent_tags = self._generate_agent_specific_tags(agent_name, agent_signal, agent_confidence, key_insight)
                if agent_tags:
                    market_mood_tags.update(agent_tags)
                
                # Add to signal groups for disagreement analysis
                if agent_signal in signals_by_type:
                    signals_by_type[agent_signal].append({
                        'agent': agent_name,
                        'confidence': agent_confidence,
                        'key_insight': key_insight
                    })
                
                # Add to structured contributions
                contribution = {
                    'agent': agent_name,
                    'action': agent_signal,
                    'confidence': agent_confidence,
                    'reason': agent_reason,
                    'key_insight': key_insight
                }
                
                if agent_tags:
                    contribution['tags'] = agent_tags
                    
                structured_contributions.append(contribution)
        
        # If nothing else, try to extract from contributing_agents
        elif contributing_agents:
            signal = decision.get('signal', None)
            # Handle signal normalization
            if signal is None or signal == 'UNKNOWN':
                # Try to get signal from final_signal or action
                if 'final_signal' in decision:
                    signal = decision.get('final_signal')
                elif 'action' in decision:
                    signal = decision.get('action')
                else:
                    # Default to NEUTRAL if nothing else found
                    signal = 'NEUTRAL'
                    
            confidence = decision.get('confidence', 0)
            reasoning = decision.get('reasoning', '')
            
            # Extract key insight
            key_insight = ''
            if reasoning:
                key_insight = reasoning.split('.')[0].strip()
                if len(key_insight) > 100:
                    key_insight = key_insight[:97] + "..."
            
            for agent_name in contributing_agents:
                if agent_name == "UnknownAgent":
                    continue
                
                # Generate agent-specific tags
                safe_signal = signal if isinstance(signal, str) else "NEUTRAL"
                agent_tags = self._generate_agent_specific_tags(agent_name, safe_signal, confidence, key_insight)
                if agent_tags:
                    market_mood_tags.update(agent_tags)
                
                # Add to signal groups for disagreement analysis
                if signal in signals_by_type:
                    signals_by_type[signal].append({
                        'agent': agent_name,
                        'confidence': confidence,
                        'key_insight': key_insight
                    })
                
                contribution = {
                    'agent': agent_name,
                    'action': signal,
                    'confidence': confidence,
                    'reason': reasoning,
                    'key_insight': key_insight
                }
                
                if agent_tags:
                    contribution['tags'] = agent_tags
                    
                structured_contributions.append(contribution)
        
        # Sort by confidence (descending)
        structured_contributions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Add disagreement summary if there are divergent signals
        disagreement_summary = self._generate_disagreement_summary(signals_by_type)
        if disagreement_summary:
            structured_contributions.append({
                'agent': 'DISAGREEMENT_SUMMARY',
                'action': 'INFO',
                'confidence': 100,  # This is metadata, not a real signal
                'reason': disagreement_summary,
                'key_insight': "Agent disagreement detected",
                'tags': ['agent_disagreement']
            })
            market_mood_tags.add('mixed_signals')
        
        # Add market mood summary if we have tags
        if market_mood_tags:
            structured_contributions.append({
                'agent': 'MARKET_MOOD',
                'action': 'INFO',
                'confidence': 100,  # This is metadata, not a real signal
                'reason': f"Market mood: {', '.join(sorted(market_mood_tags))}",
                'key_insight': "Market mood indicators",
                'tags': list(market_mood_tags)
            })
        
        return structured_contributions
    
    def _detect_tag_conflicts(self) -> Optional[str]:
        """
        Detect conflicts between market mood tags and provide clarification.
        
        Returns:
            String explanation of tag conflicts or None if no conflicts
        """
        if not hasattr(self, 'generated_tags') or not self.generated_tags:
            return None
            
        # Check for specific conflicts
        bullish_tags = []
        bearish_tags = []
        mixed_tags = []
        
        # Group tags by sentiment
        for tag, sentiment, confidence in self.generated_tags:
            if sentiment == "bullish":
                bullish_tags.append((tag, confidence))
            elif sentiment == "bearish":
                bearish_tags.append((tag, confidence))
            elif sentiment == "mixed":
                mixed_tags.append((tag, confidence))
        
        # Check for conflict (both bullish and bearish tags present)
        if bullish_tags and bearish_tags:
            # Find strongest bullish and bearish tags
            strongest_bullish = max(bullish_tags, key=lambda x: x[1])
            strongest_bearish = max(bearish_tags, key=lambda x: x[1])
            
            # Log the tag conflict for debugging
            logger.info(f"[INFO] Mood clarification added due to conflicting tags: {strongest_bullish[0]} vs {strongest_bearish[0]}")
            
            # Generate appropriate clarification
            if strongest_bullish[1] > strongest_bearish[1]:
                return f"Conflicting indicators present: {strongest_bullish[0]} is dominant over {strongest_bearish[0]}, " \
                       f"suggesting short-term noise is contrary to primary signal."
            elif strongest_bearish[1] > strongest_bullish[1]:
                return f"Conflicting indicators present: {strongest_bearish[0]} overrides {strongest_bullish[0]}, " \
                       f"indicating mixed signals with bearish tone prevailing."
            else:
                return f"Equal strength conflict between {strongest_bullish[0]} and {strongest_bearish[0]}, " \
                       f"suggesting market indecision and potentially choppy conditions."
        
        # Check for mixed tags conflicting with directional tags
        if mixed_tags and (bullish_tags or bearish_tags):
            mixed_tag = mixed_tags[0][0]
            sentiment = "bullish" if bullish_tags else "bearish"
            return f"Mixed indicator ({mixed_tag}) present alongside {sentiment} bias, " \
                   f"suggesting caution despite directional pressure."
                
        # No conflicts
        return None
        
    def _generate_strategy_tags(self, signal: Optional[str], analyst_outputs: Optional[Dict[str, Any]] = None, 
                             historical_data: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Generate specific trading strategy tags based on market conditions.
        
        This method analyzes the analyst outputs and historical data to identify
        specific trading strategies like oversold_bounce, bullish_breakout, etc.
        
        Args:
            signal: The trading signal (BUY/SELL/HOLD)
            analyst_outputs: Dictionary of analyst outputs with technical, sentiment, etc.
            historical_data: Optional historical price data
            
        Returns:
            List of strategy tags
        """
        # Store the generated tags for conflict checking later
        self.generated_tags = []
        strategy_tags = []
        
        # Skip strategy tagging for non-actionable signals
        if signal not in ["BUY", "SELL"]:
            return strategy_tags
            
        # Initialize technical indicators
        rsi_value = None
        in_uptrend = False
        in_downtrend = False
        near_support = False
        near_resistance = False
        high_volume = False
        strong_momentum = False
        
        # Extract technical analysis data if available
        technical_data = None
        if analyst_outputs and isinstance(analyst_outputs, dict):
            if "technical_analysis" in analyst_outputs:
                technical_data = analyst_outputs["technical_analysis"]
            elif "TechnicalAnalystAgent" in analyst_outputs:
                technical_data = analyst_outputs["TechnicalAnalystAgent"]
        
        # Extract key technical indicators if available
        if isinstance(technical_data, dict):
            # Try to extract RSI
            if "indicators" in technical_data and isinstance(technical_data["indicators"], dict):
                rsi_value = technical_data["indicators"].get("rsi")
            elif "rsi" in technical_data:
                rsi_value = technical_data.get("rsi")
                
            # Extract trend information from reasoning or explanation
            reasoning = technical_data.get("reasoning", "")
            if not reasoning:
                reasoning = technical_data.get("reason", "")
                
            if reasoning:
                # Check for trend mentions
                if any(term in reasoning.lower() for term in ["uptrend", "bullish trend", "higher highs"]):
                    in_uptrend = True
                if any(term in reasoning.lower() for term in ["downtrend", "bearish trend", "lower lows"]):
                    in_downtrend = True
                    
                # Check for support/resistance mentions
                if any(term in reasoning.lower() for term in ["support", "bounce", "floor"]):
                    near_support = True
                if any(term in reasoning.lower() for term in ["resistance", "ceiling", "top"]):
                    near_resistance = True
                    
                # Check for volume mentions
                if any(term in reasoning.lower() for term in ["high volume", "increased volume", "volume surge"]):
                    high_volume = True
                    
                # Check for momentum mentions
                if any(term in reasoning.lower() for term in ["strong momentum", "gaining momentum", "momentum shift"]):
                    strong_momentum = True
        
        # Extract liquidity analysis data if available
        liquidity_data = None
        if analyst_outputs and isinstance(analyst_outputs, dict):
            if "liquidity_analysis" in analyst_outputs:
                liquidity_data = analyst_outputs["liquidity_analysis"]
            elif "LiquidityAnalystAgent" in analyst_outputs:
                liquidity_data = analyst_outputs["LiquidityAnalystAgent"]
                
        # Check for liquidity walls
        has_buy_wall = False
        has_sell_wall = False
        
        if isinstance(liquidity_data, dict):
            # Check for explicit liquidity data
            if "support_clusters" in liquidity_data and liquidity_data["support_clusters"]:
                near_support = True
            if "resistance_clusters" in liquidity_data and liquidity_data["resistance_clusters"]:
                near_resistance = True
                
            # Look for liquidity walls in reasoning
            reasoning = liquidity_data.get("reasoning", "")
            if not reasoning:
                reasoning = liquidity_data.get("reason", "")
                
            if reasoning:
                if any(term in reasoning.lower() for term in ["buy wall", "buying pressure", "accumulation"]):
                    has_buy_wall = True
                if any(term in reasoning.lower() for term in ["sell wall", "selling pressure", "distribution"]):
                    has_sell_wall = True
        
        # Extract sentiment data if available
        sentiment_data = None
        if analyst_outputs and isinstance(analyst_outputs, dict):
            if "sentiment_analysis" in analyst_outputs:
                sentiment_data = analyst_outputs["sentiment_analysis"]
            elif "SentimentAnalystAgent" in analyst_outputs:
                sentiment_data = analyst_outputs["SentimentAnalystAgent"]
            elif "sentiment_aggregator" in analyst_outputs:
                sentiment_data = analyst_outputs["sentiment_aggregator"]
            elif "SentimentAggregatorAgent" in analyst_outputs:
                sentiment_data = analyst_outputs["SentimentAggregatorAgent"]
                
        # Extract sentiment insights
        sentiment_bullish = False
        sentiment_bearish = False
        sentiment_extreme = False
        sentiment_divergence = False
        
        if isinstance(sentiment_data, dict):
            sentiment_signal = sentiment_data.get("signal", "")
            sentiment_confidence = sentiment_data.get("confidence", 0)
            
            # Check for strong sentiment
            if sentiment_signal == "BUY" and sentiment_confidence >= 70:
                sentiment_bullish = True
            elif sentiment_signal == "SELL" and sentiment_confidence >= 70:
                sentiment_bearish = True
                
            # Check for extreme sentiment (possible contrarian indicator)
            if sentiment_confidence >= 90:
                sentiment_extreme = True
                
            # Check for sentiment divergence in reasoning
            reasoning = sentiment_data.get("reasoning", "")
            if not reasoning:
                reasoning = sentiment_data.get("reason", "")
                
            if reasoning and any(term in reasoning.lower() for term in ["diverge", "contrary", "opposite", "differ"]):
                sentiment_divergence = True
                
        # Extract funding rate data for potential tag conflicts
        funding_data = None
        if analyst_outputs and isinstance(analyst_outputs, dict):
            if "funding_rate_analysis" in analyst_outputs:
                funding_data = analyst_outputs["funding_rate_analysis"]
            elif "FundingRateAnalystAgent" in analyst_outputs:
                funding_data = analyst_outputs["FundingRateAnalystAgent"]
        
        # Check for favorable/unfavorable funding
        favorable_funding = False
        unfavorable_funding = False
        funding_signal = "NEUTRAL"
        
        if isinstance(funding_data, dict):
            funding_signal = funding_data.get("signal", "NEUTRAL")
            funding_confidence = funding_data.get("confidence", 0)
            
            # Check for funding conditions
            if funding_signal == "BUY" and funding_confidence >= 60:
                favorable_funding = True
                self.generated_tags.append(("favorable_funding", "bullish", funding_confidence))
            elif funding_signal == "SELL" and funding_confidence >= 60:
                unfavorable_funding = True
                self.generated_tags.append(("unfavorable_funding", "bearish", funding_confidence))
        
        # Now determine strategy tags
        # BUY signal strategies
        if signal == "BUY":
            # Oversold bounce strategy
            if rsi_value is not None and rsi_value < 35:
                strategy_tags.append("oversold_bounce")
                self.generated_tags.append(("oversold_bounce", "bullish", 75))
            elif near_support and (in_downtrend or has_buy_wall):
                strategy_tags.append("support_bounce")
                self.generated_tags.append(("support_bounce", "bullish", 70))
                
            # Bullish breakout strategy
            if near_resistance and high_volume and strong_momentum:
                strategy_tags.append("bullish_breakout")
                self.generated_tags.append(("bullish_breakout", "bullish", 80))
                
            # Trend following strategy
            if in_uptrend and strong_momentum:
                strategy_tags.append("momentum_surge")
                self.generated_tags.append(("momentum_surge", "bullish", 75))
                
            # Sentiment-based strategies
            if sentiment_bullish and near_support:
                strategy_tags.append("sentiment_support_buy")
                self.generated_tags.append(("sentiment_support_buy", "bullish", 70))
            elif sentiment_bearish and sentiment_extreme:
                strategy_tags.append("contrarian_buy")  # Contrarian strategy
                self.generated_tags.append(("contrarian_buy", "bullish", 60))
                
            # Divergence strategies
            if sentiment_divergence and technical_data and isinstance(technical_data, dict) and technical_data.get("signal") == "BUY":
                strategy_tags.append("technical_sentiment_divergence")
                self.generated_tags.append(("technical_sentiment_divergence", "mixed", 65))
                
        # SELL signal strategies
        elif signal == "SELL":
            # Overbought reversal strategy
            if rsi_value is not None and rsi_value > 65:
                strategy_tags.append("overbought_reversal")
                self.generated_tags.append(("overbought_reversal", "bearish", 75))
            elif near_resistance and (in_uptrend or has_sell_wall):
                strategy_tags.append("resistance_reversal")
                self.generated_tags.append(("resistance_reversal", "bearish", 70))
                
            # Bearish breakdown strategy
            if near_support and high_volume and strong_momentum:
                strategy_tags.append("bearish_breakdown")
                self.generated_tags.append(("bearish_breakdown", "bearish", 80))
                
            # Trend following strategy
            if in_downtrend and strong_momentum:
                strategy_tags.append("momentum_drop")
                self.generated_tags.append(("momentum_drop", "bearish", 75))
                
            # Sentiment-based strategies
            if sentiment_bearish and near_resistance:
                strategy_tags.append("sentiment_resistance_sell")
                self.generated_tags.append(("sentiment_resistance_sell", "bearish", 70))
            elif sentiment_bullish and sentiment_extreme:
                strategy_tags.append("contrarian_sell")  # Contrarian strategy
                self.generated_tags.append(("contrarian_sell", "bearish", 60))
                
            # Divergence strategies
            if sentiment_divergence and technical_data and isinstance(technical_data, dict) and technical_data.get("signal") == "SELL":
                strategy_tags.append("technical_sentiment_divergence")
                self.generated_tags.append(("technical_sentiment_divergence", "mixed", 65))
        
        return strategy_tags
        
    def _generate_disagreement_summary(self, signals_by_type: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
        """
        Generate a summary of agent disagreements.
        
        Args:
            signals_by_type: Dictionary mapping signal types to lists of agents
            
        Returns:
            String summary of disagreements or None if no significant disagreement
        """
        # Check if we have opposing signals (BUY vs SELL)
        buy_agents = signals_by_type.get("BUY", [])
        sell_agents = signals_by_type.get("SELL", [])
        neutral_agents = signals_by_type.get("NEUTRAL", []) + signals_by_type.get("HOLD", [])
        
        if not buy_agents and not sell_agents:
            return None  # No directional signals to compare
            
        # Minimal disagreement case - check confidence
        if buy_agents and not sell_agents and len(neutral_agents) <= 1:
            return None  # Only BUY signals, no significant disagreement
            
        if sell_agents and not buy_agents and len(neutral_agents) <= 1:
            return None  # Only SELL signals, no significant disagreement
        
        # We have some form of disagreement, generate summary
        parts = []
        
        if buy_agents and sell_agents:
            # Direct BUY vs SELL conflict
            buy_list = ", ".join([f"{a['agent'].replace('Agent', '')}" for a in buy_agents])
            sell_list = ", ".join([f"{a['agent'].replace('Agent', '')}" for a in sell_agents])
            
            parts.append(f"{buy_list} show{'s' if len(buy_agents) == 1 else ''} bullish pressure")
            parts.append(f"while {sell_list} {'is' if len(sell_agents) == 1 else 'are'} bearish")
        
        # Add neutral agents if they're significant
        if neutral_agents and (buy_agents or sell_agents):
            neutral_list = ", ".join([f"{a['agent'].replace('Agent', '')}" for a in neutral_agents])
            parts.append(f"and {neutral_list} remain{'s' if len(neutral_agents) == 1 else ''} neutral")
        
        # Add insight-based details for high confidence signals
        high_confidence_insights = []
        
        for signal_type, agents in signals_by_type.items():
            for agent in agents:
                if agent.get('confidence', 0) >= 75 and agent.get('key_insight'):
                    agent_name = agent['agent'].replace('Agent', '')
                    insight = agent['key_insight']
                    high_confidence_insights.append(f"{agent_name}: {insight}")
        
        # Combine everything
        summary = ". ".join(parts)
        
        if high_confidence_insights:
            summary += ". Key insights: " + "; ".join(high_confidence_insights[:3])  # Limit to top 3 insights
            
        return summary
        
    def _generate_agent_specific_tags(
        self, 
        agent_name: str, 
        signal: str, 
        confidence: float,
        key_insight: str = ""
    ) -> List[str]:
        """
        Generate market mood tags based on agent, signal, and confidence.
        
        Args:
            agent_name: Name of the agent
            signal: Agent's signal
            confidence: Agent's confidence
            key_insight: Key insight from the agent
            
        Returns:
            List of tags describing market mood
        """
        tags = []
        agent_type = agent_name.lower().replace('agent', '').strip()
        
        # High confidence signals get special tags
        if confidence >= 80:
            if signal == "BUY":
                tags.append("strong_bullish")
            elif signal == "SELL":
                tags.append("strong_bearish")
            elif signal == "HOLD":
                tags.append("strong_indecision")
        
        # Add agent-specific tags
        if "technical" in agent_type:
            if signal == "BUY":
                tags.append("technical_bullish")
            elif signal == "SELL":
                tags.append("technical_bearish")
            elif signal == "NEUTRAL" or signal == "HOLD":
                tags.append("technical_neutral")
                
            # Add key insight based tags
            if key_insight:
                insight_lower = key_insight.lower()
                if any(term in insight_lower for term in ["oversold", "support", "bottom"]):
                    tags.append("oversold_conditions")
                if any(term in insight_lower for term in ["overbought", "resistance", "top"]):
                    tags.append("overbought_conditions")
                if any(term in insight_lower for term in ["trend", "uptrend", "bullish trend"]):
                    tags.append("trending_market")
                if any(term in insight_lower for term in ["reversal", "turning", "pivot"]):
                    tags.append("potential_reversal")
        
        elif "sentiment" in agent_type:
            if signal == "BUY":
                tags.append("positive_sentiment")
            elif signal == "SELL":
                tags.append("negative_sentiment")
            elif signal == "NEUTRAL" or signal == "HOLD":
                tags.append("mixed_sentiment")
                
            # Add key insight based tags
            if key_insight:
                insight_lower = key_insight.lower()
                if any(term in insight_lower for term in ["fear", "panic", "anxiety"]):
                    tags.append("fear_dominant")
                if any(term in insight_lower for term in ["greed", "fomo", "excitement"]):
                    tags.append("greed_dominant")
        
        elif "liquidity" in agent_type:
            if signal == "BUY":
                tags.append("good_buy_liquidity")
            elif signal == "SELL":
                tags.append("good_sell_liquidity")
            elif signal == "NEUTRAL" or signal == "HOLD":
                tags.append("balanced_liquidity")
                
            # Add key insight based tags
            if key_insight:
                insight_lower = key_insight.lower()
                if any(term in insight_lower for term in ["wall", "barrier", "resistance"]):
                    tags.append("liquidity_wall")
                if any(term in insight_lower for term in ["thin", "shallow", "low liquidity"]):
                    tags.append("thin_liquidity")
        
        elif "funding" in agent_type:
            if signal == "BUY":
                tags.append("favorable_funding")
            elif signal == "SELL":
                tags.append("unfavorable_funding")
            elif signal == "NEUTRAL" or signal == "HOLD":
                tags.append("neutral_funding")
        
        elif "interest" in agent_type:
            if signal == "BUY":
                tags.append("increasing_interest")
            elif signal == "SELL":
                tags.append("decreasing_interest")
            elif signal == "NEUTRAL" or signal == "HOLD":
                tags.append("stable_interest")
        
        return tags
    
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
        # Use the enhanced _format_agent_contributions method to get structured agent data with insights
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
        is_conflicted: bool = False,  # Explicit conflict flag
        conflict_type: str = None,    # Type of conflict (soft_conflict, conflicted)
        conflict_handling_applied: bool = False,  # Whether position size was adjusted
        conflict_score: Optional[int] = None,  # Specific conflict score
        confidence_adjustment_reason: Optional[Dict[str, Any]] = None,  # Confidence adjustment reasoning
        portfolio_info: Optional[Dict[str, Any]] = None  # Portfolio state information
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
            is_conflicted: Whether there is an explicit conflict flag
            conflict_type: Type of conflict (soft_conflict, conflicted, etc.)
            conflict_handling_applied: Whether position size was adjusted
            conflict_score: Specific conflict score percentage
            confidence_adjustment_reason: Dictionary containing detailed reasoning for confidence adjustments
            
        Returns:
            Human-readable plan digest with enhanced insights from agent contributions and tags
        """
        # Don't generate detailed digest for HOLD signals
        if signal == "HOLD" or signal == "NEUTRAL":
            return "No clear directional edge. Monitor for better setup."
        
        # Add conflict warning prefix based on the conflict type
        conflict_prefix = ""
        
        # Check for explicit conflict handling based on conflict_type
        if conflict_handling_applied:
            # Format specific conflict score if available
            score_text = f"{conflict_score}%" if conflict_score is not None else ""
            
            if conflict_type == "conflicted":
                conflict_prefix = f"⚠️ HIGH CONFLICT DETECTED ({score_text}): Position size reduced by 50% due to significant signal disagreement. "
                confidence = max(0, confidence - 15)
            elif conflict_type == "soft_conflict":
                conflict_prefix = f"⚠️ SOFT CONFLICT DETECTED ({score_text}): Position size reduced by 20% due to mild signal disagreement. "
                confidence = max(0, confidence - 10)
            else:
                # Minor conflict below the soft threshold
                conflict_prefix = f"⚠️ MINOR CONFLICT DETECTED ({score_text}): Position size proportionally reduced due to minor signal disagreement. "
                confidence = max(0, confidence - 5)
        
        # Enhanced conflict handling for explicit CONFLICTED signals
        elif is_conflicted:
            # Format directional confidence if available for more detailed warnings
            directional_conf_str = ""
            directional_confidence = getattr(self, '_directional_confidence', None)
            if directional_confidence is not None:
                directional_conf_str = f", directional confidence: {directional_confidence}%"
                
            conflict_prefix = f"⚠️ EXPLICIT CONFLICT DETECTED: Trading with 70% reduced position size{directional_conf_str}. EXERCISE EXTREME CAUTION. "
            confidence = max(0, confidence - 20)  # Higher confidence reduction
        
        # Check for 'conflicted' in tags as a fallback
        elif not is_conflicted and tags and 'conflicted' in tags:
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
                
        # Add portfolio information if available
        if portfolio_info and isinstance(portfolio_info, dict) and len(portfolio_info) > 0:
            asset = portfolio_info.get('asset', '')
            total_exposure = portfolio_info.get('total_exposure_pct', 0)
            max_exposure = portfolio_info.get('max_exposure_pct', 100)
            available_exposure = portfolio_info.get('available_exposure_pct', 0)
            
            # Add asset-specific exposure if available
            asset_exposure_info = ""
            if asset and 'asset_exposure_pct' in portfolio_info:
                asset_exposure = portfolio_info.get('asset_exposure_pct', 0)
                asset_max_exposure = portfolio_info.get('asset_max_exposure_pct', 0)
                asset_exposure_info = f", {asset}: {asset_exposure:.1f}% of {asset_max_exposure:.1f}% limit"
            
            # Format portfolio constraint information
            digest += f" Portfolio constraints: {total_exposure:.1f}% allocated of {max_exposure:.1f}% max{asset_exposure_info}."
        
        # Add confidence adjustment reasoning if available
        if confidence_adjustment_reason and isinstance(confidence_adjustment_reason, dict):
            # Extract the main details
            original_pos_size = confidence_adjustment_reason.get('original_position_size')
            adjusted_pos_size = confidence_adjustment_reason.get('adjusted_position_size')
            adjustment_factors = confidence_adjustment_reason.get('adjustment_factors', {})
            
            if original_pos_size is not None and adjusted_pos_size is not None and original_pos_size != adjusted_pos_size:
                # Calculate percentage adjustment
                pct_change = ((adjusted_pos_size / original_pos_size) - 1) * 100
                adjustment_str = f" Position size {abs(pct_change):.0f}% {'reduced' if pct_change < 0 else 'increased'}"
                
                # Add reason if available
                if adjustment_factors:
                    reasons = []
                    
                    if 'conflict_score' in adjustment_factors:
                        reasons.append(f"conflict score of {adjustment_factors['conflict_score']}%")
                        
                    if 'agent_disagreements' in adjustment_factors:
                        disagreements = adjustment_factors['agent_disagreements']
                        if isinstance(disagreements, list) and disagreements:
                            agent_str = ", ".join(disagreements[:2])
                            reasons.append(f"disagreement between {agent_str}")
                    
                    # Add factors to the adjustment string
                    if reasons:
                        adjustment_str += f" due to {' and '.join(reasons)}."
                        digest += adjustment_str
        
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
        
        # Get signal and confidence metrics
        signal = trade_plan.get('signal', 'UNKNOWN')
        confidence = trade_plan.get('confidence', 0)
        normalized_confidence = trade_plan.get('normalized_confidence', confidence)
        
        # Get directional confidence if available
        directional_confidence = trade_plan.get('directional_confidence')
        summary_confidence = trade_plan.get('summary_confidence', {})
        
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
        
        # Get decision consistency info
        decision_consistency = trade_plan.get('decision_consistency', True)
        
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
        
        # Core trade details with enhanced confidence metrics
        confidence_display = f"{normalized_confidence}%"
        if directional_confidence is not None:
            confidence_display += f", Directional: {directional_confidence}%"
        elif isinstance(summary_confidence, dict) and 'directional' in summary_confidence:
            confidence_display += f", Directional: {summary_confidence['directional']}%"
            
        logger.info(f"- Signal:        {signal} (Confidence: {confidence_display})")
        
        # Add mood clarification if available
        mood_clarification = trade_plan.get('mood_clarification')
        if mood_clarification:
            logger.info(f"- Mood Status:   ⚠️ {mood_clarification}")
        
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
        
        # Portfolio info if available
        portfolio_info = trade_plan.get('portfolio_info', {})
        if portfolio_info and isinstance(portfolio_info, dict) and len(portfolio_info) > 0:
            logger.info("")
            logger.info("📊 Portfolio Information:")
            
            # Display total portfolio metrics
            logger.info(f"- Total Value:    {portfolio_info.get('total_value', 0):.2f}")
            logger.info(f"- Available Cash: {portfolio_info.get('available_cash', 0):.2f}")
            
            # Display exposure metrics
            total_exposure = portfolio_info.get('total_exposure_pct', 0)
            max_exposure = portfolio_info.get('max_exposure_pct', 100)
            logger.info(f"- Total Exposure: {total_exposure:.1f}% / {max_exposure:.1f}% max")
            
            # Display asset-specific exposure if available
            asset = portfolio_info.get('asset', '')
            if asset and 'asset_exposure_pct' in portfolio_info:
                asset_exposure = portfolio_info.get('asset_exposure_pct', 0)
                asset_max = portfolio_info.get('asset_max_exposure_pct', 0)
                logger.info(f"- {asset} Exposure: {asset_exposure:.1f}% / {asset_max:.1f}% max")
        
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
        conflict_handling_applied = trade_plan.get('conflict_handling_applied', False)
        conflict_type = trade_plan.get('conflict_type', None)
        
        if conflict_handling_applied:
            # New enhanced conflict handling with graduated thresholds
            if conflict_type == "conflicted":
                logger.info(f"⚠️ HIGH CONFLICT DETECTED: {conflict_score}% (Significant signal disagreement)")
                
                # Check if this is an explicit CONFLICTED signal with directional confidence
                if trade_plan.get('is_conflicted', False):
                    # Get directional confidence if available
                    dir_conf = ""
                    if directional_confidence is not None:
                        dir_conf = f", Directional confidence: {directional_confidence}%"
                    if hasattr(self, '_directional_confidence') and self._directional_confidence is not None:
                        dir_conf = f", Directional confidence: {self._directional_confidence}%"
                        
                    logger.info(f"🔴 EXPLICIT CONFLICT OVERRIDE: Position size reduced by 70% for risk management{dir_conf}")
                else:
                    logger.info(f"  Position size reduced by 50% for risk management (derived from conflict score)")
            elif conflict_type == "soft_conflict":
                logger.info(f"⚠️ SOFT CONFLICT DETECTED: {conflict_score}% (Moderate signal disagreement)")
                logger.info(f"  Position size reduced by 20% for risk management")
        elif conflict_score and conflict_score > 0:
            # Legacy conflict handling display for backward compatibility
            if conflict_score > 50:
                logger.info(f"⚠️ Conflict Score: {conflict_score}% (HIGH divergence)")
            elif conflict_score > 30:
                logger.info(f"⚠️ Conflict Score: {conflict_score}% (moderate divergence)")
            else:
                logger.info(f"ℹ️ Conflict Score: {conflict_score}% (minor divergence)")
            
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
        
        # Display decision consistency info
        consistency_status = "✅ Consistent" if decision_consistency else "❌ Inconsistent"
        if not decision_consistency:
            logger.info(f"  Decision Consistency: {consistency_status} (TradePlanAgent signal differs from DecisionAgent)")
        
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
            
            # Check if conflict handling was applied (new graduated approach)
            conflict_handling_applied = trade_plan.get('conflict_handling_applied', False)
            conflict_type = trade_plan.get('conflict_type')
            conflict_score = trade_plan.get('conflict_score')
            
            if conflict_handling_applied:
                # Check if this is an explicit CONFLICTED signal with enhanced reduction
                if trade_plan.get('is_conflicted', False):
                    # Explicit CONFLICTED with 70% reduction (only 30% of normal size)
                    estimated_original = position_size / 0.3  # Reverse the 70% reduction
                    dir_conf = ""
                    directional_confidence = trade_plan.get('directional_confidence')
                    if directional_confidence:
                        dir_conf = f", directional confidence: {directional_confidence}%"
                        
                    logger.info(f"  → 🔴 EXPLICIT CONFLICT HANDLING: Aggressive 70% position reduction applied{dir_conf}")
                    logger.info(f"  → Pre-conflict position: {estimated_original:.4f} → Post-conflict: {position_size:.4f}")
                elif conflict_type == "conflicted":
                    # Hard conflict (50% reduction from high conflict score)
                    estimated_original = position_size * 2
                    logger.info(f"  → HIGH CONFLICT HANDLING: {conflict_score}% conflict score triggered 50% position reduction")
                    logger.info(f"  → Pre-conflict position: {estimated_original:.4f} → Post-conflict: {position_size:.4f}")
                elif conflict_type == "soft_conflict":
                    # Soft conflict (20% reduction)
                    estimated_original = position_size * 1.25
                    logger.info(f"  → SOFT CONFLICT HANDLING: {conflict_score}% conflict score triggered 20% position reduction")
                    logger.info(f"  → Pre-conflict position: {estimated_original:.4f} → Post-conflict: {position_size:.4f}")
            elif conflict_score and conflict_score > 0:
                # Legacy conflict handling for backwards compatibility
                max_reduction = 0.7  # Same as in old _calculate_position_size
                reduction_pct = (conflict_score / 100) * max_reduction
                # Reverse the calculation to get original position size
                estimated_original = position_size / (1 - reduction_pct)
                logger.info(f"  → Legacy conflict reduction: {conflict_score}% conflict score reduced position by {reduction_pct:.2%}")
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
                
                # Core trade details with enhanced confidence display
                confidence_display = f"{trade_plan.get('normalized_confidence', 0)}%"
                directional_confidence = trade_plan.get('directional_confidence')
                
                if directional_confidence is not None:
                    confidence_display += f", Directional: {directional_confidence}%"
                    
                # Add conflict information 
                conflict_info = ""
                if trade_plan.get('is_conflicted', False):
                    conflict_info = " [EXPLICIT CONFLICT - 70% POSITION REDUCTION]"
                elif trade_plan.get('conflict_type'):
                    conflict_type = trade_plan.get('conflict_type')
                    if conflict_type == "conflicted":
                        conflict_info = " [HIGH CONFLICT - 50% POSITION REDUCTION]"
                    elif conflict_type == "soft_conflict":
                        conflict_info = " [SOFT CONFLICT - 20% POSITION REDUCTION]"
                        
                f.write(f"Signal: {trade_plan.get('signal')}{conflict_info} (Confidence: {confidence_display})\n")
                
                # Add mood clarification if available
                mood_clarification = trade_plan.get('mood_clarification')
                if mood_clarification:
                    f.write(f"Mood Status: {mood_clarification}\n")
                    
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
                    
                    # Include decision consistency info
                    decision_consistency = trade_plan.get('decision_consistency', True)
                    consistency_status = "Consistent" if decision_consistency else "Inconsistent"
                    if not decision_consistency:
                        f.write(f"\nDecision Consistency: {consistency_status} (TradePlanAgent signal differs from DecisionAgent)")
                
            logger.debug(f"Trade plan log written to {log_path}")
        except Exception as e:
            logger.warning(f"Failed to write trade plan log: {str(e)}")
            
    def _extract_conflicting_agents(self, decision: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """
        Extract conflicting agents from decision data.
        
        Args:
            decision: Decision dictionary containing agent_contributions
            
        Returns:
            Dictionary mapping signal types to agent names and their confidence scores
        """
        conflicting_agents = {}
        
        if isinstance(decision.get('agent_contributions'), dict):
            for agent_name, data in decision.get('agent_contributions', {}).items():
                if isinstance(data, dict) and 'signal' in data and 'confidence' in data:
                    # Only consider signals with confidence >= 70
                    if data['confidence'] >= 70:
                        signal_type = data['signal']
                        if signal_type in ["BUY", "SELL"]:  # Only focus on actionable signals
                            if signal_type not in conflicting_agents:
                                conflicting_agents[signal_type] = {}
                            conflicting_agents[signal_type][agent_name] = data['confidence']
        
        # Only return if we have at least two different signal types
        if len(conflicting_agents) >= 2:
            return conflicting_agents
        return {}
    
    def _generate_risk_warning(self, is_conflicted: bool, conflict_type: Optional[str], decision: Dict[str, Any]) -> Optional[str]:
        """
        Generate a risk warning message for conflicted signals.
        
        Args:
            is_conflicted: Whether this is an explicit CONFLICTED signal
            conflict_type: Type of conflict (soft_conflict, conflicted, etc.)
            decision: Decision dictionary with agent contributions
            
        Returns:
            Risk warning message or None if no conflict
        """
        if not is_conflicted and not conflict_type:
            return None
            
        # Extract conflicting agents to identify which signals are in conflict
        conflicting_agents = self._extract_conflicting_agents(decision)
        
        if is_conflicted:
            # For explicit CONFLICTED signals
            base_warning = "No position opened due to high-confidence conflict between "
            
            if "BUY" in conflicting_agents and "SELL" in conflicting_agents:
                return f"{base_warning}BUY and SELL signals. Market is indecisive."
            else:
                return f"{base_warning}analyst agents. Market is indecisive."
        elif conflict_type == "conflicted":
            # For high conflict (position reduced 50%)
            conflict_score = decision.get('conflict_score', 0)
            return f"Position size reduced by 50% due to high conflict ({conflict_score}% conflict score) between BUY and SELL signals."
        elif conflict_type == "soft_conflict":
            # For soft conflict (position reduced 20%)
            conflict_score = decision.get('conflict_score', 0)
            return f"Position size reduced by 20% due to moderate conflict ({conflict_score}% conflict score) between analyst signals."
            
        return None
        
    def _generate_risk_feedback(self, is_conflicted: bool, conflict_type: Optional[str], position_size: float, portfolio_constraints_applied: bool = False) -> str:
        """
        Generate a comprehensive risk feedback message explaining any position size adjustments 
        due to conflicts or portfolio constraints.
        
        Args:
            is_conflicted: Whether the signal is explicitly CONFLICTED
            conflict_type: Type of conflict detected (soft_conflict, conflicted, etc.)
            position_size: The final position size
            portfolio_constraints_applied: Whether portfolio risk limits were exceeded
            
        Returns:
            Risk feedback message as string
        """
        # Trade blocked due to explicit conflict
        if is_conflicted and position_size == 0:
            return "🚫 TRADE BLOCKED: High-confidence conflicting signals indicate significant market uncertainty. Trade automatically blocked for risk management."
        
        # High conflict with 50% position reduction
        if conflict_type == "conflicted":
            conflict_reduction = "50%"
            return f"⚠️ HIGH CONFLICT ADJUSTMENT: Position size reduced by {conflict_reduction} due to significant disagreement between analyst signals."
        
        # Soft conflict with 20% position reduction
        if conflict_type == "soft_conflict":
            soft_reduction = "20%"
            return f"ℹ️ MILD CONFLICT ADJUSTMENT: Position size reduced by {soft_reduction} due to moderate signal disagreement."
        
        # Portfolio constraint applied
        if portfolio_constraints_applied:
            portfolio_info = getattr(self, 'portfolio_info', {})
            if portfolio_info:
                # Get more detailed portfolio information if available
                total_exposure = portfolio_info.get('total_exposure_pct', 0)
                max_exposure = portfolio_info.get('max_exposure_pct', 0)
                asset = portfolio_info.get('asset', '')
                
                if 'asset_exposure_pct' in portfolio_info and 'asset_max_exposure_pct' in portfolio_info:
                    asset_exposure = portfolio_info.get('asset_exposure_pct', 0)
                    asset_max_exposure = portfolio_info.get('asset_max_exposure_pct', 0)
                    
                    # Determine which limit was more restrictive
                    if asset_exposure > 0 and asset_max_exposure > 0:
                        asset_available = asset_max_exposure - asset_exposure
                        total_available = max_exposure - total_exposure
                        
                        if asset_available < total_available:
                            # Asset-specific limit was more restrictive
                            return f"📊 ASSET EXPOSURE LIMIT: Position size limited because {asset} already represents {asset_exposure:.1f}% of portfolio (max allowed: {asset_max_exposure:.1f}%)."
                
                # Default to total portfolio exposure message
                return f"📊 PORTFOLIO EXPOSURE LIMIT: Position size limited because total exposure is already {total_exposure:.1f}% (max allowed: {max_exposure:.1f}%)."
            
            # Fallback if no detailed portfolio info is available
            return f"📊 PORTFOLIO CONSTRAINT: Position size limited by maximum portfolio exposure settings to maintain risk parameters."
        
        # No risk adjustment applied
        return "✅ No risk adjustments applied to position size."
        
    def build_error_response(self, error_type: str, message: str, symbol: str = "UNKNOWN", interval: str = "1h") -> Dict[str, Any]:
        """
        Build a standardized error response.
        
        Args:
            error_type: Type of error
            message: Error message
            symbol: Trading symbol (defaults to "UNKNOWN")
            interval: Trading interval (defaults to "1h")
            
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
            "plan_digest": f"Error: {message}",
            "symbol": symbol,
            "interval": interval
        }


# Note: This factory function is implemented at the module level to avoid name conflicts
# with the method defined inside the TradeType enum class.
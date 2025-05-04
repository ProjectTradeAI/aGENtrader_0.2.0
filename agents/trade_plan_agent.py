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
        confidence = decision.get('confidence', 0)
        
        # Determine if this is an actionable signal
        is_actionable = signal in ["BUY", "SELL"]
        
        # Get the interval from market data or use default
        interval = market_data.get('interval', '1h')
        
        # If no actionable signal, return a minimal plan
        if not is_actionable:
            logger.info(f"Non-actionable signal {signal}, generating minimal plan")
            return {
                "signal": signal,
                "confidence": confidence,
                "entry_price": None,
                "stop_loss": None,
                "take_profit": None,
                "position_size": 0,
                "reasoning": "No actionable signal generated",
                "timestamp": datetime.now().isoformat(),
                "execution_time_seconds": time.time() - start_time
            }
        
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
        
        # Calculate position size based on confidence
        position_size = self._calculate_position_size(confidence)
        
        # Generate reason summary
        reason_summary = self._generate_reason_summary(decision, analyst_outputs)
        
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
        
        # Determine fallback usage details
        fallback_plan = {
            "entry": entry_price == current_price,  # True if default entry price was used
            "stop_loss": False,
            "take_profit": False
        }
        
        # Check if ATR was used for stop_loss or take_profit
        atr_used = False
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
                    if abs(stop_loss - expected_atr_sl) < 0.001 * entry_price:  # Within 0.1% margin
                        fallback_plan["stop_loss"] = True
                        atr_used = True
                
                # Similar check for take_profit
                atr_tp_multiplier = self.volatility_multipliers.get("atr_tp", 3.0)
                expected_atr_tp = None
                if signal == "BUY":
                    expected_atr_tp = entry_price + (atr_value * atr_tp_multiplier)
                else:  # SELL
                    expected_atr_tp = entry_price - (atr_value * atr_tp_multiplier)
                
                if expected_atr_tp is not None:
                    # If the take_profit is very close to the expected ATR-based value, ATR was likely used
                    if abs(take_profit - expected_atr_tp) < 0.001 * entry_price:  # Within 0.1% margin
                        fallback_plan["take_profit"] = True
        
        # Auto-tagging based on logic
        auto_tags = []
        
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
            risk_snapshot=risk_snapshot
        )
        
        # Prepare comprehensive trade plan
        trade_plan = {
            "signal": signal,
            "confidence": confidence,
            "summary_confidence": summary_confidence,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_size": position_size,
            "reasoning": decision.get('reasoning', 'No reasoning provided'),
            "reason_summary": reason_summary,
            "contributing_agents": contributing_agents,
            "valid_until": valid_until,
            "trade_type": str(trade_type),
            "risk_snapshot": risk_snapshot,
            "fallback_plan": fallback_plan,
            "tags": unique_tags,
            "plan_digest": plan_digest,
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": time.time() - start_time
        }
        
        # Add override information if applicable
        if override_decision:
            trade_plan["override_decision"] = True
            trade_plan["override_reason"] = override_reason
        
        logger.info(f"Trade plan generated for {signal} {symbol} with position size {position_size}")
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
        
        # Return the combined output
        return {**decision, **trade_plan}
    
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
    
    def _calculate_position_size(self, confidence: float) -> float:
        """
        Calculate position size based on confidence level.
        
        Args:
            confidence: Decision confidence percentage
            
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
                curr_high = float(curr_candle[2])
                curr_low = float(curr_candle[3])
                curr_close = float(curr_candle[4])
                prev_close = float(prev_candle[4])
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
    
    def _generate_reason_summary(
        self, 
        decision: Dict[str, Any], 
        analyst_outputs: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a detailed reason summary from decision and analyst outputs.
        
        Args:
            decision: Decision dictionary from DecisionAgent
            analyst_outputs: Optional dictionary of analyst agent outputs
            
        Returns:
            Detailed reason summary
        """
        # Extract key information
        signal = decision.get('signal', 'NEUTRAL')
        confidence = decision.get('confidence', 0)
        contributing_agents = decision.get('contributing_agents', [])
        
        # Start building the summary
        summary_parts = []
        
        # Add signal and confidence
        summary_parts.append(f"{signal} signal with {confidence:.1f}% confidence")
        
        # Add contributing agents
        if contributing_agents:
            agents_str = ", ".join(contributing_agents)
            summary_parts.append(f"based on {agents_str}")
        
        # Add key analyst insights if available
        if analyst_outputs and isinstance(analyst_outputs, dict):
            insights = []
            
            # Check for technical signals
            if "TechnicalAnalystAgent" in analyst_outputs:
                tech = analyst_outputs["TechnicalAnalystAgent"]
                if tech.get('reasoning'):
                    insights.append(f"Technical: {tech['reasoning']}")
            
            # Check for traditional sentiment
            if "SentimentAnalystAgent" in analyst_outputs:
                sent = analyst_outputs["SentimentAnalystAgent"]
                if sent.get('reasoning'):
                    insights.append(f"Sentiment: {sent['reasoning']}")
                    
            # Check for Grok-based advanced sentiment from SentimentAggregatorAgent
            if "SentimentAggregatorAgent" in analyst_outputs:
                grok_sent = analyst_outputs["SentimentAggregatorAgent"]
                
                # Add Grok sentiment analysis if available
                if grok_sent.get('grok_sentiment_summary'):
                    # Extract first sentence for conciseness
                    first_sentence = grok_sent['grok_sentiment_summary'].split('.')[0]
                    insights.append(f"Grok sentiment: {first_sentence}")
                
                # Add sentiment rating if available
                if grok_sent.get('sentiment_rating'):
                    insights.append(f"Market mood: {grok_sent['sentiment_rating']}/5")
                    
                # Add key market drivers if available
                if grok_sent.get('market_drivers') and isinstance(grok_sent['market_drivers'], list):
                    drivers = grok_sent['market_drivers']
                    if drivers:
                        main_driver = drivers[0]
                        insights.append(f"Key driver: {main_driver}")
            
            # Check for liquidity analysis
            if "LiquidityAnalystAgent" in analyst_outputs:
                liq = analyst_outputs["LiquidityAnalystAgent"]
                if liq.get('reasoning'):
                    insights.append(f"Liquidity: {liq['reasoning']}")
                    
                # Add support/resistance clusters if available
                if liq.get('support_clusters') and signal == "BUY":
                    support = liq['support_clusters'][0] if isinstance(liq['support_clusters'], list) and liq['support_clusters'] else None
                    if support:
                        insights.append(f"Support: {support}")
                
                if liq.get('resistance_clusters') and signal == "SELL":
                    resistance = liq['resistance_clusters'][0] if isinstance(liq['resistance_clusters'], list) and liq['resistance_clusters'] else None
                    if resistance:
                        insights.append(f"Resistance: {resistance}")
                        
            # Add funding rate analysis if available
            if "FundingRateAnalystAgent" in analyst_outputs:
                fund = analyst_outputs["FundingRateAnalystAgent"]
                if fund.get('funding_summary'):
                    insights.append(f"Funding: {fund['funding_summary']}")
                    
            # Add open interest analysis if available
            if "OpenInterestAnalystAgent" in analyst_outputs:
                oi = analyst_outputs["OpenInterestAnalystAgent"]
                if oi.get('oi_summary'):
                    insights.append(f"Open Interest: {oi['oi_summary']}")
            
            # Add the top insights to the summary
            if insights:
                for insight in insights[:3]:  # Limit to top 3 insights
                    summary_parts.append(insight)
        
        return ". ".join(summary_parts)
    
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
        risk_snapshot: Dict[str, Any]
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
            
        Returns:
            Human-readable plan digest
        """
        # Don't generate detailed digest for HOLD signals
        if signal == "HOLD" or signal == "NEUTRAL":
            return "No actionable trade signal. Maintaining current position or staying out of the market."
        
        # Start with the overall market direction
        if signal == "BUY":
            digest = "Trend appears bullish"
        else:  # SELL
            digest = "Trend appears bearish"
        
        # Add confidence assessment
        if confidence >= 80:
            digest += " with strong confidence."
        elif confidence >= 65:
            digest += " with moderate confidence."
        else:
            digest += " with limited confidence."
        
        # Add conflict information if relevant
        if high_conflict:
            digest += " Significant disagreement among analysts."
        
        # Add liquidity information
        if liquidity_used:
            digest += " Entry based on key liquidity zones."
        
        # Add trade type information
        if trade_type == TradeType.SCALP:
            digest += " Short-term scalping opportunity."
        elif trade_type == TradeType.SWING:
            digest += " Medium-term swing trade setup."
        elif trade_type == TradeType.TREND_FOLLOWING:
            digest += " Longer-term trend-following position."
        elif trade_type == TradeType.MEAN_REVERSION:
            digest += " Mean reversion trade expected."
        
        # Add risk assessment
        if risk_snapshot:
            r_r_ratio = risk_snapshot.get("risk_reward_ratio")
            if r_r_ratio:
                if r_r_ratio >= 3.0:
                    digest += f" Highly favorable R:R of {r_r_ratio:.1f}."
                elif r_r_ratio >= 2.0:
                    digest += f" Good R:R of {r_r_ratio:.1f}."
                elif r_r_ratio >= 1.0:
                    digest += f" Acceptable R:R of {r_r_ratio:.1f}."
                else:
                    digest += f" Unfavorable R:R of {r_r_ratio:.1f}."
        
        return digest

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
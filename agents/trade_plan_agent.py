"""
aGENtrader v2 Trade Plan Agent

This module provides a trading plan generation agent that extends the base decision agent
to create detailed trade plans including entry, stop-loss, take-profit levels, and position sizing.
"""

import os
import logging
import time
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime

from agents.base_agent import BaseDecisionAgent

# Configure logging
logger = logging.getLogger(__name__)

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
        super().__init__(agent_name="trade_plan_agent")
        self.name = "TradePlanAgent"
        self.description = "Generates detailed trade execution plans"
        
        # Load configuration or use defaults
        self.config = config or {}
        
        # Load risk parameters from config or use defaults
        self.risk_reward_ratio = self.config.get("risk_reward_ratio", 1.5)
        self.max_position_size = self.config.get("max_position_size", 1.0)
        self.min_position_size = self.config.get("min_position_size", 0.1)
        
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
        
        # Get liquidity analysis if available
        liquidity_analysis = None
        if analyst_outputs and "liquidity_analysis" in analyst_outputs:
            liquidity_analysis = analyst_outputs["liquidity_analysis"]
        
        # Determine entry, stop-loss, and take-profit levels
        entry_price, stop_loss, take_profit = self._determine_trade_levels(
            signal=signal, 
            current_price=current_price,
            liquidity_analysis=liquidity_analysis
        )
        
        # Calculate position size based on confidence
        position_size = self._calculate_position_size(confidence)
        
        # Prepare trade plan
        trade_plan = {
            "signal": signal,
            "confidence": confidence,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_size": position_size,
            "reasoning": decision.get('reasoning', 'No reasoning provided'),
            "contributing_agents": decision.get('contributing_agents', []),
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": time.time() - start_time
        }
        
        logger.info(f"Trade plan generated for {signal} {symbol} with position size {position_size}")
        return trade_plan
    
    def make_decision(
        self, 
        symbol: str, 
        interval: str, 
        analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Override the base make_decision method to generate a trade plan.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            analyses: List of analysis results from different agents
            
        Returns:
            Trade plan dictionary
        """
        # Process each analyst's output
        signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "NEUTRAL": 0}
        signal_confidences = {"BUY": [], "SELL": [], "HOLD": [], "NEUTRAL": []}
        contributing_agents = []
        
        # Simple decision algorithm - count signals and average confidences
        for analysis in analyses:
            # Skip if empty or has errors
            if not analysis or 'error' in analysis:
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
        
        # Extract the first analysis that contains market data
        market_data = {}
        analyst_outputs = {}
        
        # Convert analyses to analyst_outputs format for generate_trade_plan
        for analysis in analyses:
            agent_name = analysis.get('agent', '')
            analyst_outputs[agent_name] = analysis
            
            # Try to get market data
            if not market_data:
                if 'market_data' in analysis:
                    market_data = analysis['market_data']
                elif 'current_price' in analysis:
                    market_data = {'current_price': analysis['current_price'], 'symbol': symbol}
        
        # If market data is still missing, create a minimal version
        if not market_data:
            market_data = {'symbol': symbol}
        
        # Generate trade plan based on the decision
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
        liquidity_analysis: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, float, float]:
        """
        Determine entry, stop-loss, and take-profit levels.
        
        Args:
            signal: Trading signal (BUY or SELL)
            current_price: Current market price
            liquidity_analysis: Optional liquidity analysis results
            
        Returns:
            Tuple of (entry_price, stop_loss, take_profit)
        """
        entry_price = current_price
        stop_loss = None
        take_profit = None
        
        # Try to use liquidity analysis for optimal levels if available
        if liquidity_analysis and isinstance(liquidity_analysis, dict):
            # Check for suggested entry and stop loss from liquidity analysis
            suggested_entry = liquidity_analysis.get("suggested_entry")
            suggested_stop_loss = liquidity_analysis.get("suggested_stop_loss")
            
            if suggested_entry is not None:
                entry_price = suggested_entry
                
            if suggested_stop_loss is not None:
                stop_loss = suggested_stop_loss
        
        # Apply default stop loss if none from liquidity analysis
        if stop_loss is None:
            if signal == "BUY":
                # Default stop loss 1% below entry for BUY
                stop_loss = entry_price * 0.99
            else:  # SELL
                # Default stop loss 1% above entry for SELL
                stop_loss = entry_price * 1.01
        
        # Calculate take profit based on risk:reward ratio
        risk = abs(entry_price - stop_loss)
        if signal == "BUY":
            take_profit = entry_price + (risk * self.risk_reward_ratio)
        else:  # SELL
            take_profit = entry_price - (risk * self.risk_reward_ratio)
        
        return entry_price, stop_loss, take_profit
    
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

# Factory function to make it easier to create the agent
def create_trade_plan_agent(config: Optional[Dict[str, Any]] = None) -> TradePlanAgent:
    """
    Create a new TradePlanAgent instance.
    
    Args:
        config: Optional configuration parameters
        
    Returns:
        TradePlanAgent instance
    """
    return TradePlanAgent(config=config)
#!/usr/bin/env python
"""
TradeExecutorAgent for aGENtrader v2

This agent is responsible for executing trading decisions, managing open positions,
and tracking trade performance.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from aGENtrader_v2.agents.trade_book_manager import TradeBookManager
from aGENtrader_v2.data.feed.data_provider_factory import DataProviderFactory

# Setup logger
logger = logging.getLogger("aGENtrader.trade_executor")

class TradeExecutorAgent:
    """
    Agent responsible for trade execution, position management, and tracking.
    
    Responsibilities:
    - Execute trading decisions from analysis agents
    - Manage open positions (prevent redundant entries)
    - Track trade performance
    - Implement risk management rules
    """
    
    def __init__(
        self, 
        config: Dict[str, Any],
        trade_book_manager: Optional[TradeBookManager] = None,
        data_provider_factory: Optional[DataProviderFactory] = None,
        risk_guard_agent=None,
        performance_tracker=None
    ):
        """
        Initialize the trade executor agent.
        
        Args:
            config: Configuration dictionary with parameters for the agent
            trade_book_manager: TradeBookManager instance (will create one if None)
            data_provider_factory: DataProviderFactory instance (needed for real execution)
            risk_guard_agent: RiskGuardAgent instance (will create one if None)
            performance_tracker: TradePerformanceTracker instance (will create one if None)
        """
        self.config = config
        
        # Default risk parameters
        self.default_position_size = config.get("default_position_size", 1.0)
        self.confidence_threshold = config.get("confidence_threshold", 60)
        self.max_position_size_pct = config.get("max_position_size_pct", 10.0)
        self.stop_loss_pct = config.get("stop_loss_pct", 5.0)
        self.take_profit_pct = config.get("take_profit_pct", 10.0)
        
        # Create or use provided trade book manager
        self.trade_book = trade_book_manager or TradeBookManager()
        
        # Initialize risk guard if not provided
        if risk_guard_agent:
            self.risk_guard = risk_guard_agent
        else:
            # Import here to avoid circular dependencies
            from aGENtrader_v2.agents.risk_guard_agent import RiskGuardAgent
            self.risk_guard = RiskGuardAgent(trade_book_manager=self.trade_book)
            logger.info("Initialized RiskGuardAgent")
        
        # Data provider for getting current prices
        self.data_provider_factory = data_provider_factory
        
        # Initialize performance tracker if not provided
        if performance_tracker:
            self.performance_tracker = performance_tracker
        else:
            # Import here to avoid circular dependencies
            from aGENtrader_v2.analytics.trade_performance_tracker import TradePerformanceTracker
            self.performance_tracker = TradePerformanceTracker(data_provider=data_provider_factory)
            logger.info("Initialized TradePerformanceTracker")
        
        logger.info(f"TradeExecutorAgent initialized with confidence threshold {self.confidence_threshold}")
    
    def execute_decision(
        self, 
        decision: Dict[str, Any], 
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a trading decision.
        
        Args:
            decision: Trading decision from an analysis agent
            market_data: Current market data (for pricing info)
            
        Returns:
            Dictionary with execution results
        """
        # Extract key information
        symbol = decision.get("symbol")
        action = decision.get("action", "HOLD")
        confidence = decision.get("confidence", 0)
        
        # Validate decision
        if not symbol:
            logger.error("Cannot execute decision without a symbol")
            return {"status": "error", "message": "Missing symbol in decision"}
        
        # Skip if confidence is below threshold
        if confidence < self.confidence_threshold:
            logger.info(
                f"Skipping {action} for {symbol} - "
                f"confidence {confidence} below threshold {self.confidence_threshold}"
            )
            return {
                "status": "skipped", 
                "reason": "low_confidence",
                "symbol": symbol,
                "action": "HOLD",
                "original_action": action,
                "confidence": confidence
            }
        
        # If HOLD, just return the decision
        if action == "HOLD":
            return {
                "status": "success",
                "action": "HOLD",
                "symbol": symbol,
                "confidence": confidence,
                "reason": decision.get("reason", "Analysis suggests holding")
            }
        
        # Check if we already have an open position in the same direction
        if self.trade_book.should_hold(symbol, action):
            logger.info(f"Already have an open {action} position for {symbol}, holding")
            return {
                "status": "hold",
                "action": "HOLD",
                "symbol": symbol,
                "confidence": confidence,
                "reason": f"Already have an open {action} position"
            }
        
        # Get current price
        current_price = self._get_current_price(symbol, market_data)
        if current_price is None:
            logger.error(f"Cannot execute trade - failed to get current price for {symbol}")
            return {"status": "error", "message": "Failed to get current price"}
        
        # Calculate position size based on strategy (confidence, volatility, or combined)
        position_size = self._calculate_position_size(
            confidence=confidence,
            symbol=symbol,
            market_data=market_data
        )
        
        # Calculate stop loss and take profit levels
        sl, tp = self._calculate_sl_tp(action, current_price)
        
        # Create trade object
        trade = {
            "symbol": symbol,
            "action": action,
            "entry_price": current_price,
            "confidence": confidence,
            "position_size": position_size,
            "stop_loss": sl,
            "take_profit": tp,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": decision.get("reason", "Based on analysis")
        }
        
        # Extract volatility from market data if available
        volatility = None
        if market_data and "ohlcv" in market_data and market_data["ohlcv"]:
            # Calculate volatility from price data if needed
            # This is a simplified version - PositionSizerAgent has a more robust calculation
            try:
                import statistics
                import math
                
                # Get last 14 prices
                prices = [candle["close"] for candle in market_data["ohlcv"][-15:]]
                if len(prices) > 1:
                    # Calculate log returns
                    returns = [math.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]
                    # Calculate standard deviation of returns
                    volatility = statistics.stdev(returns)
            except Exception as e:
                logger.warning(f"Failed to calculate volatility: {e}")
        
        # Add volatility to trade object if calculated
        if volatility is not None:
            trade["volatility"] = volatility
        
        # Run the trade through the risk guard
        accepted, rejection_reason = self.risk_guard.evaluate_trade(trade)
        
        if not accepted:
            logger.warning(f"Trade rejected by risk guard: {rejection_reason}")
            return {
                "status": "rejected",
                "action": "HOLD",
                "symbol": symbol,
                "reason": f"Risk guard rejected: {rejection_reason}",
                "original_action": action,
                "confidence": confidence,
                "position_size": position_size
            }
        
        # Record the trade if accepted
        self.trade_book.record_trade(trade)
        
        # Update risk guard's trade history
        self.risk_guard.record_trade(trade)
        
        logger.info(
            f"Executed {action} for {symbol} at {current_price} "
            f"with confidence {confidence}, position size {position_size}"
        )
        
        return {
            "status": "success",
            "trade": trade,
            "action": action,
            "symbol": symbol,
            "entry_price": current_price,
            "position_size": position_size,
            "stop_loss": sl,
            "take_profit": tp,
            "confidence": confidence
        }
    
    def check_stops(
        self, 
        symbol: str, 
        current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a stop loss or take profit has been hit.
        
        Args:
            symbol: Trading symbol
            current_price: Current price
            
        Returns:
            Closed trade info if a stop was hit, None otherwise
        """
        if symbol is None:
            logger.warning("Cannot check stops with None symbol")
            return None
            
        # Get open trade for this symbol
        trade = self.trade_book.get_open_trade(symbol)
        if not trade:
            return None
        
        # Extract trade information
        action = trade.get("action")
        entry_price = trade.get("entry_price")
        stop_loss = trade.get("stop_loss")
        take_profit = trade.get("take_profit")
        
        # If no SL/TP set, nothing to check
        if not stop_loss or not take_profit:
            return None
        
        # Track if a stop was hit and the reason
        closed_trade = None
        
        # Check for BUY positions
        if action == "BUY":
            # Check stop loss
            if current_price <= stop_loss:
                logger.info(f"Stop loss hit for {symbol} at {current_price}")
                closed_trade = self.trade_book.close_trade(
                    symbol, 
                    exit_price=current_price,
                    reason="Stop loss"
                )
            
            # Check take profit
            elif current_price >= take_profit:
                logger.info(f"Take profit hit for {symbol} at {current_price}")
                closed_trade = self.trade_book.close_trade(
                    symbol, 
                    exit_price=current_price,
                    reason="Take profit"
                )
        
        # Check for SELL positions
        elif action == "SELL":
            # Check stop loss
            if current_price >= stop_loss:
                logger.info(f"Stop loss hit for {symbol} at {current_price}")
                closed_trade = self.trade_book.close_trade(
                    symbol, 
                    exit_price=current_price,
                    reason="Stop loss"
                )
            
            # Check take profit
            elif current_price <= take_profit:
                logger.info(f"Take profit hit for {symbol} at {current_price}")
                closed_trade = self.trade_book.close_trade(
                    symbol, 
                    exit_price=current_price,
                    reason="Take profit"
                )
                
        # Evaluate trade performance if a stop was hit
        if closed_trade:
            try:
                # Evaluate the trade performance
                evaluated_trade = self.performance_tracker.evaluate_trade(closed_trade)
                logger.info(
                    f"Trade performance evaluated: {symbol} {action} - "
                    f"Return: {evaluated_trade.get('return_pct', 0):.2f}%, "
                    f"Status: {evaluated_trade.get('status', 'UNKNOWN')}, "
                    f"Reason: {closed_trade.get('reason', 'Unknown')}"
                )
            except Exception as e:
                logger.error(f"Error evaluating trade performance: {e}")
                
        return closed_trade
    
    def close_position(
        self, 
        symbol: str, 
        reason: str = "Manual close",
        current_price: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Close an open position manually.
        
        Args:
            symbol: Trading symbol
            reason: Reason for closing the position
            current_price: Current price (if None, will try to fetch it)
            
        Returns:
            Closed trade info if successful, None otherwise
        """
        if symbol is None:
            logger.warning("Cannot close position with None symbol")
            return None
            
        # If no current price provided, try to get it
        if current_price is None:
            current_price = self._get_current_price(symbol)
            
        # If we still don't have a price, we can't close the position
        if current_price is None:
            logger.error(f"Cannot close position for {symbol} - failed to get current price")
            return None
        
        # Close the trade
        closed_trade = self.trade_book.close_trade(
            symbol,
            exit_price=current_price,
            reason=reason
        )
        
        # If trade was closed successfully, evaluate its performance
        if closed_trade:
            try:
                # Evaluate the trade performance
                evaluated_trade = self.performance_tracker.evaluate_trade(closed_trade)
                logger.info(
                    f"Trade performance evaluated: {symbol} {closed_trade.get('action')} - "
                    f"Return: {evaluated_trade.get('return_pct', 0):.2f}%, "
                    f"Status: {evaluated_trade.get('status', 'UNKNOWN')}"
                )
            except Exception as e:
                logger.error(f"Error evaluating trade performance: {e}")
        
        return closed_trade
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Get a list of all open positions.
        
        Returns:
            List of open position dictionaries
        """
        return self.trade_book.list_open_trades()
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an open position.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position information or None if no open position
        """
        return self.trade_book.get_open_trade(symbol)
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current portfolio.
        
        Returns:
            Dictionary with portfolio information
        """
        return self.trade_book.get_portfolio_summary()
    
    def _calculate_position_size(self, confidence: int, symbol: Optional[str] = None, market_data: Optional[Dict[str, Any]] = None) -> float:
        """
        Calculate appropriate position size based on configured strategy.
        
        Args:
            confidence: Confidence level (0-100)
            symbol: Trading symbol
            market_data: Market data (for volatility calculation)
            
        Returns:
            Position size (0.0-1.0)
        """
        # Import here to avoid circular imports
        from aGENtrader_v2.agents.position_sizer_agent import PositionSizerAgent
        
        # If we already have a position sizer, use it
        if not hasattr(self, 'position_sizer'):
            self.position_sizer = PositionSizerAgent()
            logger.info("Initialized PositionSizerAgent")
        
        # Extract price data for volatility calculation if available
        price_data = None
        volatility = None
        
        if market_data and "ohlcv" in market_data and market_data["ohlcv"]:
            price_data = market_data["ohlcv"]
        
        # Calculate position size using the position sizer
        position_size = self.position_sizer.calculate_position_size(
            symbol=symbol if symbol is not None else "UNKNOWN",
            confidence=confidence,
            volatility=volatility,
            price_data=price_data
        )
        
        logger.info(f"Position size calculated: {position_size:.2%} for confidence {confidence}")
        
        return position_size
    
    def _calculate_sl_tp(
        self, 
        action: str, 
        entry_price: float
    ) -> tuple[float, float]:
        """
        Calculate stop loss and take profit levels.
        
        Args:
            action: Trade action ('BUY' or 'SELL')
            entry_price: Entry price
            
        Returns:
            Tuple of (stop_loss, take_profit)
        """
        # Different calculation based on position direction
        if action == "BUY":
            stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
            take_profit = entry_price * (1 + self.take_profit_pct / 100)
        else:  # SELL
            stop_loss = entry_price * (1 + self.stop_loss_pct / 100)
            take_profit = entry_price * (1 - self.take_profit_pct / 100)
        
        return stop_loss, take_profit
    
    def _get_current_price(
        self, 
        symbol: Optional[str], 
        market_data: Optional[Dict[str, Any]] = None
    ) -> Optional[float]:
        """
        Get the current price for a symbol.
        
        Args:
            symbol: Trading symbol
            market_data: Market data dictionary (if available)
            
        Returns:
            Current price or None if unavailable
        """
        # Check if symbol is None
        if symbol is None:
            logger.warning("Cannot fetch price for None symbol")
            return None
            
        # First, try to extract from provided market data
        if market_data:
            if "ticker" in market_data and "last" in market_data["ticker"]:
                return market_data["ticker"]["last"]
            
            if "ohlcv" in market_data and market_data["ohlcv"]:
                # Get the close price of the most recent candle
                return market_data["ohlcv"][-1]["close"]
        
        # If not available from market data, try to fetch using the data provider
        if self.data_provider_factory:
            try:
                # If the factory is already a provider, use it directly
                if hasattr(self.data_provider_factory, 'fetch_ticker'):
                    provider = self.data_provider_factory
                # Otherwise, try to create a provider if it has a factory method
                elif hasattr(self.data_provider_factory, 'create_provider'):
                    provider = self.data_provider_factory.create_provider()
                else:
                    logger.error("Data provider factory cannot create a provider or be used as one")
                    return None
                
                # We know symbol is not None due to check at the beginning of the function
                symbol_str = str(symbol).replace("/", "")
                ticker = provider.fetch_ticker(symbol_str)
                return ticker.get("last")
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {e}")
        
        logger.warning(f"Failed to get current price for {symbol}")
        return None
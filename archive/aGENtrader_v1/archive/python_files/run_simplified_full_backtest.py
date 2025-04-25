"""
Simplified Full-Scale Backtesting System

This script implements a full-scale backtesting system that uses simplified agent
architecture but still provides comprehensive analysis and performance tracking.

Key Features:
1. Market data retrieval from the database
2. Technical indicator calculation
3. Simplified decision-making process
4. Performance tracking and analysis
"""

import os
import sys
import json
import logging
import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"data/logs/simplified_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("simplified_full_backtest")

# Make sure data directories exist
os.makedirs("data/logs", exist_ok=True)
os.makedirs("data/backtests", exist_ok=True)
os.makedirs("data/performance", exist_ok=True)

# Import custom modules
from orchestration.simple_decision_session import SimpleDecisionSession
from utils.test_logging import TestLogger, CustomJSONEncoder
from agents.database_retrieval_tool import (
    get_db_connection,
    get_latest_price,
    get_market_data_range,
    get_recent_market_data,
    calculate_moving_average,
    calculate_rsi,
    calculate_volatility,
    find_support_resistance,
    detect_patterns
)

class BacktestPosition:
    """
    Manages a single trading position during backtesting.
    
    Tracks entry/exit points, calculates profit/loss, and handles
    risk management features like stop-loss and take-profit.
    """
    
    def __init__(self, 
                 symbol: str,
                 entry_price: float,
                 position_type: str,  # "long" or "short"
                 entry_time: datetime,
                 position_size: float = 1.0,
                 stop_loss_pct: Optional[float] = None,
                 take_profit_pct: Optional[float] = None):
        """
        Initialize a new position.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            entry_price: Entry price of the position
            position_type: "long" or "short"
            entry_time: Entry timestamp
            position_size: Size of the position (default 1.0 = 100%)
            stop_loss_pct: Optional stop loss percentage
            take_profit_pct: Optional take profit percentage
        """
        self.symbol = symbol
        self.entry_price = entry_price
        self.position_type = position_type.lower()
        self.entry_time = entry_time
        self.position_size = position_size
        
        # Exit information (will be set when position is closed)
        self.exit_price = None
        self.exit_time = None
        self.exit_reason = None
        
        # Risk management levels
        self.stop_loss = None
        self.take_profit = None
        
        # Set stop loss level if provided
        if stop_loss_pct is not None:
            if self.position_type == "long":
                self.stop_loss = entry_price * (1 - stop_loss_pct / 100)
            else:  # short position
                self.stop_loss = entry_price * (1 + stop_loss_pct / 100)
        
        # Set take profit level if provided
        if take_profit_pct is not None:
            if self.position_type == "long":
                self.take_profit = entry_price * (1 + take_profit_pct / 100)
            else:  # short position
                self.take_profit = entry_price * (1 - take_profit_pct / 100)
        
        logger.info(f"Opened {position_type} position at {entry_price:.2f} for {symbol}")
        if self.stop_loss:
            logger.info(f"Stop loss set at {self.stop_loss:.2f}")
        if self.take_profit:
            logger.info(f"Take profit set at {self.take_profit:.2f}")
    
    def check_exit_conditions(self, current_price: float, current_time: datetime) -> Optional[str]:
        """
        Check if position should be closed based on current price.
        
        Args:
            current_price: Current price to evaluate
            current_time: Current timestamp
            
        Returns:
            Exit reason or None if position should stay open
        """
        if self.exit_price:  # Position already closed
            return None
        
        # Check stop loss for long position
        if self.position_type == "long" and self.stop_loss and current_price <= self.stop_loss:
            return "stop_loss"
        
        # Check stop loss for short position
        if self.position_type == "short" and self.stop_loss and current_price >= self.stop_loss:
            return "stop_loss"
        
        # Check take profit for long position
        if self.position_type == "long" and self.take_profit and current_price >= self.take_profit:
            return "take_profit"
        
        # Check take profit for short position
        if self.position_type == "short" and self.take_profit and current_price <= self.take_profit:
            return "take_profit"
        
        return None
    
    def close_position(self, exit_price: float, exit_time: datetime, exit_reason: str) -> Dict[str, Any]:
        """
        Close the position and calculate performance metrics.
        
        Args:
            exit_price: Exit price
            exit_time: Exit timestamp
            exit_reason: Reason for closing position
            
        Returns:
            Dictionary with position details and performance
        """
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.exit_reason = exit_reason
        
        # Calculate profit/loss
        if self.position_type == "long":
            pnl_pct = (exit_price - self.entry_price) / self.entry_price * 100
        else:  # short position
            pnl_pct = (self.entry_price - exit_price) / self.entry_price * 100
            
        # Calculate absolute P&L
        pnl_abs = pnl_pct * self.position_size / 100
        
        # Calculate holding period in hours
        holding_period = (exit_time - self.entry_time).total_seconds() / 3600
        
        logger.info(f"Closed {self.position_type} position at {exit_price:.2f} ({exit_reason})")
        logger.info(f"P&L: {pnl_pct:.2f}% over {holding_period:.1f} hours")
        
        return {
            "symbol": self.symbol,
            "position_type": self.position_type,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat(),
            "exit_reason": self.exit_reason,
            "position_size": self.position_size,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "pnl_pct": pnl_pct,
            "pnl_abs": pnl_abs,
            "holding_period_hours": holding_period
        }
    
    def get_current_metrics(self, current_price: float, current_time: datetime) -> Dict[str, Any]:
        """
        Get current position metrics without closing the position.
        
        Args:
            current_price: Current price
            current_time: Current timestamp
            
        Returns:
            Dictionary with current position metrics
        """
        # Calculate unrealized profit/loss
        if self.position_type == "long":
            unrealized_pnl_pct = (current_price - self.entry_price) / self.entry_price * 100
        else:  # short position
            unrealized_pnl_pct = (self.entry_price - current_price) / self.entry_price * 100
            
        # Calculate absolute P&L
        unrealized_pnl_abs = unrealized_pnl_pct * self.position_size / 100
        
        # Calculate holding period in hours
        holding_period = (current_time - self.entry_time).total_seconds() / 3600
        
        return {
            "symbol": self.symbol,
            "position_type": self.position_type,
            "entry_price": self.entry_price,
            "current_price": current_price,
            "entry_time": self.entry_time.isoformat(),
            "current_time": current_time.isoformat(),
            "position_size": self.position_size,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "unrealized_pnl_abs": unrealized_pnl_abs,
            "holding_period_hours": holding_period,
            "is_open": True
        }

class FullScaleBacktest:
    """
    Full-scale backtesting system implementing the complete trading strategy.
    
    Features:
    - Uses real market data from the database
    - Implements the full decision-making process
    - Tracks performance metrics
    - Supports various risk management features
    """
    
    def __init__(self,
                 symbol: str,
                 interval: str,
                 start_date: datetime,
                 end_date: datetime,
                 initial_balance: float = 10000.0,
                 position_size_pct: float = 100.0,
                 stop_loss_pct: Optional[float] = None,
                 take_profit_pct: Optional[float] = None,
                 trailing_stop: bool = False,
                 verbose: bool = False):
        """
        Initialize the backtesting system.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval for data (e.g., "1h", "4h", "1d")
            start_date: Backtest start date
            end_date: Backtest end date
            initial_balance: Initial account balance
            position_size_pct: Position size as percentage of balance
            stop_loss_pct: Stop loss percentage (optional)
            take_profit_pct: Take profit percentage (optional)
            trailing_stop: Whether to use trailing stop loss
            verbose: Whether to log detailed information
        """
        self.symbol = symbol
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.position_size_pct = position_size_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trailing_stop = trailing_stop
        self.verbose = verbose
        
        # Initialize performance tracking
        self.balance = initial_balance
        self.equity_curve = []
        self.positions = []
        self.open_position = None
        self.trades = []
        self.decisions = []
        
        # Initialize test logger
        self.logger = TestLogger(log_dir="data/logs")
        self.test_id = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize decision session
        self.decision_session = SimpleDecisionSession(symbol=symbol)
        
        # Log initialization
        self.backtest_config = {
            "test_id": self.test_id,
            "symbol": symbol,
            "interval": interval,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "initial_balance": initial_balance,
            "position_size_pct": position_size_pct,
            "stop_loss_pct": stop_loss_pct,
            "take_profit_pct": take_profit_pct,
            "trailing_stop": trailing_stop
        }
        logger.info(f"Initialized backtest {self.test_id} for {symbol} ({interval})")
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        
        # Log configuration
        self.logger.log_session_start("backtest", self.backtest_config)
    
    def run(self) -> Dict[str, Any]:
        """
        Run the backtest over the specified date range.
        
        Returns:
            Dictionary with backtest results
        """
        try:
            # Fetch market data for backtest period
            market_data = self._fetch_market_data()
            if not market_data:
                logger.error("Failed to fetch market data for backtest")
                return {"status": "error", "error": "Failed to fetch market data"}
            
            logger.info(f"Fetched {len(market_data)} data points for backtesting")
            
            # Initialize performance tracking
            self.equity_curve = [{
                "timestamp": self.start_date.isoformat(),
                "balance": self.initial_balance,
                "equity": self.initial_balance,
                "open_position": None
            }]
            
            # Process each data point
            for i, data_point in enumerate(market_data):
                # Get current price and time
                current_price = data_point["close"]
                timestamp = datetime.fromisoformat(data_point["timestamp"].replace("Z", "+00:00"))
                
                # Log progress
                if self.verbose and i % max(1, len(market_data) // 20) == 0:
                    progress = (i / len(market_data)) * 100
                    logger.info(f"Progress: {progress:.1f}% - Processing {timestamp.date()} ({current_price:.2f})")
                
                # Check if we have an open position and evaluate exit conditions
                if self.open_position:
                    exit_reason = self.open_position.check_exit_conditions(current_price, timestamp)
                    
                    if exit_reason:
                        # Close position based on stop loss or take profit
                        trade_result = self.open_position.close_position(
                            exit_price=current_price,
                            exit_time=timestamp,
                            exit_reason=exit_reason
                        )
                        
                        # Update account balance
                        pnl_amount = self.balance * (trade_result["pnl_pct"] / 100) * (self.position_size_pct / 100)
                        self.balance += pnl_amount
                        
                        # Record trade
                        self.trades.append(trade_result)
                        
                        # Clear open position
                        self.open_position = None
                        
                        logger.info(f"Position closed ({exit_reason}) - New balance: ${self.balance:.2f}")
                
                # Calculate technical indicators for current window
                indicators = self._calculate_indicators(market_data[:i+1])
                
                # Create market data for decision making
                decision_market_data = {
                    "latest_price": {
                        "open": data_point["open"],
                        "high": data_point["high"],
                        "low": data_point["low"],
                        "close": data_point["close"],
                        "volume": data_point["volume"],
                        "timestamp": data_point["timestamp"]
                    },
                    "technical_indicators": indicators
                }
                
                # Make trading decision
                decision_result = self.decision_session.run_session({
                    "symbol": self.symbol,
                    "current_price": current_price,
                    "market_data": decision_market_data
                })
                
                # Record decision
                if decision_result["status"] == "completed":
                    decision = {
                        "action": decision_result["action"],
                        "confidence": decision_result["confidence"],
                        "reasoning": decision_result["reasoning"],
                        "timestamp": timestamp.isoformat()
                    }
                    self.decisions.append(decision)
                    
                    if self.verbose:
                        logger.info(f"Decision: {decision['action']} with {decision['confidence']:.1f}% confidence")
                    
                    # Execute trade based on decision
                    if not self.open_position:  # Only consider new trades when no position is open
                        if decision["action"] == "BUY":
                            # Open long position if confidence is high enough (> 60%)
                            if decision["confidence"] > 60:
                                self.open_position = BacktestPosition(
                                    symbol=self.symbol,
                                    entry_price=current_price,
                                    position_type="long",
                                    entry_time=timestamp,
                                    position_size=self.position_size_pct,
                                    stop_loss_pct=self.stop_loss_pct,
                                    take_profit_pct=self.take_profit_pct
                                )
                                logger.info(f"Opened LONG position at ${current_price:.2f}")
                                
                        elif decision["action"] == "SELL":
                            # Open short position if confidence is high enough (> 60%)
                            if decision["confidence"] > 60:
                                self.open_position = BacktestPosition(
                                    symbol=self.symbol,
                                    entry_price=current_price,
                                    position_type="short",
                                    entry_time=timestamp,
                                    position_size=self.position_size_pct,
                                    stop_loss_pct=self.stop_loss_pct,
                                    take_profit_pct=self.take_profit_pct
                                )
                                logger.info(f"Opened SHORT position at ${current_price:.2f}")
                
                # Calculate current equity and get position metrics
                equity = self.balance
                position_metrics = None
                
                if self.open_position:
                    # Get position metrics and calculate unrealized P&L
                    position_metrics = self.open_position.get_current_metrics(current_price, timestamp)
                    unrealized_pnl = self.balance * (position_metrics["unrealized_pnl_pct"] / 100) * (self.position_size_pct / 100)
                    equity += unrealized_pnl
                
                # Update equity curve
                self.equity_curve.append({
                    "timestamp": timestamp.isoformat(),
                    "balance": self.balance,
                    "equity": equity,
                    "price": current_price,
                    "open_position": position_metrics
                })
            
            # Close any remaining open position at the end of the backtest
            if self.open_position:
                last_price = market_data[-1]["close"]
                last_timestamp = datetime.fromisoformat(market_data[-1]["timestamp"].replace("Z", "+00:00"))
                
                trade_result = self.open_position.close_position(
                    exit_price=last_price,
                    exit_time=last_timestamp,
                    exit_reason="backtest_end"
                )
                
                # Update account balance
                pnl_amount = self.balance * (trade_result["pnl_pct"] / 100) * (self.position_size_pct / 100)
                self.balance += pnl_amount
                
                # Record trade
                self.trades.append(trade_result)
                
                logger.info(f"Closed position at end of backtest - Final balance: ${self.balance:.2f}")
            
            # Calculate performance metrics
            metrics = self._calculate_performance_metrics()
            
            # Compile results
            results = {
                "test_id": self.test_id,
                "config": self.backtest_config,
                "metrics": metrics,
                "trades": self.trades,
                "final_balance": self.balance,
                "equity_curve": self.equity_curve,
                "decisions": self.decisions,
                "status": "completed"
            }
            
            # Save backtest results
            self._save_results(results)
            
            # Log completion
            logger.info(f"Backtest completed: {metrics['total_return']:.2f}% gain, {metrics['win_rate']:.1f}% win rate")
            logger.info(f"Total trades: {metrics['total_trades']}, profitable: {metrics['profitable_trades']}")
            
            # Log end of backtest
            self.logger.log_session_end("backtest", {
                "test_id": self.test_id,
                "final_balance": self.balance,
                "metrics": metrics,
                "status": "completed"
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            
            # Log error
            self.logger.log_session_end("backtest", {
                "test_id": self.test_id,
                "error": str(e),
                "status": "error"
            })
            
            return {
                "test_id": self.test_id,
                "status": "error",
                "error": str(e)
            }
    
    def _fetch_market_data(self) -> List[Dict[str, Any]]:
        """
        Fetch market data for the backtest period.
        
        Returns:
            List of market data points
        """
        try:
            # Convert dates to string format
            start_str = self.start_date.strftime("%Y-%m-%d")
            end_str = self.end_date.strftime("%Y-%m-%d")
            
            # Call database function to get market data
            data_json = get_market_data_range(self.symbol, start_str, end_str)
            if not data_json:
                logger.error("No market data returned")
                return []
            
            # Parse JSON response
            data = json.loads(data_json)
            if not data:
                logger.error("Failed to parse market data")
                return []
            
            # Log data structure for debugging
            logger.debug(f"Data structure: {type(data)}")
            logger.debug(f"Data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
            
            # Extract the data points from the response
            if isinstance(data, dict) and "data" in data:
                logger.info(f"Extracted data points from response")
                return data["data"]
            
            # If data is not a dict with a "data" key, ensure we return a list
            if isinstance(data, list):
                return data
            else:
                logger.error(f"Unexpected data format: {type(data)}")
                return []
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return []
    
    def _calculate_indicators(self, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate technical indicators for the current data window.
        
        Args:
            data_points: List of market data points up to current point
            
        Returns:
            Dictionary of technical indicators
        """
        if not data_points or len(data_points) < 2:
            return {}
        
        # For testing and efficiency purposes, return simplified technical indicators
        # This avoids numerous DB calls when backtesting
        try:
            # Get the latest price point
            latest_point = data_points[-1]
            current_price = float(latest_point["close"])
            
            # Create a simple SMA (last 5 prices)
            recent_prices = [float(point["close"]) for point in data_points[-10:]]
            sma_value = sum(recent_prices) / len(recent_prices)
            
            sma = {
                "moving_average": sma_value,
                "window": 10,
                "timestamp": latest_point["timestamp"]
            }
            
            # Create a simple RSI
            # This is a simplified version; real RSI calculation is more complex
            rsi_value = 50.0  # Default neutral value
            if len(data_points) > 10:
                # Simplified RSI - compare current price to average of last 10 points
                avg_price = sum([float(p["close"]) for p in data_points[-10:]]) / 10
                if current_price > avg_price:
                    # Price is above average - higher RSI
                    rsi_value = 60.0 + (current_price - avg_price) / avg_price * 100
                else:
                    # Price is below average - lower RSI  
                    rsi_value = 40.0 - (avg_price - current_price) / avg_price * 100
                
                # Cap RSI between 0 and 100
                rsi_value = max(0, min(100, rsi_value))
            
            rsi = {
                "rsi": rsi_value,
                "period": 14,
                "interpretation": "overbought" if rsi_value > 70 else "oversold" if rsi_value < 30 else "neutral",
                "timestamp": latest_point["timestamp"]
            }
            
            # Create simplified volatility
            if len(data_points) > 5:
                recent_prices = [float(point["close"]) for point in data_points[-5:]]
                avg_price = sum(recent_prices) / len(recent_prices)
                squared_diffs = [(price - avg_price) ** 2 for price in recent_prices]
                variance = sum(squared_diffs) / len(squared_diffs)
                volatility_value = (variance ** 0.5) / avg_price
            else:
                volatility_value = 0.01  # Default low volatility
                
            volatility = {
                "volatility": volatility_value,
                "interpretation": "high" if volatility_value > 0.03 else "medium" if volatility_value > 0.01 else "low",
                "timestamp": latest_point["timestamp"]
            }
            
            # Create support/resistance levels
            support_levels = []
            resistance_levels = []
            
            if len(data_points) > 20:
                # Find min/max in the last 20 points for support/resistance
                prices = [float(point["close"]) for point in data_points[-20:]]
                min_price = min(prices)
                max_price = max(prices)
                
                # Add simple support/resistance levels
                support_levels = [min_price, min_price * 0.98]
                resistance_levels = [max_price, max_price * 1.02]
            
            support_resistance = {
                "support_levels": support_levels,
                "resistance_levels": resistance_levels,
                "current_price": current_price,
                "timestamp": latest_point["timestamp"]
            }
            
            # Simplified pattern detection (just check for simple trends)
            patterns = []
            if len(data_points) > 5:
                recent_closes = [float(point["close"]) for point in data_points[-5:]]
                
                # Check for uptrend (each price higher than previous)
                if all(recent_closes[i] < recent_closes[i+1] for i in range(len(recent_closes)-1)):
                    patterns.append({
                        "name": "Uptrend",
                        "confidence": 0.7,
                        "description": "Price showing consistent higher highs"
                    })
                
                # Check for downtrend (each price lower than previous)
                if all(recent_closes[i] > recent_closes[i+1] for i in range(len(recent_closes)-1)):
                    patterns.append({
                        "name": "Downtrend",
                        "confidence": 0.7,
                        "description": "Price showing consistent lower lows"
                    })
            
            patterns_data = {
                "patterns": patterns,
                "timestamp": latest_point["timestamp"]
            }
            
            # Combine indicators
            return {
                "sma": sma,
                "rsi": rsi,
                "volatility": volatility,
                "support_resistance": support_resistance,
                "patterns": patterns_data
            }
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return {}
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate performance metrics for the backtest.
        
        Returns:
            Dictionary of performance metrics
        """
        metrics = {}
        
        # Basic metrics
        initial_balance = self.initial_balance
        final_balance = self.balance
        
        metrics["initial_balance"] = initial_balance
        metrics["final_balance"] = final_balance
        metrics["absolute_return"] = final_balance - initial_balance
        metrics["total_return"] = ((final_balance / initial_balance) - 1) * 100
        
        # Trading metrics
        trades = self.trades
        metrics["total_trades"] = len(trades)
        
        if trades:
            # Win/loss metrics
            profitable_trades = [t for t in trades if t["pnl_pct"] > 0]
            losing_trades = [t for t in trades if t["pnl_pct"] <= 0]
            
            metrics["profitable_trades"] = len(profitable_trades)
            metrics["losing_trades"] = len(losing_trades)
            
            if metrics["total_trades"] > 0:
                metrics["win_rate"] = (metrics["profitable_trades"] / metrics["total_trades"]) * 100
            else:
                metrics["win_rate"] = 0
            
            # Average metrics
            if profitable_trades:
                metrics["avg_profit"] = sum(t["pnl_pct"] for t in profitable_trades) / len(profitable_trades)
            else:
                metrics["avg_profit"] = 0
                
            if losing_trades:
                metrics["avg_loss"] = sum(t["pnl_pct"] for t in losing_trades) / len(losing_trades)
            else:
                metrics["avg_loss"] = 0
            
            # Max metrics
            metrics["max_profit"] = max([t["pnl_pct"] for t in trades]) if trades else 0
            metrics["max_loss"] = min([t["pnl_pct"] for t in trades]) if trades else 0
            
            # Profit factor
            total_profit = sum(t["pnl_pct"] for t in profitable_trades) if profitable_trades else 0
            total_loss = abs(sum(t["pnl_pct"] for t in losing_trades)) if losing_trades else 0
            
            if total_loss > 0:
                metrics["profit_factor"] = total_profit / total_loss
            else:
                metrics["profit_factor"] = total_profit if total_profit > 0 else 0
            
            # Average hold time
            hold_times = [(datetime.fromisoformat(t["exit_time"]) - datetime.fromisoformat(t["entry_time"])).total_seconds() / 3600 for t in trades]
            metrics["avg_hold_time"] = sum(hold_times) / len(hold_times) if hold_times else 0
        
        else:
            # No trades
            metrics["profitable_trades"] = 0
            metrics["losing_trades"] = 0
            metrics["win_rate"] = 0
            metrics["avg_profit"] = 0
            metrics["avg_loss"] = 0
            metrics["max_profit"] = 0
            metrics["max_loss"] = 0
            metrics["profit_factor"] = 0
            metrics["avg_hold_time"] = 0
        
        # Calculate Sharpe Ratio (using equity curve)
        if len(self.equity_curve) > 1:
            # Calculate daily returns
            equity_values = [point["equity"] for point in self.equity_curve]
            returns = [(equity_values[i] / equity_values[i-1]) - 1 for i in range(1, len(equity_values))]
            
            avg_return = sum(returns) / len(returns)
            std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            
            if std_return > 0:
                # Annualize based on number of periods
                # Assuming 252 trading days per year
                periods_per_year = 252
                if self.interval == "1h":
                    periods_per_year = 252 * 24
                elif self.interval == "4h":
                    periods_per_year = 252 * 6
                elif self.interval == "1d":
                    periods_per_year = 252
                
                sharpe_ratio = (avg_return / std_return) * (periods_per_year ** 0.5)
                metrics["sharpe_ratio"] = sharpe_ratio
            else:
                metrics["sharpe_ratio"] = 0 if avg_return == 0 else float('inf') if avg_return > 0 else float('-inf')
        else:
            metrics["sharpe_ratio"] = 0
        
        # Calculate maximum drawdown
        if len(self.equity_curve) > 1:
            equity_values = [point["equity"] for point in self.equity_curve]
            max_drawdown = 0
            peak = equity_values[0]
            
            for value in equity_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)
            
            metrics["max_drawdown"] = max_drawdown
        else:
            metrics["max_drawdown"] = 0
        
        return metrics
    
    def _save_results(self, results: Dict[str, Any]) -> None:
        """
        Save backtest results to file.
        
        Args:
            results: Dictionary of backtest results
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs("data/backtests", exist_ok=True)
            
            # Save full results
            output_file = f"data/backtests/backtest_{self.test_id}.json"
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2, cls=CustomJSONEncoder)
            
            logger.info(f"Saved backtest results to {output_file}")
            
            # Save summary results (without full equity curve)
            summary = {
                "test_id": results["test_id"],
                "config": results["config"],
                "metrics": results["metrics"],
                "trades_count": len(results["trades"]),
                "final_balance": results["final_balance"],
                "status": results["status"]
            }
            
            summary_file = f"data/backtests/summary_{self.test_id}.json"
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2, cls=CustomJSONEncoder)
            
            logger.info(f"Saved backtest summary to {summary_file}")
            
        except Exception as e:
            logger.error(f"Error saving backtest results: {str(e)}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run a full-scale backtest of the trading system")
    
    parser.add_argument("--symbol", type=str, default="BTCUSDT",
                        help="Trading symbol (default: BTCUSDT)")
    parser.add_argument("--interval", type=str, default="4h",
                        help="Time interval (default: 4h)")
    parser.add_argument("--start_date", type=str, required=True,
                        help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end_date", type=str, required=True,
                        help="End date in YYYY-MM-DD format")
    parser.add_argument("--initial_balance", type=float, default=10000.0,
                        help="Initial account balance (default: 10000.0)")
    parser.add_argument("--position_size", type=float, default=100.0,
                        help="Position size as percentage of balance (default: 100.0)")
    parser.add_argument("--use_stop_loss", action="store_true",
                        help="Enable stop loss")
    parser.add_argument("--stop_loss_pct", type=float, default=5.0,
                        help="Stop loss percentage (default: 5.0)")
    parser.add_argument("--use_take_profit", action="store_true",
                        help="Enable take profit")
    parser.add_argument("--take_profit_pct", type=float, default=10.0,
                        help="Take profit percentage (default: 10.0)")
    parser.add_argument("--trailing_stop", action="store_true",
                        help="Enable trailing stop loss")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")
    
    return parser.parse_args()

def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Parse dates
    try:
        start_date = datetime.fromisoformat(args.start_date)
        end_date = datetime.fromisoformat(args.end_date)
    except ValueError:
        logger.error("Invalid date format. Use YYYY-MM-DD.")
        return 1
    
    # Set up stop loss and take profit
    stop_loss_pct = args.stop_loss_pct if args.use_stop_loss else None
    take_profit_pct = args.take_profit_pct if args.use_take_profit else None
    
    # Log execution parameters
    logger.info(f"Starting backtest for {args.symbol} ({args.interval}) from {args.start_date} to {args.end_date}")
    logger.info(f"Initial balance: ${args.initial_balance:.2f}, Position size: {args.position_size:.1f}%")
    if stop_loss_pct:
        logger.info(f"Stop loss: {stop_loss_pct:.1f}%")
    if take_profit_pct:
        logger.info(f"Take profit: {take_profit_pct:.1f}%")
    if args.trailing_stop:
        logger.info("Trailing stop enabled")
    
    # Initialize and run backtest
    backtest = FullScaleBacktest(
        symbol=args.symbol,
        interval=args.interval,
        start_date=start_date,
        end_date=end_date,
        initial_balance=args.initial_balance,
        position_size_pct=args.position_size,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        trailing_stop=args.trailing_stop,
        verbose=args.verbose
    )
    
    # Run the backtest
    results = backtest.run()
    
    # Check for errors
    if results.get("status") == "error":
        logger.error(f"Backtest failed: {results.get('error')}")
        return 1
    
    # Display summary results
    metrics = results.get("metrics", {})
    
    print("\n" + "="*50)
    print(f"BACKTEST SUMMARY: {args.symbol} ({args.interval})")
    print("="*50)
    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Initial Balance: ${args.initial_balance:.2f}")
    print(f"Final Balance: ${metrics.get('final_balance', 0):.2f}")
    print(f"Total Return: {metrics.get('total_return', 0):.2f}%")
    print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
    print("-"*50)
    print(f"Total Trades: {metrics.get('total_trades', 0)}")
    print(f"Win Rate: {metrics.get('win_rate', 0):.1f}%")
    print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    print(f"Avg Profit: {metrics.get('avg_profit', 0):.2f}%")
    print(f"Avg Loss: {metrics.get('avg_loss', 0):.2f}%")
    print(f"Max Profit: {metrics.get('max_profit', 0):.2f}%")
    print(f"Max Loss: {metrics.get('max_loss', 0):.2f}%")
    print(f"Avg Hold Time: {metrics.get('avg_hold_time', 0):.1f} hours")
    print("="*50)
    print(f"Results saved to: data/backtests/backtest_{results.get('test_id')}.json")
    print("="*50 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
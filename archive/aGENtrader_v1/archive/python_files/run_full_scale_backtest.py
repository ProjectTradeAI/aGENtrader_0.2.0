"""
Full-Scale Backtesting System

This script implements a full-scale backtesting system that utilizes the entire multi-agent
trading architecture, including:

1. Market data retrieval from the database
2. Multi-agent analysis with specialized agents
3. Trading decision-making using the orchestration framework
4. Performance tracking and analysis

This backtesting system provides a more realistic assessment of the trading system's
performance compared to simplified rule-based backtests.
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
        logging.FileHandler(f"data/logs/full_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("full_scale_backtest")

# Make sure data directories exist
os.makedirs("data/logs", exist_ok=True)
os.makedirs("data/backtests", exist_ok=True)
os.makedirs("data/performance", exist_ok=True)

# Import custom modules
from orchestration.decision_session_fixed import DecisionSession
from utils.test_logging import TestLogger, CustomJSONEncoder
from agents.database_retrieval_tool import (
    get_db_connection,
    get_latest_price,
    get_market_data_range,
    get_recent_market_data,
    CustomJSONEncoder
)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Full-scale multi-agent backtesting system")
    
    # Trading parameters
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--interval", type=str, default="1h", help="Candle interval (1m, 15m, 1h, 4h, 1d)")
    parser.add_argument("--start_date", type=str, default=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                        help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, default=datetime.now().strftime("%Y-%m-%d"),
                        help="End date (YYYY-MM-DD)")
    
    # Trading strategy parameters
    parser.add_argument("--initial_balance", type=float, default=10000.0, help="Initial balance in USD")
    parser.add_argument("--risk_per_trade", type=float, default=0.02, help="Risk per trade (percentage of balance)")
    parser.add_argument("--max_position_size", type=float, default=0.5, help="Maximum position size (percentage of balance)")
    parser.add_argument("--use_stop_loss", action="store_true", help="Use stop-loss orders")
    parser.add_argument("--stop_loss_pct", type=float, default=0.02, help="Stop-loss percentage")
    parser.add_argument("--use_take_profit", action="store_true", help="Use take-profit orders")
    parser.add_argument("--take_profit_pct", type=float, default=0.04, help="Take-profit percentage")
    
    # Backtest parameters
    parser.add_argument("--output_file", type=str, help="Output file for results (JSON)")
    parser.add_argument("--decision_interval", type=int, default=24, 
                        help="Interval between trading decisions (in candles)")
    parser.add_argument("--min_confidence", type=float, default=65.0, 
                        help="Minimum confidence threshold for taking action (0-100)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    return parser.parse_args()

class BacktestPosition:
    """Class representing a position in the backtest"""
    
    def __init__(self, symbol: str, entry_price: float, entry_time: datetime, 
                 amount: float, direction: str, stop_loss: Optional[float] = None,
                 take_profit: Optional[float] = None):
        """
        Initialize a backtest position.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            entry_time: Entry timestamp
            amount: Position size (in base currency)
            direction: Position direction ("long" or "short")
            stop_loss: Stop-loss price (optional)
            take_profit: Take-profit price (optional)
        """
        self.symbol = symbol
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.amount = amount
        self.direction = direction.lower()
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.exit_price = None
        self.exit_time = None
        self.exit_reason = None
        self.pnl = 0.0
        self.pnl_pct = 0.0
        self.status = "open"
    
    def close_position(self, exit_price: float, exit_time: datetime, reason: str):
        """
        Close the position.
        
        Args:
            exit_price: Exit price
            exit_time: Exit timestamp
            reason: Reason for closing the position
        """
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.exit_reason = reason
        self.status = "closed"
        
        # Calculate PnL
        if self.direction == "long":
            self.pnl = self.amount * (exit_price - self.entry_price)
            self.pnl_pct = (exit_price / self.entry_price - 1) * 100
        else:  # short
            self.pnl = self.amount * (self.entry_price - exit_price)
            self.pnl_pct = (self.entry_price / exit_price - 1) * 100
    
    def check_exit_conditions(self, current_price: float, current_time: datetime) -> bool:
        """
        Check if the position should be closed based on stop-loss or take-profit.
        
        Args:
            current_price: Current market price
            current_time: Current timestamp
            
        Returns:
            True if position should be closed, False otherwise
        """
        if self.status != "open":
            return False
        
        # Check stop-loss
        if self.stop_loss is not None:
            if (self.direction == "long" and current_price <= self.stop_loss) or \
               (self.direction == "short" and current_price >= self.stop_loss):
                self.close_position(self.stop_loss, current_time, "stop_loss")
                return True
        
        # Check take-profit
        if self.take_profit is not None:
            if (self.direction == "long" and current_price >= self.take_profit) or \
               (self.direction == "short" and current_price <= self.take_profit):
                self.close_position(self.take_profit, current_time, "take_profit")
                return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert position to dictionary.
        
        Returns:
            Dictionary representation of the position
        """
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "amount": self.amount,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_reason": self.exit_reason,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "status": self.status
        }

class FullScaleBacktest:
    """Full-scale backtesting system using multi-agent architecture"""
    
    def __init__(self, args):
        """
        Initialize the backtesting system.
        
        Args:
            args: Command line arguments
        """
        self.args = args
        self.symbol = args.symbol
        self.interval = args.interval
        self.start_date = args.start_date
        self.end_date = args.end_date
        self.initial_balance = args.initial_balance
        self.balance = args.initial_balance
        self.equity = args.initial_balance
        self.risk_per_trade = args.risk_per_trade
        self.max_position_size = args.max_position_size
        self.use_stop_loss = args.use_stop_loss
        self.stop_loss_pct = args.stop_loss_pct
        self.use_take_profit = args.use_take_profit
        self.take_profit_pct = args.take_profit_pct
        self.decision_interval = args.decision_interval
        self.min_confidence = args.min_confidence
        self.verbose = args.verbose
        
        # Trading data
        self.positions = []
        self.current_position = None
        self.trades = []
        self.equity_curve = []
        self.decisions = []
        
        # Results
        self.results = {}
        
        # Test logger
        self.test_logger = TestLogger(log_dir="data/logs", prefix="full_backtest")
        self.test_id = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Report if using decision-making thresholds
        if self.min_confidence > 0:
            logger.info(f"Using confidence threshold: {self.min_confidence}%")
    
    async def run(self) -> Dict[str, Any]:
        """
        Run the full-scale backtest.
        
        Returns:
            Results dictionary
        """
        # Log backtest start
        logger.info(f"Starting full-scale backtest for {self.symbol} from {self.start_date} to {self.end_date}")
        logger.info(f"Initial balance: ${self.initial_balance:.2f}, Risk per trade: {self.risk_per_trade:.1%}")
        
        # Validate date range
        try:
            start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
            
            if start_date >= end_date:
                logger.error("Start date must be before end date")
                return {"status": "error", "error": "Start date must be before end date"}
        except ValueError as e:
            logger.error(f"Invalid date format: {str(e)}")
            return {"status": "error", "error": f"Invalid date format: {str(e)}"}
        
        # Get market data for the backtest period
        candles = await self.get_historical_data()
        if not candles:
            logger.error(f"No historical data available for {self.symbol} in the specified date range")
            return {"status": "error", "error": "No historical data available"}
        
        # Log data range
        logger.info(f"Loaded {len(candles)} candles for {self.symbol} ({self.interval})")
        logger.info(f"Data range: {candles[0]['timestamp']} to {candles[-1]['timestamp']}")
        
        # Run the backtest
        await self.run_backtest(candles)
        
        # Calculate and log results
        self.results = self.calculate_results()
        self.log_results()
        
        # Save results if output file specified
        if self.args.output_file:
            self.save_results(self.args.output_file)
        
        return self.results
    
    async def get_historical_data(self) -> List[Dict[str, Any]]:
        """
        Get historical market data for the backtest period.
        
        Returns:
            List of candles (OHLCV data)
        """
        try:
            # Get market data from database
            data_json = get_market_data_range(
                self.symbol, 
                start_time=self.start_date, 
                end_time=self.end_date
            )
            
            if not data_json:
                logger.error("Failed to retrieve market data")
                return []
            
            data = json.loads(data_json)
            
            if not data or "data" not in data or not data["data"]:
                logger.error("No data available in the specified range")
                return []
            
            # Sort by timestamp
            candles = data["data"]
            candles.sort(key=lambda x: x["timestamp"])
            
            return candles
        except Exception as e:
            logger.error(f"Error retrieving historical data: {str(e)}")
            return []
    
    async def run_backtest(self, candles: List[Dict[str, Any]]) -> None:
        """
        Run the backtest on the provided candles.
        
        Args:
            candles: List of candles (OHLCV data)
        """
        # Initialize decision session
        decision_session = DecisionSession(symbol=self.symbol, track_performance=True)
        
        # Track equity at each candle
        self.equity_curve = []
        candle_count = 0
        
        # Log start
        logger.info(f"Running backtest with {len(candles)} candles and decision interval of {self.decision_interval} candles")
        
        # Main backtest loop
        for i, candle in enumerate(candles):
            current_time = datetime.fromisoformat(candle["timestamp"].replace("Z", "+00:00"))
            current_price = float(candle["close"])
            
            # Update equity curve
            self.update_equity(current_time, current_price)
            
            # Check if we have an open position and if it should be closed
            if self.current_position and self.current_position.status == "open":
                was_closed = self.current_position.check_exit_conditions(current_price, current_time)
                if was_closed:
                    # Position was closed due to stop-loss or take-profit
                    if self.verbose:
                        logger.info(f"Position closed at ${current_price:.2f} due to {self.current_position.exit_reason}")
                    
                    # Update account balance
                    self.balance += self.current_position.pnl
                    self.trades.append(self.current_position.to_dict())
                    self.current_position = None
            
            # Make trading decision at regular intervals
            candle_count += 1
            if candle_count >= self.decision_interval or i == len(candles) - 1:
                candle_count = 0
                
                if self.verbose:
                    logger.info(f"Making trading decision at {current_time.isoformat()} (${current_price:.2f})")
                
                # Run decision session
                session_result = await self.run_decision_session(decision_session, current_time, current_price)
                
                # Save decision
                self.decisions.append({
                    "timestamp": current_time.isoformat(),
                    "price": current_price,
                    "decision": session_result
                })
                
                # Process trading decision
                self.process_decision(session_result, current_time, current_price)
        
        # Close any remaining open position at the end of the backtest
        if self.current_position and self.current_position.status == "open":
            last_candle = candles[-1]
            last_price = float(last_candle["close"])
            last_time = datetime.fromisoformat(last_candle["timestamp"].replace("Z", "+00:00"))
            
            self.current_position.close_position(last_price, last_time, "backtest_end")
            self.balance += self.current_position.pnl
            self.trades.append(self.current_position.to_dict())
            
            if self.verbose:
                logger.info(f"Closing position at end of backtest: ${last_price:.2f}, PnL: ${self.current_position.pnl:.2f}")
            
            self.current_position = None
        
        # Log completion
        logger.info(f"Backtest completed with {len(self.trades)} trades")
    
    async def run_decision_session(self, decision_session: DecisionSession, 
                                   current_time: datetime, current_price: float) -> Dict[str, Any]:
        """
        Run a decision session to determine the trading action.
        
        Args:
            decision_session: Decision session instance
            current_time: Current timestamp
            current_price: Current price
            
        Returns:
            Decision session result
        """
        try:
            # Run the decision session
            result = decision_session.run_session(self.symbol, current_price)
            
            # Process the decision
            if not result or "status" not in result or result["status"] != "completed":
                logger.warning(f"Decision session failed: {result.get('error', 'Unknown error')}")
                return {
                    "action": "HOLD",
                    "confidence": 0.0,
                    "price": current_price,
                    "risk_level": "medium",
                    "reasoning": "Decision session failed",
                    "timestamp": current_time.isoformat()
                }
            
            # Log decision
            decision = result["decision"]
            action = decision.get("action", "HOLD")
            confidence = decision.get("confidence", 0.0)
            risk_level = decision.get("risk_level", "medium")
            
            if self.verbose:
                logger.info(f"Decision: {action} with {confidence:.1f}% confidence, Risk: {risk_level}")
            
            return decision
        except Exception as e:
            logger.error(f"Error in decision session: {str(e)}")
            return {
                "action": "HOLD",
                "confidence": 0.0,
                "price": current_price,
                "risk_level": "medium",
                "reasoning": f"Error: {str(e)}",
                "timestamp": current_time.isoformat()
            }
    
    def process_decision(self, decision: Dict[str, Any], current_time: datetime, current_price: float) -> None:
        """
        Process a trading decision.
        
        Args:
            decision: Decision data
            current_time: Current timestamp
            current_price: Current price
        """
        action = decision.get("action", "HOLD").upper()
        confidence = float(decision.get("confidence", 0.0))
        risk_level = decision.get("risk_level", "medium").lower()
        
        # Check confidence threshold
        if confidence < self.min_confidence:
            if self.verbose:
                logger.info(f"Confidence too low: {confidence:.1f}% < {self.min_confidence:.1f}%, holding")
            return
        
        # Process buy/sell signals
        if action == "BUY" and (self.current_position is None or self.current_position.direction == "short"):
            # Close existing position if it's in the opposite direction
            if self.current_position and self.current_position.status == "open":
                self.current_position.close_position(current_price, current_time, "reverse_position")
                self.balance += self.current_position.pnl
                self.trades.append(self.current_position.to_dict())
                
                if self.verbose:
                    logger.info(f"Closed short position at ${current_price:.2f}, PnL: ${self.current_position.pnl:.2f}")
            
            # Open new long position
            self.open_position("long", current_price, current_time, risk_level)
            
        elif action == "SELL" and (self.current_position is None or self.current_position.direction == "long"):
            # Close existing position if it's in the opposite direction
            if self.current_position and self.current_position.status == "open":
                self.current_position.close_position(current_price, current_time, "reverse_position")
                self.balance += self.current_position.pnl
                self.trades.append(self.current_position.to_dict())
                
                if self.verbose:
                    logger.info(f"Closed long position at ${current_price:.2f}, PnL: ${self.current_position.pnl:.2f}")
            
            # Open new short position
            self.open_position("short", current_price, current_time, risk_level)
            
        elif action == "HOLD" or (action == "BUY" and self.current_position and self.current_position.direction == "long") or \
             (action == "SELL" and self.current_position and self.current_position.direction == "short"):
            # Either explicit hold or redundant buy/sell signal (already in that position)
            if self.verbose:
                position_state = "no position" if not self.current_position else f"already {self.current_position.direction}"
                logger.info(f"Holding ({position_state})")
    
    def open_position(self, direction: str, price: float, timestamp: datetime, risk_level: str = "medium") -> None:
        """
        Open a new position.
        
        Args:
            direction: Position direction ("long" or "short")
            price: Entry price
            timestamp: Entry timestamp
            risk_level: Risk level ("low", "medium", "high")
        """
        # Calculate position size based on risk level and risk per trade
        risk_multiplier = 0.5 if risk_level == "low" else 1.0 if risk_level == "medium" else 1.5
        position_size_pct = min(self.risk_per_trade * risk_multiplier, self.max_position_size)
        position_size_usd = self.balance * position_size_pct
        position_size = position_size_usd / price
        
        # Calculate stop-loss and take-profit levels
        stop_loss = None
        take_profit = None
        
        if self.use_stop_loss:
            sl_multiplier = 0.5 if risk_level == "low" else 1.0 if risk_level == "medium" else 1.5
            sl_pct = self.stop_loss_pct * sl_multiplier
            
            if direction == "long":
                stop_loss = price * (1 - sl_pct)
            else:
                stop_loss = price * (1 + sl_pct)
        
        if self.use_take_profit:
            tp_multiplier = 1.5 if risk_level == "low" else 1.0 if risk_level == "medium" else 0.75
            tp_pct = self.take_profit_pct * tp_multiplier
            
            if direction == "long":
                take_profit = price * (1 + tp_pct)
            else:
                take_profit = price * (1 - tp_pct)
        
        # Create position
        self.current_position = BacktestPosition(
            symbol=self.symbol,
            entry_price=price,
            entry_time=timestamp,
            amount=position_size,
            direction=direction,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Log position
        if self.verbose:
            direction_str = "Long" if direction == "long" else "Short"
            sl_str = f", SL: ${stop_loss:.2f}" if stop_loss else ""
            tp_str = f", TP: ${take_profit:.2f}" if take_profit else ""
            logger.info(f"Opening {direction_str} position: ${price:.2f}, Size: ${position_size_usd:.2f}{sl_str}{tp_str}")
    
    def update_equity(self, timestamp: datetime, current_price: float) -> None:
        """
        Update equity curve with current account value.
        
        Args:
            timestamp: Current timestamp
            current_price: Current price
        """
        # Calculate current equity (balance + unrealized P&L)
        equity = self.balance
        
        if self.current_position and self.current_position.status == "open":
            # Calculate unrealized P&L
            position_size = self.current_position.amount
            entry_price = self.current_position.entry_price
            
            if self.current_position.direction == "long":
                unrealized_pnl = position_size * (current_price - entry_price)
            else:
                unrealized_pnl = position_size * (entry_price - current_price)
            
            equity += unrealized_pnl
        
        self.equity = equity
        
        # Add to equity curve
        self.equity_curve.append({
            "timestamp": timestamp.isoformat(),
            "equity": equity,
            "balance": self.balance,
            "price": current_price
        })
    
    def calculate_results(self) -> Dict[str, Any]:
        """
        Calculate backtest results.
        
        Returns:
            Results dictionary
        """
        # Basic statistics
        total_trades = len(self.trades)
        if total_trades == 0:
            return {
                "symbol": self.symbol,
                "interval": self.interval,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "initial_balance": self.initial_balance,
                "final_balance": self.balance,
                "net_profit": 0.0,
                "net_profit_pct": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_profit": 0.0,
                "avg_loss": 0.0,
                "max_drawdown": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
                "trades": [],
                "equity_curve": self.equity_curve
            }
        
        # Calculate trade statistics
        winning_trades = [trade for trade in self.trades if trade["pnl"] > 0]
        losing_trades = [trade for trade in self.trades if trade["pnl"] <= 0]
        
        num_winning = len(winning_trades)
        num_losing = len(losing_trades)
        
        win_rate = num_winning / total_trades if total_trades > 0 else 0.0
        
        gross_profit = sum(trade["pnl"] for trade in winning_trades)
        gross_loss = sum(trade["pnl"] for trade in losing_trades)
        
        avg_profit = gross_profit / num_winning if num_winning > 0 else 0.0
        avg_loss = gross_loss / num_losing if num_losing > 0 else 0.0
        
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')
        
        # Calculate drawdown
        max_equity = self.initial_balance
        max_drawdown = 0.0
        
        for point in self.equity_curve:
            equity = point["equity"]
            max_equity = max(max_equity, equity)
            drawdown = (max_equity - equity) / max_equity
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate Sharpe ratio (simplified)
        if len(self.equity_curve) > 1:
            equity_values = [point["equity"] for point in self.equity_curve]
            returns = [(equity_values[i] / equity_values[i-1]) - 1 for i in range(1, len(equity_values))]
            
            if returns:
                avg_return = sum(returns) / len(returns)
                std_dev = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
                sharpe_ratio = (avg_return / std_dev) * (252 ** 0.5) if std_dev > 0 else 0.0
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        # Decision analysis
        decision_analysis = self.analyze_decisions()
        
        # Results dictionary
        results = {
            "symbol": self.symbol,
            "interval": self.interval,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_balance": self.initial_balance,
            "final_balance": self.balance,
            "net_profit": self.balance - self.initial_balance,
            "net_profit_pct": (self.balance / self.initial_balance - 1) * 100,
            "total_trades": total_trades,
            "winning_trades": num_winning,
            "losing_trades": num_losing,
            "win_rate": win_rate * 100,
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
            "max_drawdown": max_drawdown * 100,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "trades": self.trades,
            "equity_curve": self.equity_curve[::(len(self.equity_curve)//1000 + 1)],  # Downsample for efficiency
            "decisions": self.decisions,
            "decision_analysis": decision_analysis
        }
        
        return results
    
    def analyze_decisions(self) -> Dict[str, Any]:
        """
        Analyze the quality of trading decisions.
        
        Returns:
            Decision analysis statistics
        """
        if not self.decisions:
            return {
                "total_decisions": 0,
                "buy_decisions": 0,
                "sell_decisions": 0,
                "hold_decisions": 0,
                "avg_confidence": 0.0,
                "decisions_by_risk_level": {"low": 0, "medium": 0, "high": 0}
            }
        
        # Count decision types
        buy_decisions = [d for d in self.decisions if d["decision"].get("action", "").upper() == "BUY"]
        sell_decisions = [d for d in self.decisions if d["decision"].get("action", "").upper() == "SELL"]
        hold_decisions = [d for d in self.decisions if d["decision"].get("action", "").upper() == "HOLD"]
        
        # Get average confidence
        confidence_values = [float(d["decision"].get("confidence", 0)) for d in self.decisions 
                              if "confidence" in d["decision"]]
        avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
        
        # Count by risk level
        risk_levels = ["low", "medium", "high"]
        decisions_by_risk = {level: len([d for d in self.decisions 
                                          if d["decision"].get("risk_level", "").lower() == level])
                              for level in risk_levels}
        
        # Calculate action accuracy
        # (This would require more sophisticated tracking of decision outcomes, 
        # which can be added in a future enhancement)
        
        return {
            "total_decisions": len(self.decisions),
            "buy_decisions": len(buy_decisions),
            "sell_decisions": len(sell_decisions),
            "hold_decisions": len(hold_decisions),
            "avg_confidence": avg_confidence,
            "decisions_by_risk_level": decisions_by_risk
        }
    
    def log_results(self) -> None:
        """Log backtest results summary"""
        logger.info("=" * 50)
        logger.info(" BACKTEST RESULTS ")
        logger.info("=" * 50)
        
        results = self.results
        
        logger.info(f"Symbol: {results['symbol']}, Interval: {results['interval']}")
        logger.info(f"Period: {results['start_date']} to {results['end_date']}")
        logger.info(f"Initial Balance: ${results['initial_balance']:.2f}")
        logger.info(f"Final Balance: ${results['final_balance']:.2f}")
        logger.info(f"Net Profit: ${results['net_profit']:.2f} ({results['net_profit_pct']:.2f}%)")
        logger.info(f"Total Trades: {results['total_trades']}")
        logger.info(f"Win Rate: {results['win_rate']:.2f}%")
        logger.info(f"Average Profit: ${results['avg_profit']:.2f}")
        logger.info(f"Average Loss: ${results['avg_loss']:.2f}")
        logger.info(f"Profit Factor: {results['profit_factor']:.2f}")
        logger.info(f"Maximum Drawdown: {results['max_drawdown']:.2f}%")
        logger.info(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        
        # Decision analysis
        if "decision_analysis" in results:
            analysis = results["decision_analysis"]
            logger.info("\nDecision Analysis:")
            logger.info(f"Total Decisions: {analysis['total_decisions']}")
            logger.info(f"Buy Decisions: {analysis['buy_decisions']}")
            logger.info(f"Sell Decisions: {analysis['sell_decisions']}")
            logger.info(f"Hold Decisions: {analysis['hold_decisions']}")
            logger.info(f"Average Confidence: {analysis['avg_confidence']:.2f}%")
        
        logger.info("=" * 50)
    
    def save_results(self, output_file: str) -> None:
        """
        Save backtest results to a file.
        
        Args:
            output_file: Output file path
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Save results to file
            with open(output_file, "w") as f:
                json.dump(self.results, f, cls=CustomJSONEncoder, indent=2)
            
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")

async def main():
    """Main entry point"""
    # Parse arguments
    args = parse_arguments()
    
    # Create backtest instance
    backtest = FullScaleBacktest(args)
    
    # Run backtest
    try:
        results = await backtest.run()
        
        # Check if output file is specified
        if not args.output_file and results.get("status") != "error":
            # Generate default output file name
            output_dir = "data/backtests"
            os.makedirs(output_dir, exist_ok=True)
            
            output_file = os.path.join(
                output_dir, 
                f"full_backtest_{args.symbol}_{args.interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            backtest.save_results(output_file)
        
        # Return success
        return 0
    except Exception as e:
        logger.error(f"Error running backtest: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    # Configure asyncio event loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
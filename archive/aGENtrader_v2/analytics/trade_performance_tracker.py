#!/usr/bin/env python
"""
TradePerformanceTracker for aGENtrader v2.1

This module evaluates trade performance using actual price data, 
tracks key metrics, and generates summary reports for trading performance analysis.
"""

import json
import logging
import math
import os
import statistics
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

import yaml

# Setup logger
logger = logging.getLogger("aGENtrader.performance_tracker")

class TradePerformanceTracker:
    """
    Tracks and analyzes the performance of executed trades.
    
    Key responsibilities:
    - Calculate profit/loss for closed trades
    - Track unrealized PnL for open trades
    - Generate performance metrics (win rate, avg return, profit factor)
    - Log detailed trade performance data
    - Produce summary reports for analysis
    """
    
    def __init__(
        self, 
        data_provider=None, 
        trade_log_path: str = "logs/performance/trade_performance.jsonl",
        summary_path: str = "reports/performance_summary.json"
    ):
        """
        Initialize the trade performance tracker.
        
        Args:
            data_provider: Data provider for fetching market prices
            trade_log_path: Path to store detailed trade performance logs
            summary_path: Path to store performance summary data
        """
        # If no data provider is specified, try to create one from environment
        if data_provider is None:
            try:
                from aGENtrader_v2.analytics.data_provider_finder import create_factory_from_environment
                data_provider = create_factory_from_environment()
                logger.info("Created data provider from environment variables")
            except Exception as e:
                logger.warning(f"Failed to create data provider from environment: {e}")
        
        self.data_provider = data_provider
        self.trade_log_path = trade_log_path
        self.summary_path = summary_path
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(trade_log_path), exist_ok=True)
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        
        # Load existing trade log if any
        self.trade_log = self._load_trade_log()
        
        # Initialize performance metrics
        self.metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "break_even_trades": 0,
            "open_trades": 0,
            "total_return_pct": 0.0,
            "winning_return_pct": 0.0,
            "losing_return_pct": 0.0,
            "largest_winner_pct": 0.0,
            "largest_loser_pct": 0.0,
            "avg_return_pct": 0.0,
            "profit_factor": 0.0,
            "win_rate": 0.0,
            "avg_hold_time_hours": 0.0,
            "max_drawdown_pct": 0.0,
            "current_drawdown_pct": 0.0,
            "peak_capital": 0.0,
            "current_capital": 0.0,
            "last_update": datetime.now().isoformat()
        }
        
        # Track agent performance - keyed by agent name
        self.agent_performance = {}
        
        # Update metrics if we loaded existing data
        if self.trade_log:
            self._recalculate_metrics()
    
    def _load_trade_log(self) -> List[Dict[str, Any]]:
        """
        Load the trade performance log from disk.
        
        Returns:
            List of trade performance dictionaries
        """
        trades = []
        
        if os.path.exists(self.trade_log_path):
            try:
                with open(self.trade_log_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            trade = json.loads(line)
                            trades.append(trade)
                
                logger.info(f"Loaded {len(trades)} trades from performance log")
            except Exception as e:
                logger.error(f"Error loading trade log: {e}")
        
        return trades
    
    def evaluate_trade(
        self, 
        trade: Dict[str, Any], 
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a trade's performance.
        
        For closed trades, calculates final PnL.
        For open trades, calculates unrealized PnL.
        
        Args:
            trade: Trade dictionary with trade details
            current_price: Current market price (if None, will try to fetch)
            
        Returns:
            Trade dictionary with performance metrics added
        """
        # Extract trade info
        symbol = trade.get("symbol")
        action = trade.get("action")
        entry_price = trade.get("entry_price")
        exit_price = trade.get("exit_price")
        is_closed = trade.get("is_closed", False)
        position_size = trade.get("position_size", 1.0)
        entry_time = trade.get("timestamp", datetime.now().isoformat())
        exit_time = trade.get("exit_time")
        trade_id = trade.get("id", str(hash(f"{symbol or ''}_{entry_time}")))
        
        # Validate required fields
        if not all([symbol, action, entry_price]):
            logger.error(f"Cannot evaluate trade - missing required fields: {trade}")
            return trade
        
        # Create a copy of the trade to avoid modifying the original
        evaluated_trade = trade.copy()
        
        # Assign trade ID if not present
        if "id" not in evaluated_trade:
            evaluated_trade["id"] = trade_id
        
        # For closed trades, calculate final performance
        if is_closed and exit_price is not None:
            return self._evaluate_closed_trade(evaluated_trade)
        
        # For open trades, get current price if not provided
        if current_price is None and self.data_provider:
            try:
                current_price = self._get_current_price(symbol)
            except Exception as e:
                logger.error(f"Error fetching current price for {symbol}: {e}")
                return evaluated_trade
        
        # If we still don't have a current price, we can't evaluate
        if current_price is None:
            logger.warning(f"Cannot evaluate open trade - no current price available for {symbol}")
            return evaluated_trade
        
        # Calculate unrealized PnL
        return self._evaluate_open_trade(evaluated_trade, current_price)
    
    def _evaluate_closed_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a closed trade.
        
        Args:
            trade: Trade dictionary with exit_price and exit_time
            
        Returns:
            Trade with performance metrics added
        """
        symbol = trade["symbol"]
        action = trade["action"]
        entry_price = trade["entry_price"]
        exit_price = trade["exit_price"]
        position_size = trade.get("position_size", 1.0)
        entry_time = parse_datetime(trade["timestamp"])
        exit_time = parse_datetime(trade["exit_time"])
        
        # Calculate return percentage
        if action == "BUY":
            return_pct = (exit_price - entry_price) / entry_price * 100
        else:  # SELL
            return_pct = (entry_price - exit_price) / entry_price * 100
        
        # Calculate hold time
        hold_time = exit_time - entry_time
        hold_time_hours = hold_time.total_seconds() / 3600
        
        # Determine win/loss status
        if return_pct > 0.5:  # Small threshold to account for trading fees
            status = "WIN"
        elif return_pct < -0.5:
            status = "LOSS"
        else:
            status = "BREAK-EVEN"
        
        # Calculate monetary return (normalized by position size)
        monetary_return = (return_pct / 100) * position_size * 10000  # Assuming $10K base capital
        
        # Add performance metrics to trade
        trade["return_pct"] = return_pct
        trade["hold_time_hours"] = hold_time_hours
        trade["status"] = status
        trade["monetary_return"] = monetary_return
        
        # Log the evaluated trade
        self._log_trade_performance(trade)
        
        # Update overall metrics
        self._update_metrics(trade)
        
        return trade
    
    def _evaluate_open_trade(
        self, 
        trade: Dict[str, Any], 
        current_price: float
    ) -> Dict[str, Any]:
        """
        Evaluate an open trade with current market price.
        
        Args:
            trade: Trade dictionary
            current_price: Current market price
            
        Returns:
            Trade with unrealized performance metrics added
        """
        symbol = trade["symbol"]
        action = trade["action"]
        entry_price = trade["entry_price"]
        position_size = trade.get("position_size", 1.0)
        entry_time = parse_datetime(trade["timestamp"])
        
        # Calculate unrealized return percentage
        if action == "BUY":
            unrealized_return_pct = (current_price - entry_price) / entry_price * 100
        else:  # SELL
            unrealized_return_pct = (entry_price - current_price) / entry_price * 100
        
        # Calculate current hold time
        current_time = datetime.now()
        hold_time = current_time - entry_time
        hold_time_hours = hold_time.total_seconds() / 3600
        
        # Determine current status
        if unrealized_return_pct > 0.5:
            current_status = "WINNING"
        elif unrealized_return_pct < -0.5:
            current_status = "LOSING"
        else:
            current_status = "BREAK-EVEN"
        
        # Calculate monetary return (normalized by position size)
        unrealized_monetary_return = (unrealized_return_pct / 100) * position_size * 10000
        
        # Add performance metrics to trade
        trade["unrealized_return_pct"] = unrealized_return_pct
        trade["current_price"] = current_price
        trade["hold_time_hours"] = hold_time_hours
        trade["current_status"] = current_status
        trade["unrealized_monetary_return"] = unrealized_monetary_return
        
        return trade
    
    def _log_trade_performance(self, trade: Dict[str, Any]) -> None:
        """
        Log trade performance to the trade log file.
        
        Args:
            trade: Trade dictionary with performance metrics
        """
        try:
            # Add to in-memory trade log
            existing_trade = next((t for t in self.trade_log if t.get("id") == trade.get("id")), None)
            
            if existing_trade:
                # Update existing trade
                idx = self.trade_log.index(existing_trade)
                self.trade_log[idx] = trade
            else:
                # Add new trade
                self.trade_log.append(trade)
            
            # Write to disk
            with open(self.trade_log_path, 'a') as f:
                f.write(json.dumps(trade) + '\n')
                
            logger.info(
                f"Logged performance for {trade['symbol']} {trade['action']}: "
                f"{trade.get('return_pct', 0):.2f}% ({trade.get('status', 'UNKNOWN')})"
            )
        except Exception as e:
            logger.error(f"Error logging trade performance: {e}")
    
    def update_trade_log(
        self, 
        trade_id: str, 
        exit_price: float, 
        exit_reason: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update a trade in the log with exit information.
        
        Args:
            trade_id: ID of the trade to update
            exit_price: Exit price
            exit_reason: Reason for the exit (e.g., "take_profit", "stop_loss")
            
        Returns:
            Updated trade dictionary or None if not found
        """
        # Find the trade in the log
        trade = next((t for t in self.trade_log if t.get("id") == trade_id), None)
        
        if not trade:
            logger.warning(f"Trade {trade_id} not found in trade log")
            return None
        
        # Update the trade
        trade["exit_price"] = exit_price
        trade["exit_reason"] = exit_reason
        trade["exit_time"] = datetime.now().isoformat()
        trade["is_closed"] = True
        
        # Evaluate the closed trade
        updated_trade = self._evaluate_closed_trade(trade)
        
        # Save the updated trade log
        self._save_trade_log()
        
        return updated_trade
    
    def _update_metrics(self, trade: Dict[str, Any]) -> None:
        """
        Update performance metrics with a new evaluated trade.
        
        Args:
            trade: Trade dictionary with performance metrics
        """
        status = trade.get("status")
        return_pct = trade.get("return_pct", 0)
        hold_time_hours = trade.get("hold_time_hours", 0)
        
        # Update general metrics
        self.metrics["total_trades"] += 1
        self.metrics["total_return_pct"] += return_pct
        
        # Update win/loss metrics
        if status == "WIN":
            self.metrics["winning_trades"] += 1
            self.metrics["winning_return_pct"] += return_pct
            self.metrics["largest_winner_pct"] = max(self.metrics["largest_winner_pct"], return_pct)
        elif status == "LOSS":
            self.metrics["losing_trades"] += 1
            self.metrics["losing_return_pct"] += return_pct
            self.metrics["largest_loser_pct"] = min(self.metrics["largest_loser_pct"], return_pct)
        else:  # BREAK-EVEN
            self.metrics["break_even_trades"] += 1
        
        # Calculate derived metrics
        if self.metrics["total_trades"] > 0:
            self.metrics["avg_return_pct"] = self.metrics["total_return_pct"] / self.metrics["total_trades"]
            self.metrics["win_rate"] = self.metrics["winning_trades"] / self.metrics["total_trades"]
        
        if self.metrics["losing_return_pct"] < 0:  # Avoid division by zero
            self.metrics["profit_factor"] = abs(self.metrics["winning_return_pct"] / self.metrics["losing_return_pct"]) if self.metrics["losing_return_pct"] != 0 else float('inf')
        
        # Update hold time metrics
        total_hold_hours = sum(t.get("hold_time_hours", 0) for t in self.trade_log if t.get("is_closed", False))
        closed_trades = sum(1 for t in self.trade_log if t.get("is_closed", False))
        self.metrics["avg_hold_time_hours"] = total_hold_hours / closed_trades if closed_trades > 0 else 0
        
        # Update drawdown metrics (simplified calculation)
        self._calculate_drawdown()
        
        # Update agent performance
        agent_name = trade.get("agent", "unknown")
        if agent_name not in self.agent_performance:
            self.agent_performance[agent_name] = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_return_pct": 0.0,
                "avg_return_pct": 0.0,
                "win_rate": 0.0
            }
        
        # Update agent metrics
        self.agent_performance[agent_name]["total_trades"] += 1
        self.agent_performance[agent_name]["total_return_pct"] += return_pct
        
        if status == "WIN":
            self.agent_performance[agent_name]["winning_trades"] += 1
        elif status == "LOSS":
            self.agent_performance[agent_name]["losing_trades"] += 1
        
        if self.agent_performance[agent_name]["total_trades"] > 0:
            self.agent_performance[agent_name]["avg_return_pct"] = (
                self.agent_performance[agent_name]["total_return_pct"] / 
                self.agent_performance[agent_name]["total_trades"]
            )
            self.agent_performance[agent_name]["win_rate"] = (
                self.agent_performance[agent_name]["winning_trades"] / 
                self.agent_performance[agent_name]["total_trades"]
            )
        
        # Update timestamp
        self.metrics["last_update"] = datetime.now().isoformat()
        
        # Save updated metrics
        self._save_summary()
    
    def _recalculate_metrics(self) -> None:
        """Recalculate all metrics from scratch using the trade log."""
        # Reset metrics
        self.metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "break_even_trades": 0,
            "open_trades": 0,
            "total_return_pct": 0.0,
            "winning_return_pct": 0.0,
            "losing_return_pct": 0.0,
            "largest_winner_pct": 0.0,
            "largest_loser_pct": 0.0,
            "avg_return_pct": 0.0,
            "profit_factor": 0.0,
            "win_rate": 0.0,
            "avg_hold_time_hours": 0.0,
            "max_drawdown_pct": 0.0,
            "current_drawdown_pct": 0.0,
            "peak_capital": 0.0,
            "current_capital": 0.0,
            "last_update": datetime.now().isoformat()
        }
        
        self.agent_performance = {}
        
        # Process each closed trade
        for trade in self.trade_log:
            if trade.get("is_closed", False):
                self._update_metrics(trade)
            else:
                self.metrics["open_trades"] += 1
        
        logger.info(f"Recalculated metrics from {len(self.trade_log)} trades")
    
    def _calculate_drawdown(self) -> None:
        """Calculate drawdown metrics from trade history."""
        # Sort trades by timestamp
        sorted_trades = sorted(
            [t for t in self.trade_log if t.get("is_closed", False)],
            key=lambda x: parse_datetime(x.get("timestamp", ""))
        )
        
        if not sorted_trades:
            return
        
        # Start with initial capital of 10000
        capital = 10000.0
        peak_capital = capital
        max_drawdown_pct = 0.0
        
        # Calculate equity curve and drawdown
        for trade in sorted_trades:
            monetary_return = trade.get("monetary_return", 0)
            capital += monetary_return
            
            # Update peak capital
            if capital > peak_capital:
                peak_capital = capital
            
            # Calculate current drawdown
            if peak_capital > 0:
                drawdown_pct = (peak_capital - capital) / peak_capital * 100
                max_drawdown_pct = max(max_drawdown_pct, drawdown_pct)
        
        # Calculate current drawdown
        current_drawdown_pct = (peak_capital - capital) / peak_capital * 100 if peak_capital > 0 else 0
        
        # Update metrics
        self.metrics["peak_capital"] = peak_capital
        self.metrics["current_capital"] = capital
        self.metrics["max_drawdown_pct"] = max_drawdown_pct
        self.metrics["current_drawdown_pct"] = current_drawdown_pct
    
    def _save_trade_log(self) -> None:
        """Save the entire trade log to disk."""
        try:
            with open(self.trade_log_path, 'w') as f:
                for trade in self.trade_log:
                    f.write(json.dumps(trade) + '\n')
            
            logger.info(f"Saved {len(self.trade_log)} trades to log")
        except Exception as e:
            logger.error(f"Error saving trade log: {e}")
    
    def _save_summary(self) -> None:
        """Save performance summary to disk."""
        try:
            summary = {
                "metrics": self.metrics,
                "agent_performance": self.agent_performance
            }
            
            with open(self.summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Saved performance summary to {self.summary_path}")
        except Exception as e:
            logger.error(f"Error saving performance summary: {e}")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance summary report.
        
        Returns:
            Dictionary with performance metrics
        """
        # Ensure metrics are up-to-date
        self._recalculate_metrics()
        
        # Generate extended summary
        summary = {
            "metrics": self.metrics,
            "agent_performance": self.agent_performance,
            "recent_trades": self._get_recent_trades(10),
            "best_trades": self._get_best_trades(5),
            "worst_trades": self._get_worst_trades(5),
            "confidence_analysis": self._analyze_by_confidence(),
            "hold_time_analysis": self._analyze_by_hold_time(),
            "symbol_performance": self._analyze_by_symbol()
        }
        
        # Save to disk
        try:
            with open(self.summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving summary report: {e}")
        
        return summary
    
    def _get_recent_trades(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get most recent trades."""
        return sorted(
            self.trade_log,
            key=lambda x: parse_datetime(x.get("timestamp", "")),
            reverse=True
        )[:count]
    
    def _get_best_trades(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get best performing trades."""
        return sorted(
            [t for t in self.trade_log if t.get("is_closed", False)],
            key=lambda x: x.get("return_pct", 0),
            reverse=True
        )[:count]
    
    def _get_worst_trades(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get worst performing trades."""
        return sorted(
            [t for t in self.trade_log if t.get("is_closed", False)],
            key=lambda x: x.get("return_pct", 0)
        )[:count]
    
    def _analyze_by_confidence(self) -> Dict[str, Any]:
        """Analyze performance by confidence level."""
        closed_trades = [t for t in self.trade_log if t.get("is_closed", False)]
        
        # Group by confidence ranges
        confidence_ranges = {
            "low": {"min": 0, "max": 60, "trades": [], "avg_return": 0.0, "win_rate": 0.0},
            "medium": {"min": 60, "max": 80, "trades": [], "avg_return": 0.0, "win_rate": 0.0},
            "high": {"min": 80, "max": 101, "trades": [], "avg_return": 0.0, "win_rate": 0.0}
        }
        
        # Assign trades to confidence ranges
        for trade in closed_trades:
            confidence = trade.get("confidence", 0)
            return_pct = trade.get("return_pct", 0)
            status = trade.get("status", "")
            
            for range_name, range_info in confidence_ranges.items():
                if range_info["min"] <= confidence < range_info["max"]:
                    range_info["trades"].append(trade)
                    break
        
        # Calculate metrics for each range
        for range_name, range_info in confidence_ranges.items():
            trades = range_info["trades"]
            if trades:
                # Calculate average return
                range_info["avg_return"] = sum(t.get("return_pct", 0) for t in trades) / len(trades)
                
                # Calculate win rate
                winning_trades = sum(1 for t in trades if t.get("status") == "WIN")
                range_info["win_rate"] = winning_trades / len(trades) if len(trades) > 0 else 0
                
                # Add trade count
                range_info["count"] = len(trades)
        
        return confidence_ranges
    
    def _analyze_by_hold_time(self) -> Dict[str, Any]:
        """Analyze performance by hold time."""
        closed_trades = [t for t in self.trade_log if t.get("is_closed", False)]
        
        # Group by hold time ranges
        hold_time_ranges = {
            "short": {"max_hours": 12, "trades": [], "avg_return": 0.0, "win_rate": 0.0},
            "medium": {"min_hours": 12, "max_hours": 48, "trades": [], "avg_return": 0.0, "win_rate": 0.0},
            "long": {"min_hours": 48, "trades": [], "avg_return": 0.0, "win_rate": 0.0}
        }
        
        # Assign trades to hold time ranges
        for trade in closed_trades:
            hold_time = trade.get("hold_time_hours", 0)
            
            if hold_time < hold_time_ranges["short"]["max_hours"]:
                hold_time_ranges["short"]["trades"].append(trade)
            elif hold_time < hold_time_ranges["medium"]["max_hours"]:
                hold_time_ranges["medium"]["trades"].append(trade)
            else:
                hold_time_ranges["long"]["trades"].append(trade)
        
        # Calculate metrics for each range
        for range_name, range_info in hold_time_ranges.items():
            trades = range_info["trades"]
            if trades:
                # Calculate average return
                range_info["avg_return"] = sum(t.get("return_pct", 0) for t in trades) / len(trades)
                
                # Calculate win rate
                winning_trades = sum(1 for t in trades if t.get("status") == "WIN")
                range_info["win_rate"] = winning_trades / len(trades) if len(trades) > 0 else 0
                
                # Add trade count
                range_info["count"] = len(trades)
        
        return hold_time_ranges
    
    def _analyze_by_symbol(self) -> Dict[str, Any]:
        """Analyze performance by symbol."""
        closed_trades = [t for t in self.trade_log if t.get("is_closed", False)]
        
        # Group by symbol
        symbol_performance = {}
        
        for trade in closed_trades:
            symbol = trade.get("symbol", "unknown")
            return_pct = trade.get("return_pct", 0)
            status = trade.get("status", "")
            
            if symbol not in symbol_performance:
                symbol_performance[symbol] = {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "total_return_pct": 0.0,
                    "avg_return_pct": 0.0,
                    "win_rate": 0.0
                }
            
            symbol_performance[symbol]["total_trades"] += 1
            symbol_performance[symbol]["total_return_pct"] += return_pct
            
            if status == "WIN":
                symbol_performance[symbol]["winning_trades"] += 1
        
        # Calculate derived metrics for each symbol
        for symbol, metrics in symbol_performance.items():
            if metrics["total_trades"] > 0:
                metrics["avg_return_pct"] = metrics["total_return_pct"] / metrics["total_trades"]
                metrics["win_rate"] = metrics["winning_trades"] / metrics["total_trades"]
        
        return symbol_performance
    
    def export_pnl_curve(self, output_path: str = "reports/pnl_curve.csv") -> None:
        """
        Export PnL curve data to CSV.
        
        Args:
            output_path: Path to save CSV file
        """
        # Sort trades by timestamp
        sorted_trades = sorted(
            [t for t in self.trade_log if t.get("is_closed", False)],
            key=lambda x: parse_datetime(x.get("timestamp", ""))
        )
        
        if not sorted_trades:
            logger.warning("No closed trades to generate PnL curve")
            return
        
        # Generate equity curve
        initial_capital = 10000.0
        equity_curve = []
        
        capital = initial_capital
        for trade in sorted_trades:
            # Get trade details
            timestamp = trade.get("timestamp", "")
            exit_time = trade.get("exit_time", "")
            symbol = trade.get("symbol", "")
            action = trade.get("action", "")
            return_pct = trade.get("return_pct", 0)
            monetary_return = trade.get("monetary_return", 0)
            
            # Update capital
            capital += monetary_return
            
            # Add to equity curve
            equity_curve.append({
                "timestamp": timestamp,
                "exit_time": exit_time,
                "symbol": symbol,
                "action": action,
                "return_pct": return_pct,
                "monetary_return": monetary_return,
                "cumulative_capital": capital
            })
        
        # Save to CSV
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                # Write header
                f.write("timestamp,exit_time,symbol,action,return_pct,monetary_return,cumulative_capital\n")
                
                # Write data rows
                for point in equity_curve:
                    f.write(f"{point['timestamp']},{point['exit_time']},{point['symbol']},{point['action']}," +
                            f"{point['return_pct']:.4f},{point['monetary_return']:.2f},{point['cumulative_capital']:.2f}\n")
            
            logger.info(f"Exported PnL curve to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting PnL curve: {e}")
    
    def _get_current_price(self, symbol: Optional[str]) -> Optional[float]:
        """
        Get the current price for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Current price or None if unavailable
        """
        if not self.data_provider:
            logger.warning("No data provider available to fetch current price")
            return None
            
        if symbol is None:
            logger.warning("Cannot fetch price for None symbol")
            return None
        
        try:
            # If the data provider has fetch_ticker method
            if hasattr(self.data_provider, 'fetch_ticker'):
                ticker = self.data_provider.fetch_ticker(symbol.replace("/", ""))
                return ticker.get("last")
                
            # If the data provider has a create_provider method (factory)
            elif hasattr(self.data_provider, 'create_provider'):
                provider = self.data_provider.create_provider()
                ticker = provider.fetch_ticker(symbol.replace("/", ""))
                return ticker.get("last")
            
            logger.warning("Data provider does not have required methods")
            return None
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None


def parse_datetime(dt_str: str) -> datetime:
    """
    Parse a datetime string to a datetime object.
    
    Args:
        dt_str: Datetime string
        
    Returns:
        Datetime object
    """
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return datetime.now()
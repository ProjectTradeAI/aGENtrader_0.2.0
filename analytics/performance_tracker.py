"""
aGENtrader v2 Performance Tracker

This module tracks live performance of trading decisions to monitor system health,
win/loss rates, agent contributions, and potential profitability.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Add parent directory to path to allow importing from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

class PerformanceTracker:
    """
    Performance Tracker for real-time monitoring of trading decisions.
    
    This class tracks:
    - Trading decisions and simulated outcomes
    - Win/loss rates and profitability metrics
    - Agent contributions to successful decisions
    - System evolution through version tagging
    """
    
    def __init__(self, log_dir="logs", datasets_dir="datasets"):
        """
        Initialize the Performance Tracker.
        
        Args:
            log_dir: Directory for performance logs
            datasets_dir: Directory for performance datasets
        """
        self.logger = logging.getLogger("PerformanceTracker")
        
        # Ensure directories exist
        self.log_dir = log_dir
        self.datasets_dir = datasets_dir
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(datasets_dir, exist_ok=True)
        
        # Performance log files
        self.performance_log = os.path.join(log_dir, "performance_summary.logl")
        self.performance_dataset = os.path.join(datasets_dir, "performance_dataset.jsonl")
        
        # Track active trades
        self.active_trades = {}
        self.completed_trades = []
        
        # System version
        self.version = os.getenv("SYSTEM_VERSION", "v0.2.0")
        
        self.logger.info(f"Performance Tracker initialized (version: {self.version})")
        
    def record_decision(self, decision_data: Dict[str, Any]) -> str:
        """
        Record a new trading decision.
        
        Args:
            decision_data: Decision details including symbol, action, price, etc.
            
        Returns:
            trade_id: Unique identifier for this trade decision
        """
        if not isinstance(decision_data, dict):
            self.logger.error("Decision data must be a dictionary")
            return ""
            
        # Generate a unique trade ID
        timestamp = datetime.now().isoformat()
        trade_id = f"{decision_data.get('symbol', 'UNKNOWN').replace('/', '')}-{timestamp}"
        
        # Add metadata
        trade_record = {
            "trade_id": trade_id,
            "timestamp": timestamp,
            "version": self.version,
            "symbol": decision_data.get("symbol", "UNKNOWN"),
            "interval": decision_data.get("interval", "unknown"),
            "action": decision_data.get("type", "HOLD"),
            "confidence": decision_data.get("confidence", 0),
            "entry_price": decision_data.get("price", 0),
            "reason": decision_data.get("reason", "No reason provided"),
            "status": "active" if decision_data.get("type") in ["BUY", "SELL"] else "completed",
            "agent_contributions": {}
        }
        
        # Add contributing agents and their confidence scores
        if "agent_analyses" in decision_data:
            for agent_type, analysis in decision_data["agent_analyses"].items():
                if isinstance(analysis, dict) and "confidence" in analysis:
                    trade_record["agent_contributions"][agent_type] = {
                        "confidence": analysis.get("confidence", 0),
                        "signal": analysis.get("signal", "NEUTRAL")
                    }
        
        # Skip performance tracking for HOLD decisions
        if trade_record["action"] == "HOLD":
            # Just log the HOLD decision without tracking it
            self._log_decision(trade_record)
            return trade_id
            
        # Add to active trades if BUY or SELL
        self.active_trades[trade_id] = trade_record
        
        # Log the decision
        self._log_decision(trade_record)
        
        self.logger.info(f"Recorded new trade decision: {trade_id} - {trade_record['action']} {trade_record['symbol']} @ {trade_record['entry_price']}")
        return trade_id
    
    def _log_decision(self, trade_record: Dict[str, Any]) -> None:
        """
        Log a trade decision to the performance log file.
        
        Args:
            trade_record: The trade decision data
        """
        try:
            # Format the log entry
            entry = (
                f"[{trade_record['timestamp']}] "
                f"DECISION: {trade_record['action']} {trade_record['symbol']} @ {trade_record['entry_price']} "
                f"(Confidence: {trade_record['confidence']}%) - {trade_record['reason']}"
            )
            
            # Write to performance log
            with open(self.performance_log, "a") as f:
                f.write(entry + "\n")
                
            # Append to dataset (JSONL format)
            with open(self.performance_dataset, "a") as f:
                f.write(json.dumps(trade_record) + "\n")
                
        except Exception as e:
            self.logger.error(f"Error logging trade decision: {str(e)}")
            
    def update_performance(self, market_data_provider, max_hold_time=None) -> None:
        """
        Update performance metrics for active trades.
        
        Args:
            market_data_provider: Provider to fetch current prices
            max_hold_time: Maximum holding time in minutes before auto-closing
        """
        now = datetime.now()
        trades_to_remove = []
        
        for trade_id, trade in self.active_trades.items():
            try:
                # Skip if trade is not active
                if trade["status"] != "active":
                    continue
                    
                # Get symbol and entry details
                symbol = trade["symbol"].replace("/", "")
                entry_time = datetime.fromisoformat(trade["timestamp"])
                entry_price = trade["entry_price"]
                action = trade["action"]
                
                # Calculate holding time
                hold_time_minutes = (now - entry_time).total_seconds() / 60
                
                # Check if we should auto-close based on hold time
                auto_close = False
                if max_hold_time and hold_time_minutes >= max_hold_time:
                    auto_close = True
                
                # Get current price from market data provider
                try:
                    current_price = market_data_provider.get_current_price(symbol)
                except Exception as e:
                    self.logger.warning(f"Couldn't get current price for {symbol}: {str(e)}")
                    continue
                
                # Calculate performance metrics
                if action == "BUY":
                    pnl_pct = (current_price - entry_price) / entry_price * 100
                    is_profitable = pnl_pct > 0
                elif action == "SELL":
                    pnl_pct = (entry_price - current_price) / entry_price * 100
                    is_profitable = pnl_pct > 0
                else:
                    pnl_pct = 0
                    is_profitable = False
                
                # Update the trade with current data
                trade["current_price"] = current_price
                trade["pnl_pct"] = pnl_pct
                trade["hold_time_minutes"] = hold_time_minutes
                trade["is_profitable"] = is_profitable
                
                # If auto-closing, mark as completed and log the outcome
                if auto_close:
                    trade["status"] = "completed"
                    trade["exit_price"] = current_price
                    trade["exit_time"] = now.isoformat()
                    trades_to_remove.append(trade_id)
                    
                    # Log the outcome
                    outcome = "PROFIT" if is_profitable else "LOSS"
                    entry = (
                        f"[{now.isoformat()}] "
                        f"OUTCOME: {outcome} on {trade['symbol']} - {pnl_pct:.2f}% "
                        f"(Entry: {entry_price}, Exit: {current_price}, Hold Time: {hold_time_minutes:.1f}min)"
                    )
                    
                    with open(self.performance_log, "a") as f:
                        f.write(entry + "\n")
                    
                    # Add to completed trades
                    self.completed_trades.append(trade)
                    
                    # Save to dataset with updated info
                    with open(self.performance_dataset, "a") as f:
                        f.write(json.dumps(trade) + "\n")
                
            except Exception as e:
                self.logger.error(f"Error updating performance for trade {trade_id}: {str(e)}")
        
        # Remove completed trades
        for trade_id in trades_to_remove:
            if trade_id in self.active_trades:
                del self.active_trades[trade_id]
    
    def manually_close_trade(self, trade_id: str, market_data_provider) -> Dict[str, Any]:
        """
        Manually close an active trade.
        
        Args:
            trade_id: The trade ID to close
            market_data_provider: Provider to fetch current price
            
        Returns:
            Dictionary with trade outcome
        """
        if trade_id not in self.active_trades:
            self.logger.warning(f"Trade {trade_id} not found or already closed")
            return {"error": "Trade not found"}
            
        trade = self.active_trades[trade_id]
        
        try:
            # Get symbol and entry details
            symbol = trade["symbol"].replace("/", "")
            entry_time = datetime.fromisoformat(trade["timestamp"])
            entry_price = trade["entry_price"]
            action = trade["action"]
            now = datetime.now()
            
            # Calculate holding time
            hold_time_minutes = (now - entry_time).total_seconds() / 60
            
            # Get current price
            current_price = market_data_provider.get_current_price(symbol)
            
            # Calculate performance metrics
            if action == "BUY":
                pnl_pct = (current_price - entry_price) / entry_price * 100
                is_profitable = pnl_pct > 0
            elif action == "SELL":
                pnl_pct = (entry_price - current_price) / entry_price * 100
                is_profitable = pnl_pct > 0
            else:
                pnl_pct = 0
                is_profitable = False
            
            # Update the trade
            trade["status"] = "completed"
            trade["exit_price"] = current_price
            trade["exit_time"] = now.isoformat()
            trade["pnl_pct"] = pnl_pct
            trade["hold_time_minutes"] = hold_time_minutes
            trade["is_profitable"] = is_profitable
            
            # Log the outcome
            outcome = "PROFIT" if is_profitable else "LOSS"
            entry = (
                f"[{now.isoformat()}] "
                f"OUTCOME: {outcome} on {trade['symbol']} - {pnl_pct:.2f}% "
                f"(Entry: {entry_price}, Exit: {current_price}, Hold Time: {hold_time_minutes:.1f}min)"
            )
            
            with open(self.performance_log, "a") as f:
                f.write(entry + "\n")
            
            # Add to completed trades and remove from active
            self.completed_trades.append(trade)
            del self.active_trades[trade_id]
            
            # Save to dataset with updated info
            with open(self.performance_dataset, "a") as f:
                f.write(json.dumps(trade) + "\n")
                
            self.logger.info(f"Closed trade {trade_id} with {outcome}: {pnl_pct:.2f}%")
            return trade
            
        except Exception as e:
            self.logger.error(f"Error closing trade {trade_id}: {str(e)}")
            return {"error": str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated system performance metrics.
        
        Returns:
            Dictionary with overall performance metrics
        """
        metrics = {
            "version": self.version,
            "active_trades": len(self.active_trades),
            "completed_trades": len(self.completed_trades),
            "profitable_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "avg_profit_pct": 0,
            "avg_loss_pct": 0,
            "total_pnl_pct": 0,
            "agent_performance": {}
        }
        
        # Skip if no completed trades
        if not self.completed_trades:
            return metrics
            
        # Calculate metrics
        profits = []
        losses = []
        agent_results = defaultdict(lambda: {"correct": 0, "incorrect": 0})
        
        for trade in self.completed_trades:
            if trade.get("is_profitable", False):
                metrics["profitable_trades"] += 1
                profits.append(trade.get("pnl_pct", 0))
            else:
                metrics["losing_trades"] += 1
                losses.append(trade.get("pnl_pct", 0))
                
            # Track agent contributions
            for agent, contribution in trade.get("agent_contributions", {}).items():
                agent_signal = contribution.get("signal", "NEUTRAL")
                trade_action = trade.get("action", "HOLD")
                
                # Determine if agent was correct
                if (agent_signal == "BUY" and trade_action == "BUY" and trade.get("is_profitable", False)) or \
                   (agent_signal == "SELL" and trade_action == "SELL" and trade.get("is_profitable", False)):
                    agent_results[agent]["correct"] += 1
                else:
                    agent_results[agent]["incorrect"] += 1
        
        # Calculate derived metrics
        total_completed = metrics["profitable_trades"] + metrics["losing_trades"]
        metrics["win_rate"] = (metrics["profitable_trades"] / total_completed * 100) if total_completed > 0 else 0
        metrics["avg_profit_pct"] = sum(profits) / len(profits) if profits else 0
        metrics["avg_loss_pct"] = sum(losses) / len(losses) if losses else 0
        metrics["total_pnl_pct"] = sum(profits) + sum(losses)
        
        # Calculate agent performance
        for agent, results in agent_results.items():
            total_signals = results["correct"] + results["incorrect"]
            accuracy = (results["correct"] / total_signals * 100) if total_signals > 0 else 0
            metrics["agent_performance"][agent] = {
                "accuracy": accuracy,
                "correct": results["correct"],
                "incorrect": results["incorrect"]
            }
            
        return metrics
    
    def log_system_metrics(self) -> None:
        """Log overall system performance metrics."""
        metrics = self.get_system_metrics()
        
        try:
            entry = (
                f"[{datetime.now().isoformat()}] "
                f"SYSTEM METRICS (v{metrics['version']}): "
                f"Win Rate: {metrics['win_rate']:.1f}%, "
                f"Trades: {metrics['completed_trades']}, "
                f"Avg Profit: {metrics['avg_profit_pct']:.2f}%, "
                f"Avg Loss: {metrics['avg_loss_pct']:.2f}%, "
                f"Total PnL: {metrics['total_pnl_pct']:.2f}%"
            )
            
            with open(self.performance_log, "a") as f:
                f.write(entry + "\n")
                
            self.logger.info(f"Logged system metrics: Win Rate: {metrics['win_rate']:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error logging system metrics: {str(e)}")
            
from collections import defaultdict

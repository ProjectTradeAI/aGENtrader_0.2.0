"""
Trade Performance Tracker Module

This module analyzes and tracks the performance of trades executed by the system.
It provides metrics and analytics on trading performance, including win/loss ratio,
average returns, and other key performance indicators.
"""

import os
import sys
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
import threading
import statistics
from collections import defaultdict, Counter
import math

# Add parent directory to path to allow importing from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import required modules
from utils.logger import get_logger
from utils.config import get_config
from data.feed import MarketDataFetcher

class TradePerformanceTracker:
    """
    Trade Performance Tracker for analyzing trading performance.
    
    This class:
    - Tracks trades and their outcomes
    - Calculates performance metrics
    - Generates performance reports
    - Identifies correlations between trade parameters and success
    """
    
    def __init__(self):
        """Initialize the Trade Performance Tracker."""
        self.logger = get_logger("performance_tracker")
        self.config = get_config()
        
        # Get performance tracker configuration
        tracker_config = self.config.get_section("performance_tracker")
        self.enabled = tracker_config.get("enabled", True)
        self.check_interval = tracker_config.get("check_interval_seconds", 60)
        self.stale_trade_minutes = tracker_config.get("stale_trade_minutes", 240)
        self.max_trade_hold_hours = tracker_config.get("max_trade_hold_hours", 48)
        
        # Setup directories
        self.trades_dir = os.path.join(parent_dir, "trades")
        self.reports_dir = os.path.join(parent_dir, tracker_config.get("report_dir", "reports"))
        os.makedirs(self.trades_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Define file paths
        self.trade_log_file = os.path.join(self.trades_dir, "trade_log.jsonl")
        self.active_trades_file = os.path.join(self.trades_dir, "active_trades.json")
        self.closed_trades_file = os.path.join(self.trades_dir, "closed_trades.jsonl")
        self.performance_report_file = os.path.join(self.reports_dir, "performance_report.json")
        
        # Initialize the market data fetcher for price updates
        self.market_fetcher = MarketDataFetcher()
        
        # Initialize tracking data
        self.processed_trade_ids = set()
        self.active_trades = {}
        self.closed_trades = []
        self.performance_metrics = {}
        
        # Initialize thread for background monitoring
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # Log initialization
        self.logger.info(f"Trade Performance Tracker initialized with check interval {self.check_interval}s")
        if self.enabled:
            self.logger.info("Performance tracking is enabled")
        else:
            self.logger.info("Performance tracking is disabled")
    
    def load_trades(self) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Load all trades from the trade log file and categorize them.
        
        Returns:
            Tuple containing:
            - Dictionary of active trades
            - List of closed trades
        """
        active_trades = {}
        closed_trades = []
        processed_ids = set()
        trade_close_events = {}
        trade_entries = {}
        
        # Read all trade events from the log file
        try:
            if os.path.exists(self.trade_log_file):
                self.logger.debug(f"Loading trades from: {self.trade_log_file}")
                
                # First, read all events and categorize them
                with open(self.trade_log_file, 'r') as f:
                    for line in f:
                        try:
                            trade_event = json.loads(line.strip())
                            
                            # Store close events to match with trades later
                            if trade_event.get("type") == "trade_close":
                                trade_id = trade_event.get("trade_id")
                                if trade_id:
                                    trade_close_events[trade_id] = trade_event
                                    self.logger.debug(f"Found close event for trade {trade_id}")
                            
                            # If this is a trade entry (not a close or update event)
                            elif "type" not in trade_event and "trade_id" in trade_event:
                                trade_id = trade_event["trade_id"]
                                processed_ids.add(trade_id)
                                # Store the trade entry for matching later
                                trade_entries[trade_id] = trade_event
                                self.logger.debug(f"Found trade entry: {trade_id}")
                        except json.JSONDecodeError:
                            self.logger.warning(f"Invalid JSON in trade log: {line}")
                            continue
                
                # Now match entries with close events
                for trade_id, trade in trade_entries.items():
                    if trade_id in trade_close_events:
                        # Merge the trade with its close info
                        close_event = trade_close_events[trade_id]
                        trade["status"] = "closed"
                        trade["exit_price"] = close_event.get("exit_price")
                        trade["exit_timestamp"] = close_event.get("timestamp")
                        trade["close_reason"] = close_event.get("reason")
                        trade["pnl_percentage"] = close_event.get("pnl_percentage")
                        trade["pnl_absolute"] = close_event.get("pnl_absolute")
                        
                        # Add to closed trades list
                        closed_trades.append(trade)
                        self.logger.debug(f"Matched trade {trade_id} with close event, status: closed")
                    else:
                        # This is an active trade
                        trade["status"] = "active"
                        active_trades[trade_id] = trade
                        self.logger.debug(f"No close event for {trade_id}, status: active")
                
                self.logger.info(f"Loaded {len(active_trades)} active trades and {len(closed_trades)} closed trades")
                self.processed_trade_ids = processed_ids
            else:
                self.logger.warning(f"Trade log file not found: {self.trade_log_file}")
        except Exception as e:
            self.logger.error(f"Error loading trades: {e}")
            # Print the full traceback for debugging
            import traceback
            self.logger.error(traceback.format_exc())
        
        return active_trades, closed_trades
    
    def get_current_price(self, pair: str) -> Optional[float]:
        """
        Get the current market price for a trading pair.
        
        Args:
            pair: Trading pair symbol
            
        Returns:
            Current market price or None if not available
        """
        try:
            # Try to get the current price from the market data fetcher
            # For now, use a simplified approach with default values
            # This will be enhanced later to use actual API calls
            
            # Use default prices for common pairs
            default_prices = {
                "BTC/USDT": 85000,
                "ETH/USDT": 3500,
                "BNB/USDT": 600,
                "SOL/USDT": 150,
                "ADA/USDT": 0.5,
                "XRP/USDT": 0.7
            }
            
            if pair in default_prices:
                # Apply a small random adjustment (±0.5%)
                adjustment = (random.random() - 0.5) * 0.01
                price = default_prices[pair] * (1 + adjustment)
                self.logger.debug(f"Using default price for {pair}: {price}")
                return price
            
            # For other pairs, check if we have a reference price in the trade logs
            return self._get_reference_price_from_logs(pair)
        except Exception as e:
            self.logger.warning(f"Error getting current price for {pair}: {e}")
            return None
            
    def _get_reference_price_from_logs(self, pair: str) -> Optional[float]:
        """
        Get a reference price from trade logs for a given pair.
        
        Args:
            pair: Trading pair
            
        Returns:
            Reference price or None if not found
        """
        try:
            # First check active trades
            if os.path.exists(self.active_trades_file):
                try:
                    with open(self.active_trades_file, 'r') as f:
                        active_trades = json.load(f)
                        for trade_id, trade in active_trades.items():
                            if isinstance(trade, dict) and trade.get("pair") == pair:
                                entry_price = trade.get("entry_price")
                                if entry_price is not None:
                                    # Apply a small random adjustment (±0.5%)
                                    adjustment = (random.random() - 0.5) * 0.01
                                    return float(entry_price) * (1 + adjustment)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
            
            # Then check trade log for recent trades with this pair
            if os.path.exists(self.trade_log_file):
                recent_lines = []
                try:
                    with open(self.trade_log_file, 'r') as f:
                        # Get up to the last 100 lines to search
                        lines = f.readlines()
                        recent_lines = lines[-100:] if len(lines) > 100 else lines
                        
                    # Start from the most recent
                    for line in reversed(recent_lines):
                        try:
                            trade_data = json.loads(line.strip())
                            if trade_data.get("pair") == pair:
                                # Check for exit price first (more recent)
                                if "exit_price" in trade_data and trade_data["exit_price"] is not None:
                                    adjustment = (random.random() - 0.5) * 0.01
                                    return float(trade_data["exit_price"]) * (1 + adjustment)
                                # Then check entry price
                                elif "entry_price" in trade_data and trade_data["entry_price"] is not None:
                                    adjustment = (random.random() - 0.5) * 0.01
                                    return float(trade_data["entry_price"]) * (1 + adjustment)
                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue
                except Exception:
                    pass
            
            # If nothing found, return None
            return None
        except Exception as e:
            self.logger.warning(f"Error retrieving reference price from logs: {e}")
            return None
    
    def check_trade_status(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a trade should be closed based on current market conditions.
        
        Args:
            trade: Trade data dictionary
            
        Returns:
            Updated trade dictionary with status information
        """
        # Make sure we have a valid trade to check
        if not isinstance(trade, dict):
            self.logger.warning(f"Invalid trade data: {trade}")
            return {}
        
        # Skip trades that are already closed
        if trade.get("status") == "closed":
            return trade
        
        # Get required trade data, validating each field
        trade_id = trade.get("trade_id", "unknown")
        pair = trade.get("pair")
        if not pair:
            self.logger.warning(f"Trade {trade_id} has no pair specified, cannot check status")
            return trade
            
        action = trade.get("action")
        if not action or action not in ["BUY", "SELL"]:
            self.logger.warning(f"Trade {trade_id} has invalid action: {action}")
            return trade
            
        entry_price = trade.get("entry_price")
        if entry_price is None:
            self.logger.warning(f"Trade {trade_id} has no entry price, cannot check status")
            return trade
        
        try:
            # Convert entry_price to float if it's not already
            entry_price = float(entry_price)
        except (ValueError, TypeError):
            self.logger.warning(f"Trade {trade_id} has invalid entry price: {entry_price}")
            return trade
            
        stop_loss = trade.get("stop_loss")
        take_profit = trade.get("take_profit")
        
        # Convert these to floats if they exist
        try:
            if stop_loss is not None:
                stop_loss = float(stop_loss)
            if take_profit is not None:
                take_profit = float(take_profit)
        except (ValueError, TypeError):
            self.logger.warning(f"Trade {trade_id} has invalid stop_loss or take_profit values")
            return trade
            
        entry_timestamp = trade.get("timestamp")
        
        # Get current price
        current_price = self.get_current_price(pair)
        
        # If we can't get the current price, we can't check status
        if not current_price:
            self.logger.warning(f"Unable to check status for trade {trade_id}: No current price available")
            return trade
            
        # Calculate how long the trade has been open
        current_time = datetime.now()
        trade_duration_hours = 0
        
        if entry_timestamp:
            try:
                entry_time = datetime.fromisoformat(entry_timestamp)
                trade_duration = current_time - entry_time
                trade_duration_hours = trade_duration.total_seconds() / 3600
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid timestamp for trade {trade_id}: {entry_timestamp}")
        
        # Check if trade should be closed
        should_close = False
        close_reason = None
        
        # Check take profit (only if take_profit value is defined)
        if take_profit is not None:
            if action == "BUY" and current_price >= take_profit:
                should_close = True
                close_reason = "take_profit"
            elif action == "SELL" and current_price <= take_profit:
                should_close = True
                close_reason = "take_profit"
            
        # Check stop loss (only if stop_loss value is defined)
        if not should_close and stop_loss is not None:
            if action == "BUY" and current_price <= stop_loss:
                should_close = True
                close_reason = "stop_loss"
            elif action == "SELL" and current_price >= stop_loss:
                should_close = True
                close_reason = "stop_loss"
            
        # Check if trade has been open too long
        if not should_close and trade_duration_hours >= self.max_trade_hold_hours:
            should_close = True
            close_reason = "timeout"
            
        # If trade should be closed, update trade data
        if should_close:
            # Calculate P&L
            if action == "BUY":
                pnl_percentage = (current_price - entry_price) / entry_price * 100
                position_size = float(trade.get("position_size", 0))
                pnl_absolute = position_size * (current_price - entry_price)
            else:  # SELL
                pnl_percentage = (entry_price - current_price) / entry_price * 100
                position_size = float(trade.get("position_size", 0))
                pnl_absolute = position_size * (entry_price - current_price)
                
            # Update trade
            trade["status"] = "closed"
            trade["exit_price"] = current_price
            trade["exit_timestamp"] = current_time.isoformat()
            trade["close_reason"] = close_reason
            trade["pnl_percentage"] = pnl_percentage
            trade["pnl_absolute"] = pnl_absolute
            trade["trade_duration_hours"] = trade_duration_hours
            
            # Log close
            self.logger.info(f"Trade {trade_id} closed with {pnl_percentage:.2f}% P&L ({close_reason})")
            
            # Record close event
            close_event = {
                "type": "trade_close",
                "trade_id": trade_id,
                "timestamp": current_time.isoformat(),
                "exit_price": current_price,
                "reason": close_reason,
                "pnl_percentage": pnl_percentage,
                "pnl_absolute": pnl_absolute
            }
            
            # Write close event to log
            try:
                with open(self.trade_log_file, 'a') as f:
                    f.write(json.dumps(close_event) + "\n")
            except Exception as e:
                self.logger.error(f"Error writing close event to log: {e}")
                
            # Write to closed trades log
            try:
                with open(self.closed_trades_file, 'a') as f:
                    f.write(json.dumps(trade) + "\n")
            except Exception as e:
                self.logger.error(f"Error writing to closed trades log: {e}")
        
        return trade
        
    def update_active_trades_file(self, active_trades: Dict[str, Dict[str, Any]]) -> None:
        """
        Update the active trades file with current active trades.
        
        Args:
            active_trades: Dictionary of active trades
        """
        try:
            with open(self.active_trades_file, 'w') as f:
                json.dump(active_trades, f, indent=2)
            self.logger.debug(f"Updated active trades file with {len(active_trades)} trades")
        except Exception as e:
            self.logger.error(f"Error updating active trades file: {e}")
            
    def process_trades(self) -> None:
        """Process all trades to update their status and calculate metrics."""
        # Load all trades
        active_trades, closed_trades = self.load_trades()
        self.active_trades = active_trades
        self.closed_trades = closed_trades
        
        # Check status of active trades
        updated_active_trades = {}
        newly_closed_trades = []
        
        for trade_id, trade in active_trades.items():
            updated_trade = self.check_trade_status(trade)
            
            # If trade is still active, keep it in active trades
            if updated_trade.get("status") != "closed":
                updated_active_trades[trade_id] = updated_trade
            else:
                # If trade was closed, add to closed trades
                newly_closed_trades.append(updated_trade)
        
        # Update active trades
        if len(active_trades) != len(updated_active_trades):
            self.logger.info(f"Closed {len(active_trades) - len(updated_active_trades)} trades")
            self.update_active_trades_file(updated_active_trades)
        
        # Update closed trades list
        self.closed_trades.extend(newly_closed_trades)
        
        # Calculate performance metrics
        self.calculate_performance_metrics()
        
    def calculate_performance_metrics(self) -> None:
        """Calculate all performance metrics and generate a report."""
        # Skip if there are no closed trades
        if not self.closed_trades:
            self.logger.info("No closed trades to analyze")
            return
            
        # Basic metrics
        total_trades = len(self.closed_trades)
        winning_trades = sum(1 for t in self.closed_trades if t.get("pnl_percentage", 0) > 0)
        losing_trades = sum(1 for t in self.closed_trades if t.get("pnl_percentage", 0) <= 0)
        
        # Avoid division by zero
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        loss_rate = (losing_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # Calculate returns
        total_return = sum(t.get("pnl_percentage", 0) for t in self.closed_trades)
        average_return = total_return / total_trades if total_trades > 0 else 0
        
        # Calculate other metrics
        returns = [t.get("pnl_percentage", 0) for t in self.closed_trades]
        winning_returns = [r for r in returns if r > 0]
        losing_returns = [r for r in returns if r <= 0]
        
        # Handle empty lists
        avg_win = sum(winning_returns) / len(winning_returns) if winning_returns else 0
        avg_loss = sum(losing_returns) / len(losing_returns) if losing_returns else 0
        
        # Avoid division by zero
        profit_factor = abs(sum(winning_returns) / sum(losing_returns)) if sum(losing_returns) != 0 else float('inf')
        
        # Calculate max drawdown
        pnl_curve = []
        running_pnl = 0
        peak = 0
        drawdowns = []
        
        for t in sorted(self.closed_trades, key=lambda x: x.get("timestamp", "")):
            running_pnl += t.get("pnl_percentage", 0)
            pnl_curve.append(running_pnl)
            
            if running_pnl > peak:
                peak = running_pnl
            elif peak - running_pnl > 0:
                drawdowns.append(peak - running_pnl)
        
        max_drawdown = max(drawdowns) if drawdowns else 0
        
        # Calculate hold times
        hold_times = []
        for trade in self.closed_trades:
            try:
                start_time = datetime.fromisoformat(trade.get("timestamp", ""))
                end_time = datetime.fromisoformat(trade.get("exit_timestamp", ""))
                duration = end_time - start_time
                hold_times.append(duration.total_seconds() / 3600)  # Convert to hours
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid timestamps for trade {trade.get('trade_id')}")
        
        avg_hold_time = sum(hold_times) / len(hold_times) if hold_times else 0
        
        # Performance by trading pair
        pairs_performance = {}
        for trade in self.closed_trades:
            pair = trade.get("pair", "UNKNOWN")
            if pair not in pairs_performance:
                pairs_performance[pair] = {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "total_return": 0,
                    "avg_return": 0
                }
                
            pairs_performance[pair]["total_trades"] += 1
            if trade.get("pnl_percentage", 0) > 0:
                pairs_performance[pair]["winning_trades"] += 1
            pairs_performance[pair]["total_return"] += trade.get("pnl_percentage", 0)
        
        # Calculate averages for each pair
        for pair in pairs_performance:
            pair_trades = pairs_performance[pair]["total_trades"]
            if pair_trades > 0:
                pairs_performance[pair]["avg_return"] = pairs_performance[pair]["total_return"] / pair_trades
                pairs_performance[pair]["win_rate"] = (pairs_performance[pair]["winning_trades"] / pair_trades) * 100
        
        # Sort pairs by total return
        top_pairs = sorted(
            pairs_performance.items(), 
            key=lambda x: x[1]["total_return"], 
            reverse=True
        )
        
        # Prepare top pairs data
        top_pairs_data = {
            pair: metrics for pair, metrics in top_pairs[:5]
        }
        
        # Analyze by confidence level
        confidence_performance = {}
        for trade in self.closed_trades:
            confidence = trade.get("confidence", 0)
            # Group by confidence ranges (60-70, 70-80, etc.)
            confidence_range = f"{int(confidence // 10) * 10}-{int(confidence // 10) * 10 + 10}"
            
            if confidence_range not in confidence_performance:
                confidence_performance[confidence_range] = {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "total_return": 0,
                    "avg_return": 0
                }
                
            confidence_performance[confidence_range]["total_trades"] += 1
            if trade.get("pnl_percentage", 0) > 0:
                confidence_performance[confidence_range]["winning_trades"] += 1
            confidence_performance[confidence_range]["total_return"] += trade.get("pnl_percentage", 0)
        
        # Calculate averages for each confidence range
        for conf_range in confidence_performance:
            conf_trades = confidence_performance[conf_range]["total_trades"]
            if conf_trades > 0:
                confidence_performance[conf_range]["avg_return"] = confidence_performance[conf_range]["total_return"] / conf_trades
                confidence_performance[conf_range]["win_rate"] = (confidence_performance[conf_range]["winning_trades"] / conf_trades) * 100
        
        # Collect all metrics
        # Calculate agent contribution metrics
        agent_contributions = self.calculate_agent_contribution_metrics()
        
        performance_metrics = {
            "timestamp": datetime.now().isoformat(),
            "period": {
                "start": min(t.get("timestamp", "") for t in self.closed_trades),
                "end": max(t.get("exit_timestamp", "") for t in self.closed_trades)
            },
            "overall": {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "loss_rate": loss_rate,
                "total_return": total_return,
                "average_return": average_return,
                "average_win": avg_win,
                "average_loss": avg_loss,
                "profit_factor": profit_factor,
                "max_drawdown": max_drawdown,
                "average_hold_time_hours": avg_hold_time
            },
            "by_pair": top_pairs_data,
            "by_confidence": confidence_performance,
            "exit_reasons": {
                "take_profit": sum(1 for t in self.closed_trades if t.get("close_reason") == "take_profit"),
                "stop_loss": sum(1 for t in self.closed_trades if t.get("close_reason") == "stop_loss"),
                "timeout": sum(1 for t in self.closed_trades if t.get("close_reason") == "timeout"),
                "manual": sum(1 for t in self.closed_trades if t.get("close_reason") not in ["take_profit", "stop_loss", "timeout"])
            },
            "agent_contributions": agent_contributions
        }
        
        # Save the performance metrics
        self.performance_metrics = performance_metrics
        
        # Write to performance report file
        try:
            with open(self.performance_report_file, 'w') as f:
                json.dump(performance_metrics, f, indent=2)
            self.logger.info(f"Performance report saved to {self.performance_report_file}")
        except Exception as e:
            self.logger.error(f"Error writing performance report: {e}")
        
        # Log summary
        self.logger.info(f"Performance analysis completed: {total_trades} trades, {win_rate:.1f}% win rate, {average_return:.2f}% avg return")
        
    def monitor_trades_thread(self) -> None:
        """Background thread for monitoring trades."""
        self.logger.info("Starting trade monitoring thread")
        
        while self.monitoring_active:
            try:
                # Process trades
                self.process_trades()
                
                # Wait for next check
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in trade monitoring thread: {e}")
                time.sleep(self.check_interval)  # Still sleep to avoid tight loop on error
        
        self.logger.info("Trade monitoring thread stopped")
        
    def start_monitoring(self) -> None:
        """Start the trade monitoring thread."""
        if not self.enabled:
            self.logger.info("Trade performance tracking is disabled, not starting monitoring")
            return
            
        if self.monitoring_thread is not None and self.monitoring_thread.is_alive():
            self.logger.warning("Monitoring thread already running")
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self.monitor_trades_thread)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        self.logger.info("Trade monitoring started")
        
    def stop_monitoring(self) -> None:
        """Stop the trade monitoring thread."""
        if not self.monitoring_active:
            return
            
        self.monitoring_active = False
        if self.monitoring_thread is not None:
            self.monitoring_thread.join(timeout=10.0)
            
        self.logger.info("Trade monitoring stopped")
        
    def calculate_agent_contribution_metrics(self) -> Dict[str, Any]:
        """
        Calculate metrics related to agent contributions to trading decisions.
        
        This analyzes how each agent's weighted confidence scores correlate with trade success.
        
        Returns:
            Dictionary with agent contribution metrics
        """
        # Initialize metrics structure
        agent_metrics = {}
        
        # Collect all agent names from trade data
        all_agent_names = set()
        for trade in self.closed_trades:
            contributions = trade.get("decision", {}).get("agent_contributions", {})
            all_agent_names.update(contributions.keys())
        
        # Skip if no agent contribution data found
        if not all_agent_names:
            self.logger.warning("No agent contribution data found in trade records")
            return {}
            
        # Calculate metrics for each agent
        for agent_name in all_agent_names:
            # Initialize agent statistics
            agent_stats = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "action_alignment": 0,  # How often agent's recommendation matched final decision
                "average_confidence": 0,
                "average_weight": 0,
                "average_weighted_confidence": 0,
                "average_return_when_followed": 0,
                "average_return_when_not_followed": 0,
                "trades_by_action": {"BUY": 0, "SELL": 0, "HOLD": 0}
            }
            
            # Collect data for this agent
            confidence_sum = 0
            weight_sum = 0
            weighted_confidence_sum = 0
            alignment_count = 0
            followed_return_sum = 0
            followed_count = 0
            not_followed_return_sum = 0
            not_followed_count = 0
            
            for trade in self.closed_trades:
                # Skip trades without agent contribution data
                decision = trade.get("decision", {})
                contributions = decision.get("agent_contributions", {})
                if agent_name not in contributions:
                    continue
                
                # Get agent's data for this trade
                agent_data = contributions[agent_name]
                final_action = decision.get("action", "UNKNOWN")
                agent_action = agent_data.get("action", "UNKNOWN")
                agent_confidence = agent_data.get("confidence", 0)
                agent_weight = agent_data.get("weight", 1.0)
                agent_weighted_confidence = agent_data.get("weighted_confidence", 0)
                trade_return = trade.get("pnl_percentage", 0)
                
                # Update basic stats
                agent_stats["total_trades"] += 1
                if trade_return > 0:
                    agent_stats["winning_trades"] += 1
                else:
                    agent_stats["losing_trades"] += 1
                
                # Count actions
                if agent_action in agent_stats["trades_by_action"]:
                    agent_stats["trades_by_action"][agent_action] += 1
                
                # Check alignment with final decision
                if agent_action == final_action:
                    alignment_count += 1
                    followed_return_sum += trade_return
                    followed_count += 1
                else:
                    not_followed_return_sum += trade_return
                    not_followed_count += 1
                
                # Update sums for averages
                confidence_sum += agent_confidence
                weight_sum += agent_weight
                weighted_confidence_sum += agent_weighted_confidence
            
            # Calculate averages and rates
            if agent_stats["total_trades"] > 0:
                agent_stats["win_rate"] = (agent_stats["winning_trades"] / agent_stats["total_trades"]) * 100
                agent_stats["action_alignment"] = (alignment_count / agent_stats["total_trades"]) * 100
                agent_stats["average_confidence"] = confidence_sum / agent_stats["total_trades"]
                agent_stats["average_weight"] = weight_sum / agent_stats["total_trades"]
                agent_stats["average_weighted_confidence"] = weighted_confidence_sum / agent_stats["total_trades"]
                
                if followed_count > 0:
                    agent_stats["average_return_when_followed"] = followed_return_sum / followed_count
                
                if not_followed_count > 0:
                    agent_stats["average_return_when_not_followed"] = not_followed_return_sum / not_followed_count
                
                # Calculate influence score (how much following this agent's advice improves returns)
                if followed_count > 0 and not_followed_count > 0:
                    agent_stats["influence_score"] = agent_stats["average_return_when_followed"] - agent_stats["average_return_when_not_followed"]
                else:
                    agent_stats["influence_score"] = 0
            
            # Store this agent's metrics
            agent_metrics[agent_name] = agent_stats
        
        # Calculate overall agent contribution summary
        summary = {
            "most_influential_agent": max(agent_metrics.items(), key=lambda x: x[1].get("influence_score", 0))[0] if agent_metrics else "None",
            "most_aligned_agent": max(agent_metrics.items(), key=lambda x: x[1].get("action_alignment", 0))[0] if agent_metrics else "None",
            "highest_win_rate_agent": max(agent_metrics.items(), key=lambda x: x[1].get("win_rate", 0))[0] if agent_metrics else "None"
        }
        
        # Return complete agent contribution metrics
        return {
            "agent_metrics": agent_metrics,
            "summary": summary
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get the latest performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        # If metrics are not calculated yet, try calculating them
        if not self.performance_metrics:
            self.process_trades()
            
        return self.performance_metrics
        
    def get_performance_summary(self) -> str:
        """
        Get a human-readable summary of performance metrics.
        
        Returns:
            String with performance summary
        """
        if not self.performance_metrics:
            return "No performance metrics available yet"
            
        metrics = self.performance_metrics
        overall = metrics.get("overall", {})
        
        # Format the summary
        summary = [
            "=== TRADING PERFORMANCE SUMMARY ===",
            f"Period: {metrics.get('period', {}).get('start', 'Unknown')} to {metrics.get('period', {}).get('end', 'Unknown')}",
            f"Total Trades: {overall.get('total_trades', 0)}",
            f"Win Rate: {overall.get('win_rate', 0):.1f}%",
            f"Total Return: {overall.get('total_return', 0):.2f}%",
            f"Average Return: {overall.get('average_return', 0):.2f}%",
            f"Profit Factor: {overall.get('profit_factor', 0):.2f}",
            f"Max Drawdown: {overall.get('max_drawdown', 0):.2f}%",
            f"Average Hold Time: {overall.get('average_hold_time_hours', 0):.1f} hours",
            ""
        ]
        
        # Add exit reasons
        exit_reasons = metrics.get("exit_reasons", {})
        summary.append("Exit Reasons:")
        for reason, count in exit_reasons.items():
            summary.append(f"  - {reason.replace('_', ' ').title()}: {count}")
        
        # Add top performing pairs
        top_pairs = metrics.get("by_pair", {})
        if top_pairs:
            summary.append("\nTop Performing Pairs:")
            for pair, pair_metrics in top_pairs.items():
                summary.append(f"  - {pair}: {pair_metrics.get('total_return', 0):.2f}% ({pair_metrics.get('total_trades', 0)} trades)")
        
        # Add agent contribution summary
        agent_contributions = metrics.get("agent_contributions", {})
        if agent_contributions and agent_contributions.get("summary"):
            agent_summary = agent_contributions.get("summary", {})
            summary.append("\nAgent Contribution:")
            if "most_influential_agent" in agent_summary:
                summary.append(f"  Most Influential: {agent_summary['most_influential_agent']}")
            if "highest_win_rate_agent" in agent_summary:
                summary.append(f"  Highest Win Rate: {agent_summary['highest_win_rate_agent']}")
            if "most_aligned_agent" in agent_summary:
                summary.append(f"  Most Aligned: {agent_summary['most_aligned_agent']}")
            
            # Add detailed metrics for top agents
            agent_metrics = agent_contributions.get("agent_metrics", {})
            if agent_metrics:
                # Find the agent with the highest influence score
                top_agent = agent_summary.get("most_influential_agent")
                if top_agent in agent_metrics:
                    agent_data = agent_metrics[top_agent]
                    summary.append(f"\nTop Agent ({top_agent}) Metrics:")
                    summary.append(f"  Win Rate: {agent_data.get('win_rate', 0):.1f}%")
                    summary.append(f"  Decision Alignment: {agent_data.get('action_alignment', 0):.1f}%")
                    summary.append(f"  Avg Weight: {agent_data.get('average_weight', 0):.2f}")
                    summary.append(f"  Avg Return When Followed: {agent_data.get('average_return_when_followed', 0):.2f}%")
        
        return "\n".join(summary)

# Example usage
if __name__ == "__main__":
    tracker = TradePerformanceTracker()
    
    # Process trades once
    tracker.process_trades()
    
    # Print summary
    print(tracker.get_performance_summary())
    
    # Start monitoring in the background
    # tracker.start_monitoring()
    
    # To stop monitoring:
    # tracker.stop_monitoring()
"""
Live Trading Mode Script

This script implements live trading mode for the aGENtrader v2 system.
It uses the MarketDataFetcher to fetch real-time market data and feeds it
into the agent pipeline to generate trading decisions.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import core components
from aGENtrader_v2.data.feed import MarketDataFetcher
from aGENtrader_v2.utils.logger import get_logger
from aGENtrader_v2.utils.config import get_config
from aGENtrader_v2.orchestrator.core_orchestrator import CoreOrchestrator
from aGENtrader_v2.agents.trade_executor_agent import TradeExecutorAgent
from aGENtrader_v2.performance.trade_performance_tracker import TradePerformanceTracker

# Global variables
logger = get_logger("live_trading")
config = get_config()

class LiveTradingManager:
    """
    Manager class for live trading operations.
    
    This class orchestrates:
    - Market data fetching at regular intervals
    - Feeding data to the agent pipeline
    - Logging and persisting trading decisions
    - (Optional) Executing trades via exchange APIs
    """
    
    def __init__(self, symbol: Optional[str] = None, interval: Optional[str] = None):
        """Initialize the live trading manager."""
        self.logger = get_logger("live_trading_manager")
        
        # Load market configuration
        market_config = config.get_section("market_data")
        self.symbol = symbol or market_config.get("default_pair", "BTC/USDT")
        self.interval = interval or market_config.get("default_interval", "1h")
        self.poll_interval = market_config.get("poll_interval_seconds", 300)
        self.save_data = market_config.get("save_fetched_data", True)
        
        # Load trade execution configuration
        trade_config = config.get_section("trade_execution")
        self.execution_mode = trade_config.get("execution_mode", "disabled")
        self.confidence_threshold = trade_config.get("confidence_threshold", 75)
        
        # Load performance tracker configuration
        performance_config = config.get_section("performance_tracker")
        self.performance_tracking_enabled = performance_config.get("enabled", True)
        
        self.logger.info(f"Initializing live trading for {self.symbol} at {self.interval} interval")
        self.logger.info(f"Trade execution mode: {self.execution_mode}")
        self.logger.info(f"Performance tracking enabled: {self.performance_tracking_enabled}")
        
        # Initialize components
        self.market_fetcher = MarketDataFetcher()
        self.orchestrator = CoreOrchestrator()
        self.trade_executor = TradeExecutorAgent()
        self.performance_tracker = TradePerformanceTracker()
        
        # Set up directories
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "live")
        self.logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        self.reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Output files
        self.decisions_file = os.path.join(self.logs_dir, "decisions_live.jsonl")
        self.market_data_file = os.path.join(self.data_dir, f"{self.symbol.replace('/', '_')}_{self.interval}_live.jsonl")
        
    def save_market_event(self, event: Dict[str, Any]) -> None:
        """
        Save a market event to a JSONL file.
        
        Args:
            event: Market event data dictionary
        """
        if not self.save_data:
            return
            
        try:
            with open(self.market_data_file, "a") as f:
                f.write(json.dumps(event) + "\n")
                
            self.logger.debug(f"Saved market event to {self.market_data_file}")
        except Exception as e:
            self.logger.error(f"Error saving market event: {e}")
            
    def save_trading_decision(self, decision: Dict[str, Any]) -> None:
        """
        Save a trading decision to a JSONL file.
        
        Args:
            decision: Trading decision data dictionary
        """
        try:
            with open(self.decisions_file, "a") as f:
                f.write(json.dumps(decision) + "\n")
                
            self.logger.info(f"Saved trading decision to {self.decisions_file}")
        except Exception as e:
            self.logger.error(f"Error saving trading decision: {e}")
            
    def process_market_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a market event through the agent pipeline.
        
        Args:
            event: Market event data dictionary
            
        Returns:
            Dictionary containing the trading decision
        """
        self.logger.info(f"Processing market event for {event.get('symbol')} at {event.get('timestamp')}")
        
        # Save the event
        self.save_market_event(event)
        
        # Process through orchestrator
        try:
            # Generate a trading decision
            results = self.orchestrator.process_market_event(event)
            
            # Extract the decision from the results
            if results and "decision" in results and results["decision"]:
                decision = results["decision"]
            else:
                # Create fallback decision if none was returned
                decision = {
                    "action": "HOLD",
                    "pair": event.get("symbol", "UNKNOWN"),
                    "confidence": 50,
                    "reason": "Waiting for clearer signals"
                }
            
            # Add metadata
            decision["timestamp"] = datetime.now().isoformat()
            decision["source"] = "live_trading"
            decision["market_timestamp"] = event.get("timestamp")
            
            # Log the decision
            self.logger.info(f"Trading decision: {decision.get('action')} with confidence {decision.get('confidence')}%")
            
            # Save the decision
            self.save_trading_decision(decision)
            
            # Execute trade if appropriate and not HOLD
            if self.execution_mode != "disabled" and decision.get("action") != "HOLD":
                try:
                    # Use the full execution pipeline through the orchestrator
                    # rather than directly calling the trade executor
                    self.logger.info(f"Running complete execution pipeline for {decision.get('action')} decision")
                    
                    # Make a copy of the decision for safety
                    decision_dict = dict(decision)
                    
                    # Execute the full pipeline
                    pipeline_result = self.orchestrator._execute_trade_pipeline(decision_dict, event)
                    
                    # Add the pipeline result to the decision for tracking
                    decision["execution_pipeline"] = pipeline_result
                    
                    # Set status based on pipeline result
                    pipeline_status = pipeline_result.get("status", "unknown")
                    
                    if pipeline_status == "success":
                        self.logger.info(f"Trade executed: {pipeline_result.get('trade_id')}")
                        decision["trade_id"] = pipeline_result.get("trade_id")
                        decision["trade_status"] = "executed"
                    elif pipeline_status in ["rejected_by_portfolio_manager", "rejected_by_risk_guard"]:
                        self.logger.info(f"Trade rejected: {pipeline_result.get('reason')}")
                        decision["trade_status"] = "rejected"
                        decision["rejection_reason"] = pipeline_result.get("reason")
                    elif pipeline_status == "skipped":
                        self.logger.info(f"Trade not executed: {pipeline_result.get('reason')}")
                        decision["trade_status"] = "skipped"
                    else:
                        self.logger.warning(f"Trade execution issue: {pipeline_result.get('status')}")
                        decision["trade_status"] = "error"
                except Exception as e:
                    self.logger.error(f"Error executing trade pipeline: {e}")
                    decision["trade_status"] = "error"
                    decision["trade_error"] = str(e)
            else:
                if decision.get("action") == "HOLD":
                    decision["trade_status"] = "hold_no_action"
                else:
                    decision["trade_status"] = "disabled"
                
            # Also check if there are any open trades that need to be managed
            if self.execution_mode != "disabled":
                try:
                    # Check if any open trades need to be closed based on current market data
                    closed_trades = self.trade_executor.check_open_trades(event)
                    if closed_trades:
                        self.logger.info(f"Closed {len(closed_trades)} trades based on current market conditions")
                        decision["closed_trades"] = [t.get("trade_id") for t in closed_trades]
                except Exception as e:
                    self.logger.error(f"Error checking open trades: {e}")
                
            return decision
        except Exception as e:
            self.logger.error(f"Error processing market event: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "source": "live_trading_error"
            }
            
    def start_live_trading(self, iterations: Optional[int] = None) -> None:
        """
        Start live trading mode.
        
        Args:
            iterations: Optional number of iterations (None for infinite)
        """
        self.logger.info(f"Starting live trading for {self.symbol} with {self.poll_interval}s interval")
        
        # Start the performance tracker in the background
        self.performance_tracker.start_monitoring()
        self.logger.info("Performance tracking started")
        
        try:
            # Start the market data fetcher in live mode with our callback
            self.market_fetcher.start_live_mode(
                callback=self.process_market_event,
                iterations=iterations
            )
        finally:
            # Stop the performance tracker when trading stops
            self.performance_tracker.stop_monitoring()
            
            # Display performance summary if any trades were made
            try:
                metrics = self.performance_tracker.get_performance_metrics()
                if metrics and "overall" in metrics and metrics["overall"].get("total_trades", 0) > 0:
                    self.logger.info("Trading session completed, performance summary:")
                    for line in self.performance_tracker.get_performance_summary().split("\n"):
                        self.logger.info(line)
            except Exception as e:
                self.logger.error(f"Error generating performance summary: {e}")
        
        self.logger.info("Live trading session completed")

def main():
    """Main entry point for live trading mode."""
    parser = argparse.ArgumentParser(description="aGENtrader v2 Live Trading Mode")
    parser.add_argument("--symbol", type=str, help="Trading symbol (e.g., 'BTC/USDT')")
    parser.add_argument("--interval", type=str, help="Time interval (e.g., '1h', '15m')")
    parser.add_argument("--iterations", type=int, default=None, help="Number of iterations (default: infinite)")
    
    args = parser.parse_args()
    
    # Print banner
    print("\n" + "=" * 60)
    print("aGENtrader v2 Live Trading Mode")
    print("=" * 60)
    
    # Create and start live trading manager
    try:
        manager = LiveTradingManager(symbol=args.symbol, interval=args.interval)
        manager.start_live_trading(iterations=args.iterations)
    except KeyboardInterrupt:
        logger.info("Live trading interrupted by user")
    except Exception as e:
        logger.error(f"Error in live trading: {e}")
        
    print("\nLive trading session completed")
    print("=" * 60)

if __name__ == "__main__":
    main()
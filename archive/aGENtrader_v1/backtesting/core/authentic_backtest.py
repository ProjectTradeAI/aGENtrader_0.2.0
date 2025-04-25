#!/usr/bin/env python3
"""
Authentic Multi-Agent Backtesting System

This script provides a backtesting framework that uses real market data from the database
and integrates with the multi-agent decision framework.
"""
import os
import sys
import json
import logging
import argparse
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple

# Add parent directory to sys.path to allow importing orchestration module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/backtests/backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

class AuthenticBacktest:
    """
    Authentic multi-agent backtesting system using real market data
    """
    
    def __init__(self, symbol="BTCUSDT", interval="1h", 
                 start_date=None, end_date=None, 
                 initial_balance=10000.0,
                 output_dir="results",
                 strategy="multi_agent"):
        """
        Initialize the backtesting system.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Timeframe interval (e.g., "1h", "4h", "1d")
            start_date: Start date for backtest (datetime or str in format YYYY-MM-DD)
            end_date: End date for backtest (datetime or str in format YYYY-MM-DD)
            initial_balance: Initial balance for backtesting
            output_dir: Directory to save results
            strategy: Trading strategy to use (default: multi_agent)
        """
        self.logger = logging.getLogger("authentic_backtest")
        self.logger.info("Initializing authentic backtesting system")
        
        # Set parameters
        self.symbol = symbol
        self.interval = interval
        self.initial_balance = float(initial_balance)
        self.output_dir = output_dir
        self.strategy = strategy
        self.logger.info(f"Using strategy: {strategy}")
        
        # Process dates
        if isinstance(start_date, str):
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        elif isinstance(start_date, datetime):
            self.start_date = start_date
        else:
            # Use a known start date where we have data
            self.start_date = datetime(2025, 3, 10)
            
        if isinstance(end_date, str):
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        elif isinstance(end_date, datetime):
            self.end_date = end_date
        else:
            # Use the last available data date instead of current date
            self.end_date = datetime(2025, 3, 24, 19, 0, 0)
            
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs("logs/backtests", exist_ok=True)
        
        # Set up trading environment
        self.balance = self.initial_balance
        self.position = 0
        self.position_entry_price = 0
        self.trades = []
        self.equity_curve = []
        
        # Load market data
        self.logger.info(f"Loading market data for {symbol} {interval} from {self.start_date} to {self.end_date}")
        self.market_data = self.get_historical_market_data(symbol, interval, self.start_date, self.end_date)
        
        if not self.market_data:
            self.logger.error(f"Failed to load market data for {symbol} {interval}")
            return
            
        self.logger.info(f"Loaded {len(self.market_data)} candles for {symbol} {interval}")
        
        # Initialize results
        self.results = {
            "symbol": symbol,
            "interval": interval,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "initial_balance": initial_balance,
            "strategy": strategy,
            "trades": [],
            "equity_curve": [],
            "performance_metrics": {}
        }
        
        # Try to import decision session
        try:
            from orchestration.decision_session import DecisionSession
            self.logger.info("Successfully imported DecisionSession")
            self.decision_session = DecisionSession()
            self.has_decision_session = True
        except ImportError as e:
            self.logger.warning(f"Could not import DecisionSession: {str(e)}")
            self.has_decision_session = False
            
    def get_historical_market_data(self, symbol, interval, start_date, end_date):
        """Get historical market data from the database."""
        self.logger.info(f"Getting historical market data for {symbol} {interval} from {start_date} to {end_date}")
        
        # Convert dates to strings in format YYYY-MM-DD
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # Connect to the database
        conn = None
        try:
            # Use the database URL from environment if available
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                self.logger.error("DATABASE_URL environment variable is not set")
                return None
                
            self.logger.info(f"Using database URL: {db_url[:10]}...{db_url[-10:]}")
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Query to get historical market data directly from market_data table
            query = """
                SELECT 
                    timestamp, 
                    open, 
                    high, 
                    low, 
                    close, 
                    volume 
                FROM 
                    market_data 
                WHERE 
                    symbol = %s 
                    AND interval = %s
                    AND timestamp >= %s 
                    AND timestamp <= %s 
                ORDER BY 
                    timestamp
            """
            
            cursor.execute(query, (symbol, interval, start_str, end_str))
            
            # Get results
            results = cursor.fetchall()
            
            if not results:
                self.logger.warning(f"No market data found for {symbol} {interval} from {start_date} to {end_date}")
                return None
            
            # Convert results to list of dictionaries
            market_data = []
            for row in results:
                market_data.append({
                    "timestamp": row[0],
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5])
                })
            
            self.logger.info(f"Found {len(market_data)} candles for {symbol} {interval}")
            
            return market_data
        
        except Exception as e:
            self.logger.error(f"Error getting historical market data: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            if conn:
                conn.close()
            return None
        
        finally:
            if conn:
                conn.close()
                
    def run_backtest(self):
        """
        Run the backtest using multi-agent decision making
        """
        self.logger.info(f"Starting backtest for {self.symbol} {self.interval}")
        self.logger.info(f"Period: {self.start_date} to {self.end_date}")
        
        if not self.market_data:
            self.logger.error("No market data available")
            return False
            
        # Set up initial state
        self.balance = self.initial_balance
        self.position = 0  # 0 = no position, 1 = long, -1 = short
        self.position_entry_price = 0
        self.trades = []
        self.equity_curve = []
        
        # Record initial equity
        self.equity_curve.append({
            "timestamp": self.market_data[0]["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "equity": self.balance,
            "balance": self.balance,
            "position": 0,
            "price": self.market_data[0]["close"]
        })
        
        # Run through each candle
        for i, candle in enumerate(self.market_data):
            # Skip the first few candles as we need some history for analysis
            if i < 10:
                continue
                
            # Get the current market data slice (current candle and some history)
            current_data = self.market_data[max(0, i-50):i+1]
            current_price = candle["close"]
            current_time = candle["timestamp"]
            
            # Update equity curve
            position_value = 0
            if self.position != 0:
                # Calculate current position value
                position_size = self.position * (self.balance / self.position_entry_price)
                position_value = position_size * current_price
                
            current_equity = self.balance + position_value
            
            self.equity_curve.append({
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "equity": current_equity,
                "balance": self.balance,
                "position": self.position,
                "price": current_price
            })
            
            # Make trading decision
            decision = self.make_trading_decision(current_data, i)
            
            # Execute trading decision
            if decision and "action" in decision:
                action = decision["action"]
                
                # Handle entry signals
                if action == "BUY" and self.position <= 0:
                    # Close any existing short position
                    if self.position < 0:
                        self.close_position(current_price, current_time, "Short position closed")
                        
                    # Enter long position
                    self.enter_position(1, current_price, current_time, decision.get("reasoning", ""))
                    
                elif action == "SELL" and self.position >= 0:
                    # Close any existing long position
                    if self.position > 0:
                        self.close_position(current_price, current_time, "Long position closed")
                    
                # Handle exit signals
                elif action == "EXIT" and self.position != 0:
                    self.close_position(current_price, current_time, decision.get("reasoning", ""))
                    
        # Close any open position at the end of the backtest
        if self.position != 0:
            last_candle = self.market_data[-1]
            self.close_position(last_candle["close"], last_candle["timestamp"], "End of backtest")
        
        # Calculate performance metrics
        self.calculate_performance()
        
        # Save results
        self.save_results()
        
        self.logger.info(f"Backtest completed. Final equity: ${self.equity_curve[-1]['equity']:.2f}")
        return True
        
    def make_trading_decision(self, current_data, current_index):
        """
        Make trading decision using multi-agent framework or fallback strategy
        
        Args:
            current_data: Current market data slice
            current_index: Current index in the full dataset
            
        Returns:
            Decision dictionary with action and reasoning
        """
        current_candle = current_data[-1]
        current_price = current_candle["close"]
        current_timestamp = current_candle["timestamp"]
        
        # Check if decision session is available for agent-based decisions
        if self.has_decision_session:
            try:
                # Prepare market data for the decision session
                market_data_dict = {
                    "recent_data": current_data[-20:],  # Last 20 candles
                    "current_price": current_price,
                    "timestamp": current_timestamp
                }
                
                # Run the decision session
                self.logger.info(f"Running decision session for {self.symbol} at {current_timestamp}")
                
                # Prepare market data for the decision
                recent_candles = current_data[-20:]  # Last 20 candles
                
                # Format market data for the decision session
                market_data_dict = {
                    "recent_data": recent_candles,
                    "recent_prices": [(candle["timestamp"].strftime("%Y-%m-%d %H:%M:%S"), candle["close"]) 
                                     for candle in recent_candles],
                    "volume_24h": sum(candle["volume"] for candle in recent_candles[-24:] if candle),
                    "change_24h": (current_price / recent_candles[-25]["close"] - 1) * 100 if len(recent_candles) >= 25 else 0
                }
                
                session_result = self.decision_session.run_decision(
                    symbol=self.symbol, 
                    interval=self.interval,
                    current_price=current_price,
                    market_data=market_data_dict
                )
                
                if session_result and session_result.get("status") == "success":
                    decision = session_result.get("decision", {})
                    self.logger.info(f"Decision: {decision.get('action')} with confidence {decision.get('confidence', 0)}")
                    return decision
                else:
                    self.logger.warning(f"Decision session failed or returned no decision: {session_result}")
                    # Fall back to simple strategy
                    return self.simple_strategy_decision(current_data)
            except Exception as e:
                self.logger.error(f"Error in agent decision making: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                # Fall back to simple strategy
                return self.simple_strategy_decision(current_data)
        else:
            # Use simple strategy if decision session is not available
            return self.simple_strategy_decision(current_data)
    
    def simple_strategy_decision(self, data):
        """
        Simple trading strategy as fallback
        
        Args:
            data: Current market data slice
            
        Returns:
            Decision dictionary
        """
        # Use a simple moving average crossover strategy
        if len(data) < 20:
            return {"action": "HOLD", "reasoning": "Not enough data"}
            
        # Calculate short and long moving averages
        short_period = 5
        long_period = 20
        
        short_ma = sum(candle["close"] for candle in data[-short_period:]) / short_period
        long_ma = sum(candle["close"] for candle in data[-long_period:]) / long_period
        
        # Previous values
        prev_short_ma = sum(candle["close"] for candle in data[-short_period-1:-1]) / short_period
        prev_long_ma = sum(candle["close"] for candle in data[-long_period-1:-1]) / long_period
        
        # Current price
        current_price = data[-1]["close"]
        
        # Check for crossovers
        prev_short_above = prev_short_ma > prev_long_ma
        current_short_above = short_ma > long_ma
        
        # Trading logic
        if not prev_short_above and current_short_above:
            # Bullish crossover
            return {
                "action": "BUY",
                "confidence": 0.7,
                "price": current_price,
                "reasoning": f"Bullish crossover: Short MA {short_ma:.2f} crossed above Long MA {long_ma:.2f}"
            }
        elif prev_short_above and not current_short_above:
            # Bearish crossover
            return {
                "action": "SELL",
                "confidence": 0.7,
                "price": current_price,
                "reasoning": f"Bearish crossover: Short MA {short_ma:.2f} crossed below Long MA {long_ma:.2f}"
            }
        else:
            # No crossover
            return {
                "action": "HOLD",
                "confidence": 0.5,
                "price": current_price,
                "reasoning": f"No crossover detected. Short MA: {short_ma:.2f}, Long MA: {long_ma:.2f}"
            }
    
    def enter_position(self, direction, price, timestamp, reason=""):
        """
        Enter a trading position
        
        Args:
            direction: 1 for long, -1 for short
            price: Entry price
            timestamp: Entry time
            reason: Reason for entry
        """
        if direction == 0:
            return
            
        # Record the trade
        trade = {
            "type": "ENTRY",
            "direction": "LONG" if direction > 0 else "SHORT",
            "price": price,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "balance": self.balance,
            "reason": reason
        }
        
        self.position = direction
        self.position_entry_price = price
        self.trades.append(trade)
        
        self.logger.info(f"Entered {trade['direction']} position at {price} ({timestamp})")
        
    def close_position(self, price, timestamp, reason=""):
        """
        Close an existing position
        
        Args:
            price: Exit price
            timestamp: Exit time
            reason: Reason for exit
        """
        if self.position == 0:
            return
            
        # Calculate profit/loss
        if self.position > 0:  # Long position
            pnl_pct = (price / self.position_entry_price - 1) * 100
        else:  # Short position
            pnl_pct = (self.position_entry_price / price - 1) * 100
            
        pnl_amount = self.balance * (pnl_pct / 100)
        new_balance = self.balance + pnl_amount
        
        # Record the trade
        trade = {
            "type": "EXIT",
            "direction": "LONG" if self.position > 0 else "SHORT",
            "entry_price": self.position_entry_price,
            "exit_price": price,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "pnl_percentage": pnl_pct,
            "pnl_amount": pnl_amount,
            "old_balance": self.balance,
            "new_balance": new_balance,
            "reason": reason
        }
        
        self.trades.append(trade)
        self.balance = new_balance
        self.position = 0
        self.position_entry_price = 0
        
        self.logger.info(f"Closed {trade['direction']} position at {price} ({timestamp}). PnL: {pnl_pct:.2f}% (${pnl_amount:.2f})")
        
    def calculate_performance(self):
        """Calculate performance metrics"""
        if not self.equity_curve:
            return
            
        # Extract relevant data
        timestamps = [entry["timestamp"] for entry in self.equity_curve]
        equity = [entry["equity"] for entry in self.equity_curve]
        
        # Calculate returns
        returns = []
        for i in range(1, len(equity)):
            returns.append((equity[i] / equity[i-1]) - 1)
            
        # Calculate metrics
        total_return = (equity[-1] / equity[0] - 1) * 100
        
        # Count trades
        winning_trades = [t for t in self.trades if t.get("type") == "EXIT" and t.get("pnl_amount", 0) > 0]
        losing_trades = [t for t in self.trades if t.get("type") == "EXIT" and t.get("pnl_amount", 0) <= 0]
        
        win_rate = len(winning_trades) / max(1, len(winning_trades) + len(losing_trades)) * 100
        
        # Calculate average win/loss
        avg_win = sum(t.get("pnl_amount", 0) for t in winning_trades) / max(1, len(winning_trades))
        avg_loss = sum(t.get("pnl_amount", 0) for t in losing_trades) / max(1, len(losing_trades))
        
        # Calculate max drawdown
        max_equity = equity[0]
        max_drawdown = 0
        max_drawdown_pct = 0
        
        for i in range(1, len(equity)):
            max_equity = max(max_equity, equity[i])
            drawdown = max_equity - equity[i]
            drawdown_pct = drawdown / max_equity * 100
            max_drawdown = max(max_drawdown, drawdown)
            max_drawdown_pct = max(max_drawdown_pct, drawdown_pct)
            
        # Annualized return (approximation)
        days = (datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S") - 
                datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S")).days
        annualized_return = ((1 + total_return / 100) ** (365 / max(1, days)) - 1) * 100
        
        # Store metrics
        self.results["performance_metrics"] = {
            "initial_balance": self.equity_curve[0]["balance"],
            "final_equity": equity[-1],
            "total_return_pct": total_return,
            "annualized_return_pct": annualized_return,
            "max_drawdown_pct": max_drawdown_pct,
            "max_drawdown_amount": max_drawdown,
            "total_trades": len(winning_trades) + len(losing_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": abs(sum(t.get("pnl_amount", 0) for t in winning_trades) / 
                              max(0.01, abs(sum(t.get("pnl_amount", 0) for t in losing_trades))))
        }
        
        # Store trades and equity curve
        self.results["trades"] = self.trades
        self.results["equity_curve"] = self.equity_curve
        
        # Log results
        self.logger.info(f"Backtest Results for {self.symbol} {self.interval}")
        self.logger.info(f"Period: {self.start_date} to {self.end_date}")
        self.logger.info(f"Initial Balance: ${self.initial_balance:.2f}")
        self.logger.info(f"Final Equity: ${equity[-1]:.2f}")
        self.logger.info(f"Total Return: {total_return:.2f}%")
        self.logger.info(f"Annualized Return: {annualized_return:.2f}%")
        self.logger.info(f"Win Rate: {win_rate:.2f}% ({len(winning_trades)}/{len(winning_trades) + len(losing_trades)})")
        self.logger.info(f"Max Drawdown: {max_drawdown_pct:.2f}% (${max_drawdown:.2f})")
        
    def save_results(self):
        """Save backtest results to file"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/backtest_{self.symbol}_{self.interval}_{timestamp}.json"
            
            # Save results to file
            with open(filename, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            
            # Store the filename for possible later renaming
            self.last_result_file = filename
                
            self.logger.info(f"Results saved to {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")
            return None

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run authentic backtests using real market data")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--interval", type=str, default="1h", help="Timeframe interval")
    parser.add_argument("--start_date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, help="Number of days to backtest (alternative to start_date)")
    parser.add_argument("--initial_balance", type=float, default=10000.0, help="Initial balance")
    parser.add_argument("--output_dir", type=str, default="results", help="Output directory")
    parser.add_argument("--output", type=str, help="Output file path (overrides output_dir)")
    parser.add_argument("--strategy", type=str, default="multi_agent", help="Trading strategy to use")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Set up logging based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.info("Verbose logging enabled")
    
    # Calculate start_date from days if provided and start_date not set
    if args.days and not args.start_date:
        # Since we have market data from 2025-02-17 to 2025-03-24, use that range instead of current date
        reference_date = datetime(2025, 3, 17)  # Use a date we know has data, about a week before the latest date
        start_date = reference_date - timedelta(days=args.days)
        args.start_date = start_date.strftime('%Y-%m-%d')
        # If no end date is provided, use a date we know has data
        if not args.end_date:
            args.end_date = "2025-03-24"
        logging.info(f"Calculated start date from days: {args.start_date}")
        logging.info(f"Using end date: {args.end_date}")
    
    # Determine output directory or specific output file
    output_dir = args.output_dir
    output_file = None
    if args.output:
        output_file = args.output
        output_dir = os.path.dirname(args.output)
        if not output_dir:
            output_dir = "."
        logging.info(f"Using specific output file: {output_file}")
    
    # Create the backtest
    backtest = AuthenticBacktest(
        symbol=args.symbol,
        interval=args.interval,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_balance=args.initial_balance,
        output_dir=output_dir,
        strategy=args.strategy
    )
    
    # Run the backtest
    success = backtest.run_backtest()
    
    # If output file is specified and backtest was successful, rename the result file
    if success and output_file and hasattr(backtest, 'last_result_file'):
        try:
            os.rename(backtest.last_result_file, output_file)
            logging.info(f"Renamed result file to {output_file}")
        except Exception as e:
            logging.error(f"Failed to rename result file: {str(e)}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

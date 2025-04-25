#!/usr/bin/env python3
"""
Fix for the market_data_adapter.py script to handle reserved keyword 'timestamp'
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fix_adapter_script")

def fix_market_data_adapter(file_path):
    """
    Fix the SQL syntax error in market_data_adapter.py
    
    Args:
        file_path: Path to the market_data_adapter.py file on EC2
    """
    try:
        # Create the fixed SQL function
        fixed_function = """
        CREATE OR REPLACE FUNCTION get_market_data_by_interval(
            p_symbol TEXT,
            p_interval TEXT,
            p_start_date TIMESTAMP,
            p_end_date TIMESTAMP
        )
        RETURNS TABLE (
            time_stamp TIMESTAMP,
            open_price NUMERIC,
            high_price NUMERIC,
            low_price NUMERIC,
            close_price NUMERIC,
            volume_val NUMERIC
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                md.timestamp as time_stamp,
                md.open as open_price,
                md.high as high_price,
                md.low as low_price,
                md.close as close_price,
                md.volume as volume_val
            FROM
                market_data md
            WHERE
                md.symbol = p_symbol
                AND md.interval = p_interval
                AND md.timestamp >= p_start_date
                AND md.timestamp <= p_end_date
            ORDER BY
                md.timestamp;
        END;
        $$;
        """
        
        # Create fixed SQL view creation
        fixed_view = """
            CREATE VIEW {view_name} AS
            SELECT
                symbol,
                timestamp as time_stamp,
                open as open_price,
                high as high_price,
                low as low_price,
                close as close_price,
                volume as volume_val
            FROM
                market_data
            WHERE
                interval = '{interval}'
        """
        
        # Create the fixed adapter script
        with open("fixed_market_data_adapter.py", "w") as f:
            f.write("""#!/usr/bin/env python3
\"\"\"
Market Data Adapter for Multi-Agent Backtesting (Fixed Version)

This script adapts the market_data table for use with the authentic backtesting framework.
It creates functions to access the data in the format expected by agents.
\"\"\"
import os
import sys
import json
import time
import logging
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime, timedelta
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/db_adapter_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("market_data_adapter_fixed")

class MarketDataAdapter:
    \"\"\"Adapter for the market_data database schema\"\"\"
    
    def __init__(self, db_url=None):
        \"\"\"Initialize the adapter\"\"\"
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        logger.info(f"Initializing with database URL: {self.db_url[:10]}...{self.db_url[-10:]}")
        
        # Test connection
        self.test_connection()
    
    def test_connection(self):
        \"\"\"Test the database connection\"\"\"
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"Connected to PostgreSQL: {version[0]}")
            
            # Check if market_data table exists
            cursor.execute(\"\"\"
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'market_data'
                );
            \"\"\")
            
            if cursor.fetchone()[0]:
                logger.info("market_data table exists")
                
                # Check columns
                cursor.execute(\"\"\"
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'market_data';
                \"\"\")
                
                columns = [row[0] for row in cursor.fetchall()]
                logger.info(f"market_data columns: {', '.join(columns)}")
                
                # Check for data
                cursor.execute("SELECT COUNT(*) FROM market_data")
                count = cursor.fetchone()[0]
                logger.info(f"market_data contains {count} rows")
                
                # Check for intervals
                cursor.execute("SELECT DISTINCT interval FROM market_data")
                intervals = [row[0] for row in cursor.fetchall()]
                logger.info(f"Available intervals: {', '.join(intervals)}")
                
                # Sample data
                cursor.execute(\"\"\"
                    SELECT symbol, interval, timestamp, open, high, low, close, volume
                    FROM market_data
                    ORDER BY timestamp DESC
                    LIMIT 1
                \"\"\")
                sample = cursor.fetchone()
                if sample:
                    logger.info(f"Sample data: {sample}")
            else:
                logger.error("market_data table does not exist")
                
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            traceback.print_exc()
            return False
        finally:
            if conn:
                conn.close()
    
    def create_data_access_functions(self):
        \"\"\"Create functions to access market data for backtesting\"\"\"
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Create function to get market data by interval (fixed to avoid reserved keyword issues)
            logger.info("Creating function get_market_data_by_interval")
            cursor.execute(\"\"\"{}\"\"\"
            )
            
            # Create views for common intervals
            intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
            
            for interval in intervals:
                view_name = f"market_data_{interval.replace('m', 'min').replace('h', 'hour').replace('d', 'day')}"
                logger.info(f"Creating view {{view_name}}")
                
                try:
                    # Drop view if it exists
                    cursor.execute(f"DROP VIEW IF EXISTS {{view_name}}")
                    
                    # Create view with fixed column names to avoid reserved keywords
                    cursor.execute(f\"\"\"{}\"\"\"
                    .format(interval=interval, view_name=view_name))
                    
                    logger.info(f"View {{view_name}} created successfully")
                except Exception as e:
                    logger.error(f"Error creating view {{view_name}}: {{str(e)}}")
            
            # Create helper function to get the most recent data point
            logger.info("Creating function get_latest_price")
            cursor.execute(\"\"\"
            CREATE OR REPLACE FUNCTION get_latest_market_data(
                p_symbol TEXT,
                p_interval TEXT DEFAULT '1h'
            )
            RETURNS TABLE (
                symbol TEXT,
                interval TEXT,
                time_stamp TIMESTAMP,
                open_price NUMERIC,
                high_price NUMERIC,
                low_price NUMERIC,
                close_price NUMERIC,
                volume_val NUMERIC
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    md.symbol,
                    md.interval,
                    md.timestamp as time_stamp,
                    md.open as open_price,
                    md.high as high_price,
                    md.low as low_price,
                    md.close as close_price,
                    md.volume as volume_val
                FROM
                    market_data md
                WHERE
                    md.symbol = p_symbol
                    AND md.interval = p_interval
                ORDER BY
                    md.timestamp DESC
                LIMIT 1;
            END;
            $$;
            \"\"\")
            
            logger.info("Data access functions created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create data access functions: {{str(e)}}")
            traceback.print_exc()
            return False
        finally:
            if conn:
                conn.close()
    
    def get_data_availability(self):
        \"\"\"Get information about available data\"\"\"
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get data date ranges
            cursor.execute(\"\"\"
                SELECT 
                    symbol,
                    interval,
                    MIN(timestamp) as start_date,
                    MAX(timestamp) as end_date,
                    COUNT(*) as row_count
                FROM
                    market_data
                GROUP BY
                    symbol, interval
                ORDER BY
                    symbol, interval
            \"\"\")
            
            availability = {{}}
            rows = cursor.fetchall()
            
            for row in rows:
                symbol = row['symbol']
                interval = row['interval']
                
                if symbol not in availability:
                    availability[symbol] = {{}}
                
                availability[symbol][interval] = {{
                    "start_date": row['start_date'].strftime("%Y-%m-%d %H:%M:%S"),
                    "end_date": row['end_date'].strftime("%Y-%m-%d %H:%M:%S"),
                    "count": row['row_count']
                }}
            
            return availability
        except Exception as e:
            logger.error(f"Failed to get data availability: {{str(e)}}")
            traceback.print_exc()
            return {{}}
        finally:
            if conn:
                conn.close()

def main():
    \"\"\"Main entry point\"\"\"
    try:
        # Ensure database URL is set
        if not os.environ.get("DATABASE_URL"):
            logger.error("DATABASE_URL environment variable is not set")
            return False
        
        # Create adapter
        adapter = MarketDataAdapter()
        
        # Create data access functions
        success = adapter.create_data_access_functions()
        
        if success:
            # Get data availability
            availability = adapter.get_data_availability()
            
            # Print availability in a nice format
            logger.info("Data availability:")
            for symbol, intervals in availability.items():
                logger.info(f"Symbol: {{symbol}}")
                for interval, data in intervals.items():
                    logger.info(f"  {{interval}}: {{data['start_date']}} to {{data['end_date']}} ({{data['count']}} records)")
            
            print("\\nRecommended date ranges for backtesting:")
            for symbol, intervals in availability.items():
                if symbol == "BTCUSDT":  # Focus on BTC for now
                    for interval in ["1h", "4h", "1d"]:
                        if interval in intervals:
                            print(f"  BTCUSDT {{interval}}: {{intervals[interval]['start_date']}} to {{intervals[interval]['end_date']}}")
            
            return True
        else:
            logger.error("Failed to set up data access functions")
            return False
    
    except Exception as e:
        logger.error(f"Error in main: {{str(e)}}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ Market data adapter setup completed successfully")
    else:
        print("❌ Market data adapter setup failed")
        sys.exit(1)
""".format(fixed_function, fixed_view))
        
        logger.info("Created fixed market data adapter script")
        return True
    except Exception as e:
        logger.error(f"Failed to create fixed adapter: {str(e)}")
        return False

def fix_authentic_backtest_patch(file_path):
    """
    Create a simpler patch for authentic_backtest.py
    
    Args:
        file_path: Path to the patch_authentic_backtest.py file
    """
    try:
        # Create a simpler patch script
        with open("simple_backtest_patch.py", "w") as f:
            f.write("""#!/usr/bin/env python3
\"\"\"
Simple patch for authentic_backtest.py
\"\"\"
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simple_patch_script")

def create_authentic_backtest():
    \"\"\"
    Create a simplified authentic_backtest.py file that works with the market_data table
    \"\"\"
    try:
        # Create directory if it doesn't exist
        os.makedirs("backtesting/core", exist_ok=True)
        
        # Create the file
        with open("backtesting/core/authentic_backtest.py", "w") as f:
            f.write(\"\"\"
import os
import sys
import json
import logging
import argparse
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple

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
    \"\"\"
    Authentic multi-agent backtesting system using real market data
    \"\"\"
    
    def __init__(self, symbol="BTCUSDT", interval="1h", 
                 start_date=None, end_date=None, 
                 initial_balance=10000.0,
                 output_dir="results"):
        \"\"\"
        Initialize the backtesting system.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Timeframe interval (e.g., "1h", "4h", "1d")
            start_date: Start date for backtest (datetime or str in format YYYY-MM-DD)
            end_date: End date for backtest (datetime or str in format YYYY-MM-DD)
            initial_balance: Initial balance for backtesting
            output_dir: Directory to save results
        \"\"\"
        self.logger = logging.getLogger("authentic_backtest")
        self.logger.info("Initializing authentic backtesting system")
        
        # Set parameters
        self.symbol = symbol
        self.interval = interval
        self.initial_balance = float(initial_balance)
        self.output_dir = output_dir
        
        # Process dates
        if isinstance(start_date, str):
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        elif isinstance(start_date, datetime):
            self.start_date = start_date
        else:
            self.start_date = datetime.now() - timedelta(days=30)
            
        if isinstance(end_date, str):
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        elif isinstance(end_date, datetime):
            self.end_date = end_date
        else:
            self.end_date = datetime.now()
            
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
            "trades": [],
            "equity_curve": [],
            "performance_metrics": {}
        }
        
        # Try to import decision session
        try:
            from orchestration.decision_session import DecisionSession
            self.logger.info("Successfully imported DecisionSession")
            self.decision_session = DecisionSession(symbol=symbol)
            self.has_decision_session = True
        except ImportError as e:
            self.logger.warning(f"Could not import DecisionSession: {str(e)}")
            self.has_decision_session = False
            
    def get_historical_market_data(self, symbol, interval, start_date, end_date):
        \"\"\"Get historical market data from the database.\"\"\"
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
            query = \"\"\"
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
            \"\"\"
            
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
        \"\"\"
        Run the backtest using multi-agent decision making
        \"\"\"
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
                        
                    # Enter short position (if enabled)
                    # self.enter_position(-1, current_price, current_time, decision.get("reasoning", ""))
                    
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
        \"\"\"
        Make trading decision using multi-agent framework or fallback strategy
        
        Args:
            current_data: Current market data slice
            current_index: Current index in the full dataset
            
        Returns:
            Decision dictionary with action and reasoning
        \"\"\"
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
                session_result = self.decision_session.run_session(
                    symbol=self.symbol, 
                    current_price=current_price
                )
                
                if session_result and session_result.get("status") == "completed":
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
        \"\"\"
        Simple trading strategy as fallback
        
        Args:
            data: Current market data slice
            
        Returns:
            Decision dictionary
        \"\"\"
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
        \"\"\"
        Enter a trading position
        
        Args:
            direction: 1 for long, -1 for short
            price: Entry price
            timestamp: Entry time
            reason: Reason for entry
        \"\"\"
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
        \"\"\"
        Close an existing position
        
        Args:
            price: Exit price
            timestamp: Exit time
            reason: Reason for exit
        \"\"\"
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
        \"\"\"Calculate performance metrics\"\"\"
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
        \"\"\"Save backtest results to file\"\"\"
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/backtest_{self.symbol}_{self.interval}_{timestamp}.json"
            
            # Save results to file
            with open(filename, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
                
            self.logger.info(f"Results saved to {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")
            return None

def parse_arguments():
    \"\"\"Parse command line arguments\"\"\"
    parser = argparse.ArgumentParser(description="Run authentic backtests using real market data")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--interval", type=str, default="1h", help="Timeframe interval")
    parser.add_argument("--start_date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--initial_balance", type=float, default=10000.0, help="Initial balance")
    parser.add_argument("--output_dir", type=str, default="results", help="Output directory")
    
    return parser.parse_args()

def main():
    \"\"\"Main entry point\"\"\"
    args = parse_arguments()
    
    # Create the backtest
    backtest = AuthenticBacktest(
        symbol=args.symbol,
        interval=args.interval,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_balance=args.initial_balance,
        output_dir=args.output_dir
    )
    
    # Run the backtest
    success = backtest.run_backtest()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
\"\"\")
        
        logger.info("Created simplified authentic_backtest.py")
        return True
    except Exception as e:
        logger.error(f"Failed to create authentic_backtest.py: {str(e)}")
        return False

def main():
    \"\"\"Main entry point\"\"\"
    # Create fixed adapter script
    success1 = fix_market_data_adapter("market_data_adapter.py")
    
    # Create simplified authentic_backtest implementation
    success2 = create_authentic_backtest()
    
    if success1 and success2:
        print("✅ Fixes created successfully")
        print("To apply fixes:")
        print("1. Upload fixed_market_data_adapter.py to EC2")
        print("2. On EC2, run: python3 fixed_market_data_adapter.py")
        print("3. Run backtest with: ./run_full_backtest.sh")
        return 0
    else:
        print("❌ Failed to create fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())
\"\"\")
        
        logger.info("Created simplified backtest patch script")
        return True
    except Exception as e:
        logger.error(f"Failed to create simplified patch: {str(e)}")
        return False

if __name__ == "__main__":
    # Create fixed scripts
    fixed_adapter = fix_market_data_adapter("market_data_adapter.py")
    fixed_patch = fix_authentic_backtest_patch("patch_authentic_backtest.py")
    
    if fixed_adapter and fixed_patch:
        print("✅ Fixed scripts created successfully")
        print("\nTo apply fixes:")
        print("1. Run: ./deploy-db-fixes.sh")
    else:
        print("❌ Failed to create fixed scripts")
        sys.exit(1)
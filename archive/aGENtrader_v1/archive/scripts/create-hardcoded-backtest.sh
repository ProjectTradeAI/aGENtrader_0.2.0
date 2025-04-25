#!/bin/bash
# Script to create and run a hardcoded backtest solution

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
  echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

log_info() {
  echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Welcome message
log "🔨 Creating Hardcoded Backtest Solution"
log "==================================================="

# Step 1: Get database URL
log "Step 1: Getting database URL..."

# Get database URL using node
DB_URL=$(node -e "console.log(process.env.DATABASE_URL || '')")

if [ -z "$DB_URL" ]; then
  log_error "DATABASE_URL environment variable is not set!"
  exit 1
fi

# Get alpaca keys
ALPACA_API_KEY=$(node -e "console.log(process.env.ALPACA_API_KEY || '')")
ALPACA_API_SECRET=$(node -e "console.log(process.env.ALPACA_API_SECRET || '')")

# Mask the URL for security in the logs
MASKED_URL="${DB_URL:0:10}...${DB_URL: -10}"
log_info "Got database URL: $MASKED_URL"

# Step 2: Set up EC2 connection
log "Step 2: Setting up EC2 connection..."

# Set parameters
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Create key file using the hardcoded key
log_info "Creating EC2 key file..."
cat > "$KEY_PATH" << 'KEYEOF'
-----BEGIN RSA PRIVATE KEY-----
MIIEoQIBAAKCAQEAyxNT6X+1frDllJPAbCAjOjNV6+IYbJTBJF+NNUESxrYsMK8J
1Dt4OBuXKSMV7nttmb6/jy6tItkztExoPyqr1QuKwHUInkbkKTm15Cl90o6yzXba
UfntOfpwZHwmEOJRVniLRJPzkOldOplyTiIxaf8mZKLeaXDlleaHZlNyrBWs9wNN
gJJbCBve2Z1TJsZeRig3u0Tg0+xo1BPxSm8dROalr8/30UrXpCkDQVL5S3oA2kSd
6hvwQhUZclGNheGgLOGTMtZ/FxGAI/mVsD29ErWnEoysLGCpbLfXpw7o3yEDCND+
cpqtV+ckbTeX2gqbugyZmBVrxcnbafwW1ykoaQIDAQABAoIBAE53gmXn1c5FNgBp
8uEUrefwLBQAAeX6uIKAdUSNh17Gx15sVATwkaxEZO0dRH0orhnJDaWaqIWdnY/e
Mi2uJEUmt49T6WeXBtQzG2g07Awu3UHs2cDxLEvJzCHXorHFcR5TZ6Sw8l0c/swE
vJkaNzO4xjH+iKf/WobIU6sjNVzuNjJF7TNUJ/kZmfZHOjOKCSBF/ahY+weeVBFp
lqaSKrNINPYoYn4nrAgWVxMiPqItWhm3Y9G3c3z9ePNJKRkNKnRB+pCfGS3EZTq0
deI3rcurPsBe34B/SxZF7G1hLVhEtom18YUbZvSBxgCJmI7D239e/Qz6bgqB7FAo
rFJ/S3ECgYEA+oCEP5NjBilqOHSdLLPhI/Ak6pNIK017xMBdiBTjnRh93D8Xzvfh
glkHRisZo8gmIZsgW3izlEeUv4CaVf7OzlOUiu2KmmrLxGHPoT+QPLf/Ak3GZE14
XY9vtaQQSwxM+i5sNtAD/3/KcjH6wT1B+8R4xqtHUYXw7VoEQWRSs/UCgYEAz4hW
j7+ooYlyHzkfuiEMJG0CtKR/fYsd9Zygn+Y6gGQvCiL+skAmx/ymG/qU6D8ZejkN
Azzv7JGQ+1z8OtTNStgDPE7IT74pA0BC60jHySDYzyGAaoMJDhHxA2CPm60EwPDU
5pRVy+FN5LmCCT8oDgcpsPpgjALOqR2TUkcOziUCgYAFXdN3eTTZ4PFBnF3xozjj
iDWCQP1+z/4izOw0Ch6GMwwfN8rOyEiwfi/FtQ6rj5Ihji03SHKwboglQiAMT5Um
nmvEPiqF/Fu5LU9BaRcx9c8kwX3KkE5P0s7V2VnwAad0hKIU2of7ZUV1BNUWZrWP
KzpbJzgz6uaqbw9AR2HuMQJ/YuaWWer8cf8OY9LVS95z6ugIYg4Cs9GYdXQvGASf
3I/h2vLSbiAkWyoL/0lrrUJk4dpOWTyxGgxFC4VErsS7EO/gmtzwmRAGe4YkXfxR
OYhtykgs6pWHuyzRrspVpdrOaSRcUYZfXMoCVP4S+lUewZCoTa8EU7UCx5VQn+U9
KQKBgQDsjVRcsfC/szL7KgeheEN/2zRADix5bqrg0rAB1y+sw+yzkCCh3jcRn2O2
wNIMroggGNy+vcR8Xo/V1wLCsEn45cxB6W7onqxFRM6IkGxkBgdatEL/aBnETSAI
x4C5J+IqaT2T53O2n3DR+GsVoeNUbz8j/lPONNQnV0ZqHRVWpA==
-----END RSA PRIVATE KEY-----
KEYEOF
chmod 600 "$KEY_PATH"

# Test the connection
log "Testing connection to EC2 instance at $EC2_IP..."
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'"; then
  log_error "Failed to connect to EC2 instance. Check your EC2_PUBLIC_IP variable."
  exit 1
fi

log_info "✅ Connection to EC2 established successfully."

# Step 3: Create a hardcoded backtest script on EC2
log "Step 3: Creating a hardcoded backtest script on EC2..."

# Create the backtest script content with hardcoded database URL
cat > backtest_hardcoded.py << EOF
#!/usr/bin/env python3
"""
Hardcoded Backtesting Script

This script implements a simple backtesting framework with the database URL
hardcoded directly into the script to avoid environment variable issues.
"""
import os
import sys
import logging
import argparse
import datetime
import traceback
import json
import psycopg2
import psycopg2.extras
from decimal import Decimal
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hardcoded_backtest")

# Hardcoded database URL directly in the script
DATABASE_URL = "${DB_URL}"
ALPACA_API_KEY = "${ALPACA_API_KEY}"
ALPACA_API_SECRET = "${ALPACA_API_SECRET}"

class Backtest:
    """Simple backtesting framework"""
    
    def __init__(self, symbol, interval, start_date, end_date, initial_balance=10000):
        """Initialize the backtest"""
        self.symbol = symbol
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.position = 0  # Current position size
        self.trades = []
        self.trade_history = []
        self.market_data = None
        self.logger = logger
        
        # Ensure output directories exist
        os.makedirs("logs/backtests", exist_ok=True)
        os.makedirs("results", exist_ok=True)
        
        # Setup log file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"logs/backtests/backtest_{timestamp}.log"
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)
        
        # Results file
        self.results_file = f"results/backtest_{timestamp}.json"
        
        logger.info(f"Backtesting environment set up for {symbol} {interval} from {start_date} to {end_date}")
        logger.info(f"Log file: {self.log_file}")
    
    def get_market_data(self):
        """Get market data from the database"""
        self.logger.info(f"Getting market data for {self.symbol} {self.interval} from {self.start_date} to {self.end_date}")
        
        # Connect to the database
        conn = None
        try:
            self.logger.info(f"Connecting to database: {DATABASE_URL[:10]}...{DATABASE_URL[-10:]}")
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Query to get market data
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
            
            # Convert dates to strings
            start_str = self.start_date.strftime("%Y-%m-%d")
            end_str = self.end_date.strftime("%Y-%m-%d")
            
            self.logger.info(f"Executing query for {self.symbol} {self.interval} from {start_str} to {end_str}")
            cursor.execute(query, (self.symbol, self.interval, start_str, end_str))
            
            # Get results
            results = cursor.fetchall()
            
            if not results:
                self.logger.warning(f"No market data found for {self.symbol} {self.interval}")
                return False
            
            # Convert results to list of dictionaries
            self.market_data = []
            for row in results:
                self.market_data.append({
                    "timestamp": row[0],
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5])
                })
            
            self.logger.info(f"Found {len(self.market_data)} candles for {self.symbol} {self.interval}")
            
            # Close database connection
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error getting market data: {str(e)}")
            traceback.print_exc()
            
            if conn:
                conn.close()
                
            return False
    
    def run(self):
        """Run the backtest"""
        self.logger.info("Running backtest...")
        
        # Get market data
        if not self.get_market_data():
            self.logger.error("No market data available for backtesting")
            return False
        
        # Simple example strategy: Buy when price is above 20-period SMA, sell when below
        df = pd.DataFrame(self.market_data)
        df['sma_20'] = df['close'].rolling(window=20).mean()
        
        # Skip the first 20 periods to allow SMA to calculate
        df = df.iloc[20:].reset_index(drop=True)
        
        # Initialize variables
        position = 0
        balance = self.initial_balance
        equity_curve = []
        
        # Loop through each candle
        for i in range(len(df) - 1):
            current_price = df.loc[i, 'close']
            next_price = df.loc[i + 1, 'open']
            sma = df.loc[i, 'sma_20']
            timestamp = df.loc[i, 'timestamp']
            
            # Record equity
            equity_curve.append({
                "timestamp": timestamp,
                "equity": balance + position * current_price
            })
            
            # Strategy: Buy when price crosses above SMA, sell when it crosses below
            if current_price > sma and position == 0:
                # Buy signal
                position_size = balance / current_price
                position = position_size
                balance = 0
                
                # Record trade
                self.trades.append({
                    "type": "buy",
                    "timestamp": timestamp,
                    "price": current_price,
                    "size": position_size,
                    "balance": balance
                })
                
                self.logger.info(f"BUY signal at {timestamp}: price={current_price}, size={position_size}")
                
            elif current_price < sma and position > 0:
                # Sell signal
                balance = position * current_price
                
                # Record trade
                self.trades.append({
                    "type": "sell",
                    "timestamp": timestamp,
                    "price": current_price,
                    "size": position,
                    "balance": balance
                })
                
                self.logger.info(f"SELL signal at {timestamp}: price={current_price}, size={position}, balance={balance}")
                position = 0
        
        # Close any open position at the end
        if position > 0:
            last_price = df.iloc[-1]['close']
            last_timestamp = df.iloc[-1]['timestamp']
            
            balance = position * last_price
            
            # Record trade
            self.trades.append({
                "type": "sell",
                "timestamp": last_timestamp,
                "price": last_price,
                "size": position,
                "balance": balance
            })
            
            self.logger.info(f"FINAL SELL at {last_timestamp}: price={last_price}, size={position}, balance={balance}")
            position = 0
        
        # Final equity value
        final_equity = balance + position * df.iloc[-1]['close']
        
        # Calculate trade statistics
        total_trades = len(self.trades)
        winning_trades = 0
        total_profit = 0
        
        if total_trades > 0:
            buy_trades = [t for t in self.trades if t['type'] == 'buy']
            sell_trades = [t for t in self.trades if t['type'] == 'sell']
            
            # Pair buys and sells to calculate trade performance
            for i in range(min(len(buy_trades), len(sell_trades))):
                buy = buy_trades[i]
                sell = sell_trades[i]
                
                profit = (sell['price'] - buy['price']) * buy['size']
                
                if profit > 0:
                    winning_trades += 1
                
                total_profit += profit
                
                # Record completed trade
                self.trade_history.append({
                    "entry_time": buy['timestamp'],
                    "exit_time": sell['timestamp'],
                    "entry_price": buy['price'],
                    "exit_price": sell['price'],
                    "size": buy['size'],
                    "profit": profit,
                    "profit_percent": (sell['price'] / buy['price'] - 1) * 100
                })
        
        # Calculate performance metrics
        start_balance = self.initial_balance
        end_balance = final_equity
        percent_return = (end_balance / start_balance - 1) * 100
        
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        # Save results
        results = {
            "symbol": self.symbol,
            "interval": self.interval,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "initial_balance": start_balance,
            "final_balance": end_balance,
            "profit": end_balance - start_balance,
            "percent_return": percent_return,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate": win_rate,
            "trade_history": self.trade_history,
            "equity_curve": equity_curve
        }
        
        # Save results to file
        with open(self.results_file, 'w') as f:
            # Custom JSON serializer for datetime objects
            def json_serialize(obj):
                if isinstance(obj, (datetime.datetime, datetime.date)):
                    return obj.isoformat()
                raise TypeError("Type not serializable")
            
            json.dump(results, f, default=json_serialize, indent=2)
        
        self.logger.info(f"Backtest completed: {total_trades} trades, {win_rate:.2f}% win rate, {percent_return:.2f}% return")
        self.logger.info(f"Results saved to {self.results_file}")
        
        print(f"Backtest completed successfully!")
        print(f"Final balance: ${end_balance:.2f} (${end_balance - start_balance:.2f} profit, {percent_return:.2f}%)")
        print(f"Total trades: {total_trades}, Win rate: {win_rate:.2f}%")
        print(f"Results saved to {self.results_file}")
        
        return True

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run hardcoded backtest")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--interval", type=str, default="1h", help="Candlestick interval")
    parser.add_argument("--start_date", type=str, default="2025-04-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, default="2025-04-10", help="End date (YYYY-MM-DD)")
    parser.add_argument("--initial_balance", type=float, default=10000, help="Initial balance")
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Convert dates
    try:
        start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError as e:
        logger.error(f"Invalid date format: {str(e)}")
        print(f"Error: Invalid date format. Use YYYY-MM-DD")
        return False
    
    # Create and run backtest
    backtest = Backtest(
        symbol=args.symbol,
        interval=args.interval,
        start_date=start_date,
        end_date=end_date,
        initial_balance=args.initial_balance
    )
    
    success = backtest.run()
    
    if not success:
        print(f"Backtest failed: {backtest.logger.handlers[0].baseFilename}")
        return False
    
    return True

if __name__ == "__main__":
    if not main():
        sys.exit(1)
EOF

# Upload to EC2
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no backtest_hardcoded.py "$SSH_USER@$EC2_IP:$EC2_DIR/backtest_hardcoded.py"

# Make executable
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/backtest_hardcoded.py"

# Create a simple run script on EC2
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cat > $EC2_DIR/run_backtest_hardcoded.sh << 'EOL'
#!/bin/bash
# Simple script to run the hardcoded backtest

cd \$(dirname \$0)
python3 backtest_hardcoded.py \"\$@\"
EOL"

# Make the script executable
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/run_backtest_hardcoded.sh"

# Clean up local file
rm backtest_hardcoded.py

# Step 4: Create a local run script
log "Step 4: Creating local run script..."

cat > ./backtest-hardcoded.sh << 'EOL'
#!/bin/bash
# Run script for the hardcoded backtesting script

# Set parameters
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Create key file if it doesn't exist
if [ ! -f "$KEY_PATH" ]; then
  echo "Creating EC2 key file..."
  cat > "$KEY_PATH" << 'KEYEOF'
-----BEGIN RSA PRIVATE KEY-----
MIIEoQIBAAKCAQEAyxNT6X+1frDllJPAbCAjOjNV6+IYbJTBJF+NNUESxrYsMK8J
1Dt4OBuXKSMV7nttmb6/jy6tItkztExoPyqr1QuKwHUInkbkKTm15Cl90o6yzXba
UfntOfpwZHwmEOJRVniLRJPzkOldOplyTiIxaf8mZKLeaXDlleaHZlNyrBWs9wNN
gJJbCBve2Z1TJsZeRig3u0Tg0+xo1BPxSm8dROalr8/30UrXpCkDQVL5S3oA2kSd
6hvwQhUZclGNheGgLOGTMtZ/FxGAI/mVsD29ErWnEoysLGCpbLfXpw7o3yEDCND+
cpqtV+ckbTeX2gqbugyZmBVrxcnbafwW1ykoaQIDAQABAoIBAE53gmXn1c5FNgBp
8uEUrefwLBQAAeX6uIKAdUSNh17Gx15sVATwkaxEZO0dRH0orhnJDaWaqIWdnY/e
Mi2uJEUmt49T6WeXBtQzG2g07Awu3UHs2cDxLEvJzCHXorHFcR5TZ6Sw8l0c/swE
vJkaNzO4xjH+iKf/WobIU6sjNVzuNjJF7TNUJ/kZmfZHOjOKCSBF/ahY+weeVBFp
lqaSKrNINPYoYn4nrAgWVxMiPqItWhm3Y9G3c3z9ePNJKRkNKnRB+pCfGS3EZTq0
deI3rcurPsBe34B/SxZF7G1hLVhEtom18YUbZvSBxgCJmI7D239e/Qz6bgqB7FAo
rFJ/S3ECgYEA+oCEP5NjBilqOHSdLLPhI/Ak6pNIK017xMBdiBTjnRh93D8Xzvfh
glkHRisZo8gmIZsgW3izlEeUv4CaVf7OzlOUiu2KmmrLxGHPoT+QPLf/Ak3GZE14
XY9vtaQQSwxM+i5sNtAD/3/KcjH6wT1B+8R4xqtHUYXw7VoEQWRSs/UCgYEAz4hW
j7+ooYlyHzkfuiEMJG0CtKR/fYsd9Zygn+Y6gGQvCiL+skAmx/ymG/qU6D8ZejkN
Azzv7JGQ+1z8OtTNStgDPE7IT74pA0BC60jHySDYzyGAaoMJDhHxA2CPm60EwPDU
5pRVy+FN5LmCCT8oDgcpsPpgjALOqR2TUkcOziUCgYAFXdN3eTTZ4PFBnF3xozjj
iDWCQP1+z/4izOw0Ch6GMwwfN8rOyEiwfi/FtQ6rj5Ihji03SHKwboglQiAMT5Um
nmvEPiqF/Fu5LU9BaRcx9c8kwX3KkE5P0s7V2VnwAad0hKIU2of7ZUV1BNUWZrWP
KzpbJzgz6uaqbw9AR2HuMQJ/YuaWWer8cf8OY9LVS95z6ugIYg4Cs9GYdXQvGASf
3I/h2vLSbiAkWyoL/0lrrUJk4dpOWTyxGgxFC4VErsS7EO/gmtzwmRAGe4YkXfxR
OYhtykgs6pWHuyzRrspVpdrOaSRcUYZfXMoCVP4S+lUewZCoTa8EU7UCx5VQn+U9
KQKBgQDsjVRcsfC/szL7KgeheEN/2zRADix5bqrg0rAB1y+sw+yzkCCh3jcRn2O2
wNIMroggGNy+vcR8Xo/V1wLCsEn45cxB6W7onqxFRM6IkGxkBgdatEL/aBnETSAI
x4C5J+IqaT2T53O2n3DR+GsVoeNUbz8j/lPONNQnV0ZqHRVWpA==
-----END RSA PRIVATE KEY-----
KEYEOF
  chmod 600 "$KEY_PATH"
fi

# Test the connection
echo "Testing connection to EC2 instance at $EC2_IP..."
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'"; then
  echo "Failed to connect to EC2 instance. Check your EC2_PUBLIC_IP variable."
  exit 1
fi

echo "Connection successful!"

# Parse command line arguments
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-04-01"
END_DATE="2025-04-10"
INITIAL_BALANCE="10000"

while [[ $# -gt 0 ]]; do
  case $1 in
    --symbol)
      SYMBOL="$2"
      shift 2
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --start)
      START_DATE="$2"
      shift 2
      ;;
    --end)
      END_DATE="$2"
      shift 2
      ;;
    --balance)
      INITIAL_BALANCE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "🚀 Running Hardcoded Backtest on EC2"
echo "==================================================="
echo "Parameters:"
echo "- Symbol: $SYMBOL"
echo "- Interval: $INTERVAL"
echo "- Date Range: $START_DATE to $END_DATE"
echo "- Initial Balance: $INITIAL_BALANCE"
echo ""

# Run the backtest on EC2
echo "Running backtest on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && ./run_backtest_hardcoded.sh --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $INITIAL_BALANCE"

# Get the latest result file from EC2
echo "Checking for results..."
LATEST_RESULT=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "ls -t $EC2_DIR/results/backtest_*.json 2>/dev/null | head -n 1")

if [ -n "$LATEST_RESULT" ]; then
  echo "Latest result file on EC2: $LATEST_RESULT"
  
  # Download the result file
  echo "Downloading result file from EC2..."
  mkdir -p ./results
  LOCAL_RESULT="./results/$(basename $LATEST_RESULT)"
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$LATEST_RESULT" "$LOCAL_RESULT"
  echo "Downloaded result file to: $LOCAL_RESULT"
fi

# Get the latest log file from EC2
LATEST_LOG=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "ls -t $EC2_DIR/logs/backtests/backtest_*.log 2>/dev/null | head -n 1")

if [ -n "$LATEST_LOG" ]; then
  echo "Latest log file on EC2: $LATEST_LOG"
  
  # Download the log file
  echo "Downloading log file from EC2..."
  mkdir -p ./logs/backtests
  LOCAL_LOG="./logs/backtests/$(basename $LATEST_LOG)"
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$LATEST_LOG" "$LOCAL_LOG"
  echo "Downloaded log file to: $LOCAL_LOG"
fi

echo "✅ Backtest process completed!"
EOL

chmod +x ./backtest-hardcoded.sh

log_info "✅ Local run script created."
log "The hardcoded backtest solution has been created. You can now run backtests with:"
log "   ./backtest-hardcoded.sh --symbol BTCUSDT --interval 1h --start 2025-04-01 --end 2025-04-10"
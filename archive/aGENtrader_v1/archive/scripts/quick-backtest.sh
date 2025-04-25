#!/bin/bash
# Quick backtest on EC2 with minimal disk usage

EC2_IP="51.20.250.135"
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

# Get parameters
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-20"
END_DATE="2025-03-22"
BALANCE="10000"

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
      BALANCE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Get database URL
DB_URL=$(node -e "console.log(process.env.DATABASE_URL || '')")
if [ -z "$DB_URL" ]; then
  echo "ERROR: DATABASE_URL environment variable is not set!"
  exit 1
fi

echo "🔍 Testing database access directly..."
echo "Creating temporary database test script..."
cat > test_db.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import psycopg2

def test_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL is not set")
        return False
    
    try:
        print(f"Connecting to database: {db_url[:10]}...{db_url[-10:]}")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("Connected! Testing query...")
        cursor.execute("SELECT COUNT(*) FROM market_data WHERE symbol=%s AND interval=%s", ("BTCUSDT", "1h"))
        count = cursor.fetchone()[0]
        print(f"Found {count} records for BTCUSDT 1h")
        
        # Get date range
        cursor.execute("""
            SELECT 
                MIN(timestamp) as start_date,
                MAX(timestamp) as end_date
            FROM market_data 
            WHERE symbol=%s AND interval=%s
        """, ("BTCUSDT", "1h"))
        
        start_date, end_date = cursor.fetchone()
        print(f"Date range: {start_date} to {end_date}")
        
        # Get sample data
        cursor.execute("""
            SELECT 
                timestamp, open, high, low, close, volume
            FROM market_data 
            WHERE symbol=%s AND interval=%s
            ORDER BY timestamp DESC
            LIMIT 3
        """, ("BTCUSDT", "1h"))
        
        print("\nSample data:")
        for row in cursor.fetchall():
            print(row)
        
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_db_connection()
EOF

echo "Uploading and testing database connection..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no test_db.py "$SSH_USER@$EC2_IP:/tmp/"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd /tmp && DATABASE_URL='$DB_URL' python3 test_db.py"

echo -e "\n🚀 Creating simplified backtest script..."
cat > simplified_backtest.py << 'EOF'
#!/usr/bin/env python3
"""
Simplified Backtest for Market Data Testing

This script runs a simplified backtest against the market_data table to verify
the data access and multi-agent framework integration.
"""
import os
import sys
import json
import logging
import argparse
import psycopg2
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simplified_backtest")

def get_market_data(symbol, interval, start_date, end_date):
    """Get market data from the database"""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable is not set")
        return None
    
    try:
        logger.info(f"Connecting to database: {db_url[:10]}...{db_url[-10:]}")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        logger.info(f"Fetching market data for {symbol} {interval} from {start_date} to {end_date}")
        cursor.execute("""
            SELECT 
                timestamp, open, high, low, close, volume
            FROM market_data 
            WHERE symbol=%s AND interval=%s
                AND timestamp >= %s
                AND timestamp <= %s
            ORDER BY timestamp
        """, (symbol, interval, start_date, end_date))
        
        rows = cursor.fetchall()
        logger.info(f"Retrieved {len(rows)} candles")
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            data.append({
                "timestamp": row[0].strftime("%Y-%m-%d %H:%M:%S"),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5])
            })
        
        conn.close()
        return data
    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
        return None

def run_simple_backtest(symbol, interval, start_date, end_date, initial_balance=10000):
    """Run a simple backtest using market data"""
    logger.info(f"Running backtest for {symbol} {interval} from {start_date} to {end_date}")
    
    # Get market data
    market_data = get_market_data(symbol, interval, start_date, end_date)
    if not market_data:
        logger.error("Failed to get market data")
        return None
    
    # Initialize backtest state
    balance = initial_balance
    position = 0  # 0 = cash, 1 = long
    entry_price = 0
    trades = []
    equity_curve = []
    
    # Record initial equity
    equity_curve.append({
        "timestamp": market_data[0]["timestamp"],
        "equity": balance,
        "price": market_data[0]["close"]
    })
    
    # Simple moving average strategy
    short_period = 5
    long_period = 20
    
    # Skip first 20 candles as we need enough data for moving averages
    for i in range(long_period, len(market_data)):
        # Calculate moving averages
        short_ma = sum(candle["close"] for candle in market_data[i-short_period:i]) / short_period
        long_ma = sum(candle["close"] for candle in market_data[i-long_period:i]) / long_period
        
        current_price = market_data[i]["close"]
        current_time = market_data[i]["timestamp"]
        
        # Calculate equity
        if position == 0:
            equity = balance
        else:
            # Calculate position value
            position_size = balance / entry_price
            equity = position_size * current_price
        
        # Record equity
        equity_curve.append({
            "timestamp": current_time,
            "equity": equity,
            "price": current_price
        })
        
        # Previous moving averages
        prev_short_ma = sum(candle["close"] for candle in market_data[i-short_period-1:i-1]) / short_period
        prev_long_ma = sum(candle["close"] for candle in market_data[i-long_period-1:i-1]) / long_period
        
        # Check for crossovers
        prev_short_above = prev_short_ma > prev_long_ma
        current_short_above = short_ma > long_ma
        
        # Trading logic
        if position == 0 and not prev_short_above and current_short_above:
            # Buy signal
            position = 1
            entry_price = current_price
            trades.append({
                "type": "BUY",
                "price": current_price,
                "timestamp": current_time,
                "balance": balance
            })
            logger.info(f"BUY at {current_price} ({current_time})")
        elif position == 1 and prev_short_above and not current_short_above:
            # Sell signal
            position_size = balance / entry_price
            new_balance = position_size * current_price
            pnl = (new_balance - balance) / balance * 100
            
            trades.append({
                "type": "SELL",
                "price": current_price,
                "timestamp": current_time,
                "entry_price": entry_price,
                "pnl_percentage": pnl,
                "old_balance": balance,
                "new_balance": new_balance
            })
            
            balance = new_balance
            position = 0
            logger.info(f"SELL at {current_price} ({current_time}), PnL: {pnl:.2f}%")
    
    # Close any open position at the end
    if position == 1:
        position_size = balance / entry_price
        new_balance = position_size * market_data[-1]["close"]
        pnl = (new_balance - balance) / balance * 100
        
        trades.append({
            "type": "SELL",
            "price": market_data[-1]["close"],
            "timestamp": market_data[-1]["timestamp"],
            "entry_price": entry_price,
            "pnl_percentage": pnl,
            "old_balance": balance,
            "new_balance": new_balance
        })
        
        balance = new_balance
        position = 0
        logger.info(f"Final SELL at {market_data[-1]['close']}, PnL: {pnl:.2f}%")
    
    # Calculate performance metrics
    total_pnl = (balance - initial_balance) / initial_balance * 100
    winning_trades = [t for t in trades if t.get("type") == "SELL" and t.get("pnl_percentage", 0) > 0]
    losing_trades = [t for t in trades if t.get("type") == "SELL" and t.get("pnl_percentage", 0) <= 0]
    win_rate = len(winning_trades) / max(1, len(winning_trades) + len(losing_trades)) * 100
    
    logger.info(f"Backtest completed: Balance ${balance:.2f}, PnL: {total_pnl:.2f}%")
    logger.info(f"Win rate: {win_rate:.2f}% ({len(winning_trades)}/{len(winning_trades) + len(losing_trades)})")
    
    # Compile results
    results = {
        "symbol": symbol,
        "interval": interval,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "initial_balance": initial_balance,
        "final_balance": balance,
        "total_pnl_percentage": total_pnl,
        "win_rate": win_rate,
        "total_trades": len(winning_trades) + len(losing_trades),
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "trades": trades,
        "equity_curve": equity_curve
    }
    
    # Save results
    os.makedirs("results", exist_ok=True)
    result_file = f"results/backtest_{symbol}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {result_file}")
    return results

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run a simplified backtest")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--interval", type=str, default="1h", help="Timeframe interval")
    parser.add_argument("--start_date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--initial_balance", type=float, default=10000.0, help="Initial balance")
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Parse dates
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        start_date = datetime.now() - timedelta(days=30)
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    else:
        end_date = datetime.now()
    
    # Run backtest
    result = run_simple_backtest(
        args.symbol,
        args.interval,
        start_date,
        end_date,
        args.initial_balance
    )
    
    if not result:
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF

echo "Uploading simplified backtest script..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no simplified_backtest.py "$SSH_USER@$EC2_IP:/tmp/"

echo -e "\n🚀 Running simplified backtest..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd /tmp && mkdir -p results && DATABASE_URL='$DB_URL' python3 simplified_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $BALANCE"

echo -e "\n📊 Downloading results..."
LATEST_RESULT=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "ls -t /tmp/results/backtest_*.json 2>/dev/null | head -n 1")

if [ -n "$LATEST_RESULT" ]; then
  echo "Latest result file on EC2: $LATEST_RESULT"
  
  # Download the result file
  echo "Downloading result file from EC2..."
  mkdir -p ./results
  LOCAL_RESULT="./results/$(basename $LATEST_RESULT)"
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$LATEST_RESULT" "$LOCAL_RESULT"
  echo "Downloaded result file to: $LOCAL_RESULT"
  
  # Display basic results
  echo -e "\n📈 BACKTEST SUMMARY"
  echo "===================="
  python3 -c "
import json
try:
    with open('$LOCAL_RESULT', 'r') as f:
        data = json.load(f)
    
    print(f\"Symbol: {data.get('symbol')}\")
    print(f\"Interval: {data.get('interval')}\")
    print(f\"Period: {data.get('start_date')} to {data.get('end_date')}\")
    print(f\"Initial Balance: ${data.get('initial_balance', 0):.2f}\")
    print(f\"Final Balance: ${data.get('final_balance', 0):.2f}\")
    print(f\"Total Return: {data.get('total_pnl_percentage', 0):.2f}%\")
    print(f\"Win Rate: {data.get('win_rate', 0):.2f}%\")
    print(f\"Total Trades: {data.get('total_trades', 0)}\")
    
    # Display last 3 trades
    trades = data.get('trades', [])
    if trades:
        print(f\"\\nLast 3 trades:\")
        for trade in trades[-3:]:
            if trade.get('type') == 'BUY':
                print(f\"  BUY at ${trade.get('price', 0):.2f} ({trade.get('timestamp')})\")
            else:
                print(f\"  SELL at ${trade.get('price', 0):.2f} ({trade.get('timestamp')}) - PnL: {trade.get('pnl_percentage', 0):.2f}%\")
except Exception as e:
    print(f\"Error reading results: {str(e)}\")
"
else
  echo "No results found on EC2"
fi

# Clean up
rm -f test_db.py simplified_backtest.py

echo -e "\n✅ Backtest completed!"
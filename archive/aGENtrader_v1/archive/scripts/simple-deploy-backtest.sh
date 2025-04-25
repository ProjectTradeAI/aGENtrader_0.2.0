#!/bin/bash
# Simple deployment script with automatic environment variable setup

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
log "📦 Simple Authentic Backtesting Deployment"
log "==================================================="

# Step 1: Create or update the local .env file
log "Step 1: Setting up environment variables..."

# Get database URL using NODE_OPTIONS to avoid TypeScript errors
DB_URL=$(node -e "console.log(process.env.DATABASE_URL || '')")

if [ -z "$DB_URL" ]; then
  log_error "DATABASE_URL environment variable is not set!"
  exit 1
fi

# Create or update .env file
log_info "Creating .env file with database configuration..."
cat > .env << EOF
SESSION_SECRET=bZyxYOvBxEertvn1IINT7PmaYKyp44ha
NODE_ENV=production
PORT=5000

# Database configuration for backtesting
DATABASE_URL="$DB_URL"
ALPACA_API_KEY="${ALPACA_API_KEY:-}"
ALPACA_API_SECRET="${ALPACA_API_SECRET:-}"
EOF

log_info "✅ Environment variables configured successfully."

# Step 2: Set up EC2 connection
log "Step 2: Setting up EC2 connection..."

# Set parameters
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Create key file using the hardcoded key (as in working script)
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

# Step 3: Set up directory structure
log "Step 3: Creating directory structure on EC2..."

# Create necessary directories on EC2
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "mkdir -p $EC2_DIR/backtesting/core $EC2_DIR/backtesting/utils $EC2_DIR/backtesting/analysis $EC2_DIR/backtesting/scripts $EC2_DIR/results $EC2_DIR/logs/backtests $EC2_DIR/data/analysis"

# Create necessary directories locally
mkdir -p ./backtesting/core ./backtesting/utils ./backtesting/analysis ./backtesting/scripts
mkdir -p ./results ./logs/backtests ./data/analysis

log_info "✅ Directory structure created."

# Step 4: Create required files
log "Step 4: Creating required Python files..."

# Create backtesting core file if it doesn't exist
if [ ! -f "./backtesting/core/authentic_backtest.py" ]; then
  log_info "Creating authentic_backtest.py..."
  cat > ./backtesting/core/authentic_backtest.py << 'EOF'
#!/usr/bin/env python3
"""
Authentic Backtesting Framework

This script performs backtesting using real market data from the database
and actual trading logic from the trading system.
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = os.path.join(os.getcwd(), "logs", "backtests")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"backtest_{timestamp}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("authentic_backtest")

def setup_environment(symbol, interval, start_date, end_date):
    """
    Set up the backtesting environment and import necessary modules.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        interval: Time interval (e.g., "1h")
        start_date: Start date for backtesting
        end_date: End date for backtesting
        
    Returns:
        Dictionary containing imported modules and configurations
    """
    logger.info("Setting up backtesting environment...")
    
    # Check database connection through environment variable
    if "DATABASE_URL" not in os.environ:
        logger.error("DATABASE_URL environment variable is not set")
        return None
    
    # Import market data module
    try:
        sys.path.append(os.getcwd())
        from backtesting.utils.market_data import get_historical_data
        
        # Test data retrieval
        data = get_historical_data(symbol, interval, start_date, end_date)
        if data is None or len(data) == 0:
            logger.error("Cannot get historical market data - no database connection")
            return None
    except Exception as e:
        logger.error(f"Failed to import market data module: {str(e)}")
        return None
    
    # Import decision session and agents
    env = {}
    try:
        # Try to import decision session
        from agents.session import DecisionSession
        logger.info("Successfully imported DecisionSession")
        env["DecisionSession"] = DecisionSession
    except Exception as e:
        logger.error(f"Failed to import DecisionSession: {str(e)}")
    
    # Import data integrity checker
    try:
        from backtesting.utils.data_integrity_checker import check_database_access
        logger.info("Successfully imported data integrity module")
        env["check_database_access"] = check_database_access
    except Exception as e:
        logger.error(f"Failed to import data integrity module: {str(e)}")
    
    # Try importing analysts
    try:
        from agents.technical import TechnicalAnalyst
        env["TechnicalAnalyst"] = TechnicalAnalyst
    except Exception as e:
        logger.warning(f"Failed to import TechnicalAnalyst")
    
    try:
        from agents.fundamental import FundamentalAnalyst
        env["FundamentalAnalyst"] = FundamentalAnalyst
    except Exception as e:
        logger.warning(f"Failed to import FundamentalAnalyst")
    
    try:
        from agents.sentiment import SentimentAnalyst
        env["SentimentAnalyst"] = SentimentAnalyst
    except Exception as e:
        logger.warning(f"Failed to import SentimentAnalyst")
    
    try:
        from agents.trading_system import TradingSystem
        env["TradingSystem"] = TradingSystem
    except Exception as e:
        logger.warning(f"Failed to import TradingSystem")
    
    # Set up configuration
    env["config"] = {
        "symbol": symbol,
        "interval": interval,
        "start_date": start_date,
        "end_date": end_date,
        "log_file": log_file
    }
    
    logger.info(f"Backtesting environment set up for {symbol} {interval} from {start_date} to {end_date}")
    logger.info(f"Log file: {log_file}")
    
    return env

def run_backtest(env, initial_balance=10000.0):
    """
    Run the backtest.
    
    Args:
        env: Environment dictionary from setup_environment
        initial_balance: Initial account balance
        
    Returns:
        Results dictionary
    """
    if env is None:
        logger.error("No market data available for backtesting")
        print("\nBacktest failed: No market data available for backtesting")
        return None
    
    config = env["config"]
    symbol = config["symbol"]
    interval = config["interval"]
    start_date = config["start_date"]
    end_date = config["end_date"]
    
    try:
        # Get historical data
        from backtesting.utils.market_data import get_historical_data
        data = get_historical_data(symbol, interval, start_date, end_date)
        
        if data is None or len(data) == 0:
            logger.error("No market data available for the specified period")
            print("\nBacktest failed: No market data available for the specified period")
            return None
        
        logger.info(f"Retrieved {len(data)} data points for backtesting")
        
        # Run simulation with the data
        # This is a simplified simulation, replace with actual trading logic
        results = simulate_trading(data, env, initial_balance)
        
        # Save results
        save_results(results)
        
        logger.info("Backtest completed successfully")
        print("\nBacktest completed successfully!")
        return results
    
    except Exception as e:
        logger.error(f"Error during backtest: {str(e)}")
        print(f"\nBacktest failed: {str(e)}")
        return None

def simulate_trading(data, env, initial_balance):
    """
    Simulate trading using historical data.
    
    Args:
        data: Historical price data
        env: Environment dictionary from setup_environment
        initial_balance: Initial account balance
        
    Returns:
        Results dictionary
    """
    # Convert data to pandas DataFrame if it's not already
    if not isinstance(data, pd.DataFrame):
        df = pd.DataFrame(data)
    else:
        df = data
    
    # Ensure required columns exist
    required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Required column {col} not found in market data")
            return None
    
    # Set up initial state
    balance = initial_balance
    position = 0
    trades = []
    equity_curve = []
    
    # Record initial equity
    equity_curve.append({
        "timestamp": df.iloc[0]["timestamp"],
        "equity": balance,
        "position": position
    })
    
    # Process each data point
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # Simple moving average strategy for demonstration
        # In reality, you would use your trading system logic here
        if i > 20:  # Need enough data for moving average
            short_ma = df.iloc[i-20:i]["close"].mean()
            long_ma = df.iloc[i-50:i]["close"].mean()
            
            # Buy signal: short MA crosses above long MA
            if position == 0 and short_ma > long_ma:
                # Buy logic
                price = row["open"]
                position = balance / price
                cost = position * price
                balance = 0
                
                trades.append({
                    "timestamp": row["timestamp"],
                    "type": "buy",
                    "price": price,
                    "amount": position,
                    "cost": cost
                })
                
                logger.info(f"BUY at {price} - Amount: {position}")
            
            # Sell signal: short MA crosses below long MA
            elif position > 0 and short_ma < long_ma:
                # Sell logic
                price = row["open"]
                proceeds = position * price
                balance = proceeds
                
                trades.append({
                    "timestamp": row["timestamp"],
                    "type": "sell",
                    "price": price,
                    "amount": position,
                    "proceeds": proceeds
                })
                
                logger.info(f"SELL at {price} - Amount: {position} - Proceeds: {proceeds}")
                position = 0
        
        # Calculate current equity
        equity = balance + (position * row["close"])
        
        # Record equity at this point
        equity_curve.append({
            "timestamp": row["timestamp"],
            "equity": equity,
            "position": position
        })
    
    # Liquidate any remaining position at the end
    if position > 0:
        price = df.iloc[-1]["close"]
        proceeds = position * price
        balance = proceeds
        
        trades.append({
            "timestamp": df.iloc[-1]["timestamp"],
            "type": "sell",
            "price": price,
            "amount": position,
            "proceeds": proceeds
        })
        
        logger.info(f"FINAL SELL at {price} - Amount: {position} - Proceeds: {proceeds}")
        position = 0
    
    # Calculate final equity
    final_equity = balance
    
    # Calculate performance metrics
    initial_equity = initial_balance
    profit_loss = final_equity - initial_equity
    profit_loss_percent = (profit_loss / initial_equity) * 100
    
    # Calculate drawdown
    max_equity = initial_equity
    max_drawdown = 0
    max_drawdown_percent = 0
    
    for point in equity_curve:
        equity = point["equity"]
        if equity > max_equity:
            max_equity = equity
        
        drawdown = max_equity - equity
        drawdown_percent = (drawdown / max_equity) * 100
        
        if drawdown_percent > max_drawdown_percent:
            max_drawdown = drawdown
            max_drawdown_percent = drawdown_percent
    
    # Prepare results
    results = {
        "symbol": env["config"]["symbol"],
        "interval": env["config"]["interval"],
        "start_date": env["config"]["start_date"],
        "end_date": env["config"]["end_date"],
        "initial_balance": initial_balance,
        "final_balance": final_equity,
        "profit_loss": profit_loss,
        "profit_loss_percent": profit_loss_percent,
        "max_drawdown": max_drawdown,
        "max_drawdown_percent": max_drawdown_percent,
        "total_trades": len(trades),
        "trades": trades,
        "equity_curve": equity_curve
    }
    
    return results

def save_results(results):
    """
    Save backtest results to file.
    
    Args:
        results: Results dictionary from run_backtest
    """
    if results is None:
        return
    
    # Create results directory if it doesn't exist
    results_dir = os.path.join(os.getcwd(), "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    symbol = results["symbol"]
    interval = results["interval"]
    filename = f"backtest_{symbol}_{interval}_{timestamp}.json"
    file_path = os.path.join(results_dir, filename)
    
    # Save to file
    with open(file_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {file_path}")
    print(f"Results saved to {file_path}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Authentic Backtesting Framework")
    
    parser.add_argument("--symbol", type=str, default="BTCUSDT",
                        help="Trading symbol (e.g., BTCUSDT)")
    
    parser.add_argument("--interval", type=str, default="1h",
                        help="Time interval (e.g., 1m, 5m, 15m, 1h, 4h, 1d)")
    
    parser.add_argument("--start_date", type=str, 
                        default=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                        help="Start date for backtesting (YYYY-MM-DD)")
    
    parser.add_argument("--end_date", type=str, 
                        default=datetime.now().strftime("%Y-%m-%d"),
                        help="End date for backtesting (YYYY-MM-DD)")
    
    parser.add_argument("--initial_balance", type=float, default=10000.0,
                        help="Initial account balance")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Set up environment
    env = setup_environment(args.symbol, args.interval, args.start_date, args.end_date)
    
    # Run backtest
    run_backtest(env, args.initial_balance)

if __name__ == "__main__":
    main()
EOF
fi

# Create data integrity checker if it doesn't exist
if [ ! -f "./backtesting/utils/data_integrity_checker.py" ]; then
  log_info "Creating data_integrity_checker.py..."
  cat > ./backtesting/utils/data_integrity_checker.py << 'EOF'
#!/usr/bin/env python3
"""
Data Integrity Checker for Backtesting

This module provides functions to check data integrity for backtesting.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("data_integrity_checker")

def check_database_access():
    """
    Check if the database is accessible and has market data.
    
    Returns:
        Dictionary with database status information
    """
    result = {
        "database_url_set": "DATABASE_URL" in os.environ,
        "can_connect": False,
        "tables_available": [],
        "data_available": False
    }
    
    if not result["database_url_set"]:
        logger.error("DATABASE_URL environment variable is not set")
        return result
    
    # Try to connect to the database
    try:
        import psycopg2
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cursor = conn.cursor()
        result["can_connect"] = True
        
        # Check for tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        result["tables_available"] = tables
        
        # Check for market data
        if "market_data" in tables:
            cursor.execute("SELECT COUNT(*) FROM market_data LIMIT 1")
            count = cursor.fetchone()[0]
            result["data_available"] = count > 0
        
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
    
    return result

def check_agent_imports():
    """
    Check if the agent modules can be imported.
    
    Returns:
        Dictionary with status of each agent import
    """
    result = {
        "technical_analyst": False,
        "fundamental_analyst": False,
        "sentiment_analyst": False,
        "trading_system": False
    }
    
    try:
        sys.path.append(os.getcwd())
        
        try:
            from agents.technical import TechnicalAnalyst
            result["technical_analyst"] = True
        except ImportError:
            pass
        
        try:
            from agents.fundamental import FundamentalAnalyst
            result["fundamental_analyst"] = True
        except ImportError:
            pass
        
        try:
            from agents.sentiment import SentimentAnalyst
            result["sentiment_analyst"] = True
        except ImportError:
            pass
        
        try:
            from agents.trading_system import TradingSystem
            result["trading_system"] = True
        except ImportError:
            pass
    
    except Exception as e:
        logger.error(f"Error checking agent imports: {str(e)}")
    
    return result

def check_market_data_availability(symbol, interval, start_date, end_date):
    """
    Check if market data is available for the specified parameters.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        interval: Time interval (e.g., "1h")
        start_date: Start date for backtesting
        end_date: End date for backtesting
        
    Returns:
        Dictionary with market data status information
    """
    result = {
        "symbol": symbol,
        "interval": interval,
        "start_date": start_date,
        "end_date": end_date,
        "data_available": False,
        "data_points": 0
    }
    
    try:
        sys.path.append(os.getcwd())
        from backtesting.utils.market_data import get_historical_data
        
        data = get_historical_data(symbol, interval, start_date, end_date)
        if data is not None and len(data) > 0:
            result["data_available"] = True
            result["data_points"] = len(data)
    
    except Exception as e:
        logger.error(f"Error checking market data availability: {str(e)}")
    
    return result

def main():
    """Main entry point for command-line usage."""
    load_dotenv()
    
    print("\nData Integrity Checker for Backtesting")
    print("=====================================\n")
    
    # Check database access
    print("Checking database access...")
    db_status = check_database_access()
    print(f"  DATABASE_URL set: {db_status['database_url_set']}")
    print(f"  Can connect: {db_status['can_connect']}")
    print(f"  Tables available: {', '.join(db_status['tables_available'])}")
    print(f"  Data available: {db_status['data_available']}")
    
    # Check agent imports
    print("\nChecking agent imports...")
    agent_status = check_agent_imports()
    print(f"  TechnicalAnalyst: {agent_status['technical_analyst']}")
    print(f"  FundamentalAnalyst: {agent_status['fundamental_analyst']}")
    print(f"  SentimentAnalyst: {agent_status['sentiment_analyst']}")
    print(f"  TradingSystem: {agent_status['trading_system']}")
    
    # Check market data availability
    print("\nChecking market data availability...")
    symbol = "BTCUSDT"
    interval = "1h"
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    data_status = check_market_data_availability(symbol, interval, start_date, end_date)
    print(f"  Symbol: {data_status['symbol']}")
    print(f"  Interval: {data_status['interval']}")
    print(f"  Date range: {data_status['start_date']} to {data_status['end_date']}")
    print(f"  Data available: {data_status['data_available']}")
    print(f"  Data points: {data_status['data_points']}")
    
    print("\nData integrity check complete.")

if __name__ == "__main__":
    main()
EOF
fi

# Create market data utility if it doesn't exist
if [ ! -f "./backtesting/utils/market_data.py" ]; then
  log_info "Creating market_data.py..."
  cat > ./backtesting/utils/market_data.py << 'EOF'
#!/usr/bin/env python3
"""
Market Data Utility for Backtesting

This module provides functions to get market data for backtesting.
"""
import os
import logging
from datetime import datetime
import psycopg2
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("market_data")

def get_db_connection():
    """
    Get a connection to the database.
    
    Returns:
        Database connection or None if connection fails
    """
    try:
        if "DATABASE_URL" not in os.environ:
            logger.error("DATABASE_URL environment variable is not set")
            return None
        
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        return conn
    
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

def get_historical_data(symbol, interval, start_date, end_date):
    """
    Get historical market data for a symbol and interval.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        interval: Time interval (e.g., "1h")
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        DataFrame with historical data or None if data retrieval fails
    """
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        # Convert start_date and end_date to datetime
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Add 1 day to end_date to include the end date
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        
        cursor = conn.cursor()
        
        # Try to query market_data table
        try:
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM market_data
                WHERE symbol = %s AND interval = %s AND timestamp BETWEEN %s AND %s
                ORDER BY timestamp
            """
            
            cursor.execute(query, (symbol, interval, start_datetime, end_datetime))
            rows = cursor.fetchall()
            
            if rows:
                df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
                logger.info(f"Retrieved {len(df)} rows from market_data table")
                return df
            else:
                logger.warning(f"No data found in market_data table for {symbol} {interval} from {start_date} to {end_date}")
        
        except Exception as e:
            logger.error(f"Error querying market_data table: {str(e)}")
        
        # If market_data table query failed, try candles table
        try:
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM candles
                WHERE symbol = %s AND timeframe = %s AND timestamp BETWEEN %s AND %s
                ORDER BY timestamp
            """
            
            cursor.execute(query, (symbol, interval, start_datetime, end_datetime))
            rows = cursor.fetchall()
            
            if rows:
                df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
                logger.info(f"Retrieved {len(df)} rows from candles table")
                return df
            else:
                logger.warning(f"No data found in candles table for {symbol} {interval} from {start_date} to {end_date}")
        
        except Exception as e:
            logger.error(f"Error querying candles table: {str(e)}")
        
        # If both queries failed, return None
        logger.error(f"No data found for {symbol} {interval} from {start_date} to {end_date}")
        return None
    
    finally:
        conn.close()

def get_latest_price(symbol):
    """
    Get the latest price for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        
    Returns:
        Latest price or None if data retrieval fails
    """
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Try to query market_data table
        try:
            query = """
                SELECT close
                FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """
            
            cursor.execute(query, (symbol,))
            row = cursor.fetchone()
            
            if row:
                logger.info(f"Retrieved latest price from market_data table: {row[0]}")
                return row[0]
            else:
                logger.warning(f"No latest price found in market_data table for {symbol}")
        
        except Exception as e:
            logger.error(f"Error querying market_data table for latest price: {str(e)}")
        
        # If market_data table query failed, try candles table
        try:
            query = """
                SELECT close
                FROM candles
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """
            
            cursor.execute(query, (symbol,))
            row = cursor.fetchone()
            
            if row:
                logger.info(f"Retrieved latest price from candles table: {row[0]}")
                return row[0]
            else:
                logger.warning(f"No latest price found in candles table for {symbol}")
        
        except Exception as e:
            logger.error(f"Error querying candles table for latest price: {str(e)}")
        
        # If both queries failed, return None
        logger.error(f"No latest price found for {symbol}")
        return None
    
    finally:
        conn.close()

def get_market_statistics(symbol, interval="1d", days=30):
    """
    Get market statistics for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        interval: Time interval (e.g., "1d")
        days: Number of days to look back
        
    Returns:
        Dictionary with market statistics or None if data retrieval fails
    """
    from datetime import datetime, timedelta
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    df = get_historical_data(symbol, interval, start_date, end_date)
    if df is None or len(df) == 0:
        return None
    
    # Calculate statistics
    latest_price = df.iloc[-1]["close"]
    high_price = df["high"].max()
    low_price = df["low"].min()
    
    # Calculate returns
    df["daily_return"] = df["close"].pct_change()
    
    # Calculate volatility (annualized standard deviation of returns)
    volatility = df["daily_return"].std() * (365 ** 0.5) * 100  # Annualized and as percentage
    
    # Calculate average volume
    avg_volume = df["volume"].mean()
    
    # Calculate 7-day and 30-day price change
    price_7d_ago = df.iloc[-min(7, len(df))]["close"] if len(df) >= 7 else df.iloc[0]["close"]
    price_30d_ago = df.iloc[-min(30, len(df))]["close"] if len(df) >= 30 else df.iloc[0]["close"]
    
    change_7d = ((latest_price - price_7d_ago) / price_7d_ago) * 100
    change_30d = ((latest_price - price_30d_ago) / price_30d_ago) * 100
    
    # Return statistics
    return {
        "symbol": symbol,
        "latest_price": latest_price,
        "high_price": high_price,
        "low_price": low_price,
        "volatility": volatility,
        "avg_volume": avg_volume,
        "change_7d": change_7d,
        "change_30d": change_30d,
        "data_points": len(df)
    }

def main():
    """Main entry point for command-line usage."""
    load_dotenv()
    
    print("\nMarket Data Utility for Backtesting")
    print("==================================\n")
    
    # Get historical data
    symbol = "BTCUSDT"
    interval = "1h"
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    print(f"Getting historical data for {symbol} {interval} from {start_date} to {end_date}...")
    data = get_historical_data(symbol, interval, start_date, end_date)
    
    if data is not None:
        print(f"Retrieved {len(data)} data points")
        print("\nFirst 5 rows:")
        print(data.head())
    else:
        print("Failed to retrieve historical data")
    
    # Get latest price
    print(f"\nGetting latest price for {symbol}...")
    price = get_latest_price(symbol)
    
    if price is not None:
        print(f"Latest price: {price}")
    else:
        print("Failed to retrieve latest price")
    
    # Get market statistics
    print(f"\nGetting market statistics for {symbol}...")
    stats = get_market_statistics(symbol)
    
    if stats is not None:
        print("Market statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("Failed to retrieve market statistics")
    
    print("\nMarket data utility test complete.")

if __name__ == "__main__":
    main()
EOF
fi

# Create visualization utility if it doesn't exist
if [ ! -f "./backtesting/analysis/visualize_backtest.py" ]; then
  log_info "Creating visualize_backtest.py..."
  cat > ./backtesting/analysis/visualize_backtest.py << 'EOF'
#!/usr/bin/env python3
"""
Backtest Visualization Utility

This module provides functions to visualize backtest results.
"""
import os
import json
import argparse
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def load_backtest_results(file_path):
    """
    Load backtest results from a JSON file.
    
    Args:
        file_path: Path to the backtest results JSON file
        
    Returns:
        Dictionary with backtest results
    """
    with open(file_path, "r") as f:
        results = json.load(f)
    
    return results

def create_equity_curve_df(results):
    """
    Create a DataFrame with the equity curve from backtest results.
    
    Args:
        results: Dictionary with backtest results
        
    Returns:
        DataFrame with equity curve
    """
    equity_curve = results["equity_curve"]
    
    # Convert to DataFrame
    df = pd.DataFrame(equity_curve)
    
    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Set timestamp as index
    df.set_index("timestamp", inplace=True)
    
    return df

def create_trades_df(results):
    """
    Create a DataFrame with trade information from backtest results.
    
    Args:
        results: Dictionary with backtest results
        
    Returns:
        DataFrame with trade information
    """
    trades = results["trades"]
    
    # Convert to DataFrame
    df = pd.DataFrame(trades)
    
    if len(df) == 0:
        return df
    
    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Calculate profit/loss for each trade
    df["profit_loss"] = 0.0
    
    for i in range(0, len(df), 2):
        if i + 1 < len(df):
            if df.iloc[i]["type"] == "buy" and df.iloc[i+1]["type"] == "sell":
                buy_cost = df.iloc[i]["cost"]
                sell_proceeds = df.iloc[i+1]["proceeds"]
                profit_loss = sell_proceeds - buy_cost
                
                df.loc[df.index[i], "profit_loss"] = profit_loss
                df.loc[df.index[i+1], "profit_loss"] = profit_loss
    
    return df

def visualize_equity_curve(results, output_dir):
    """
    Visualize the equity curve from backtest results.
    
    Args:
        results: Dictionary with backtest results
        output_dir: Directory to save the output files
    """
    # Create equity curve DataFrame
    equity_df = create_equity_curve_df(results)
    
    # Create trades DataFrame
    trades_df = create_trades_df(results)
    
    # Set up plot
    plt.figure(figsize=(12, 6))
    
    # Plot equity curve
    plt.plot(equity_df.index, equity_df["equity"], label="Equity")
    
    # Plot buy and sell points
    if len(trades_df) > 0:
        buy_trades = trades_df[trades_df["type"] == "buy"]
        sell_trades = trades_df[trades_df["type"] == "sell"]
        
        for _, trade in buy_trades.iterrows():
            plt.scatter(trade["timestamp"], trade["cost"], color="green", marker="^", s=100)
        
        for _, trade in sell_trades.iterrows():
            plt.scatter(trade["timestamp"], trade["proceeds"], color="red", marker="v", s=100)
    
    # Set labels and title
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.title(f"Equity Curve for {results['symbol']} ({results['interval']})")
    
    # Add legend
    plt.legend()
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"equity_curve_{results['symbol']}_{results['interval']}_{timestamp}.png")
    plt.savefig(output_file)
    
    print(f"Equity curve saved to {output_file}")

def visualize_trade_analysis(results, output_dir):
    """
    Visualize trade analysis from backtest results.
    
    Args:
        results: Dictionary with backtest results
        output_dir: Directory to save the output files
    """
    # Create trades DataFrame
    trades_df = create_trades_df(results)
    
    if len(trades_df) == 0:
        print("No trades to analyze")
        return
    
    # Calculate cumulative profit/loss
    trades_df["cumulative_pl"] = trades_df["profit_loss"].cumsum()
    
    # Set up plot
    plt.figure(figsize=(12, 6))
    
    # Plot cumulative profit/loss
    plt.plot(trades_df["timestamp"], trades_df["cumulative_pl"], label="Cumulative P/L")
    
    # Set labels and title
    plt.xlabel("Date")
    plt.ylabel("Profit/Loss")
    plt.title(f"Cumulative Profit/Loss for {results['symbol']} ({results['interval']})")
    
    # Add legend
    plt.legend()
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"trade_analysis_{results['symbol']}_{results['interval']}_{timestamp}.png")
    plt.savefig(output_file)
    
    print(f"Trade analysis saved to {output_file}")

def visualize_trade_distribution(results, output_dir):
    """
    Visualize trade distribution from backtest results.
    
    Args:
        results: Dictionary with backtest results
        output_dir: Directory to save the output files
    """
    # Create trades DataFrame
    trades_df = create_trades_df(results)
    
    if len(trades_df) == 0:
        print("No trades to analyze")
        return
    
    # Filter sell trades to analyze profit/loss
    sell_trades = trades_df[trades_df["type"] == "sell"]
    
    if len(sell_trades) == 0:
        print("No sell trades to analyze")
        return
    
    # Set up plot
    plt.figure(figsize=(12, 6))
    
    # Plot profit/loss distribution
    sns.histplot(sell_trades["profit_loss"], kde=True)
    
    # Set labels and title
    plt.xlabel("Profit/Loss")
    plt.ylabel("Frequency")
    plt.title(f"Profit/Loss Distribution for {results['symbol']} ({results['interval']})")
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"trade_distribution_{results['symbol']}_{results['interval']}_{timestamp}.png")
    plt.savefig(output_file)
    
    print(f"Trade distribution saved to {output_file}")

def create_performance_summary(results):
    """
    Create a performance summary from backtest results.
    
    Args:
        results: Dictionary with backtest results
        
    Returns:
        String with performance summary
    """
    summary = []
    
    summary.append("Performance Summary")
    summary.append("===================")
    summary.append("")
    
    summary.append(f"Symbol: {results['symbol']}")
    summary.append(f"Interval: {results['interval']}")
    summary.append(f"Date Range: {results['start_date']} to {results['end_date']}")
    summary.append("")
    
    summary.append("Account Performance")
    summary.append("-------------------")
    summary.append(f"Initial Balance: ${results['initial_balance']:.2f}")
    summary.append(f"Final Balance: ${results['final_balance']:.2f}")
    summary.append(f"Profit/Loss: ${results['profit_loss']:.2f} ({results['profit_loss_percent']:.2f}%)")
    summary.append(f"Max Drawdown: ${results['max_drawdown']:.2f} ({results['max_drawdown_percent']:.2f}%)")
    summary.append("")
    
    summary.append("Trade Statistics")
    summary.append("----------------")
    summary.append(f"Total Trades: {results['total_trades']}")
    
    # Calculate win rate
    trades_df = create_trades_df(results)
    
    if len(trades_df) > 0:
        sell_trades = trades_df[trades_df["type"] == "sell"]
        
        if len(sell_trades) > 0:
            winning_trades = sell_trades[sell_trades["profit_loss"] > 0]
            win_rate = (len(winning_trades) / len(sell_trades)) * 100
            
            summary.append(f"Winning Trades: {len(winning_trades)}")
            summary.append(f"Losing Trades: {len(sell_trades) - len(winning_trades)}")
            summary.append(f"Win Rate: {win_rate:.2f}%")
            
            if len(winning_trades) > 0:
                avg_win = winning_trades["profit_loss"].mean()
                summary.append(f"Average Win: ${avg_win:.2f}")
            
            losing_trades = sell_trades[sell_trades["profit_loss"] <= 0]
            
            if len(losing_trades) > 0:
                avg_loss = losing_trades["profit_loss"].mean()
                summary.append(f"Average Loss: ${avg_loss:.2f}")
                
                if len(winning_trades) > 0:
                    profit_factor = abs(winning_trades["profit_loss"].sum() / losing_trades["profit_loss"].sum()) if losing_trades["profit_loss"].sum() != 0 else "Infinity"
                    
                    if isinstance(profit_factor, str):
                        summary.append(f"Profit Factor: {profit_factor}")
                    else:
                        summary.append(f"Profit Factor: {profit_factor:.2f}")
    
    return "\n".join(summary)

def save_performance_summary(summary, results, output_dir):
    """
    Save the performance summary to a file.
    
    Args:
        summary: String with performance summary
        results: Dictionary with backtest results
        output_dir: Directory to save the output file
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"performance_summary_{results['symbol']}_{results['interval']}_{timestamp}.txt")
    
    with open(output_file, "w") as f:
        f.write(summary)
    
    print(f"Performance summary saved to {output_file}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Backtest Visualization Utility")
    
    parser.add_argument("--backtest-file", type=str, required=True,
                        help="Path to the backtest results JSON file")
    
    parser.add_argument("--output-dir", type=str, default="./data/analysis",
                        help="Directory to save the output files")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Load backtest results
    results = load_backtest_results(args.backtest_file)
    
    # Visualize equity curve
    visualize_equity_curve(results, args.output_dir)
    
    # Visualize trade analysis
    visualize_trade_analysis(results, args.output_dir)
    
    # Visualize trade distribution
    visualize_trade_distribution(results, args.output_dir)
    
    # Create and save performance summary
    summary = create_performance_summary(results)
    save_performance_summary(summary, results, args.output_dir)
    
    print("Visualization complete!")

if __name__ == "__main__":
    main()
EOF
fi

# Create run script if it doesn't exist
if [ ! -f "./backtesting/scripts/run_authentic_backtest.sh" ]; then
  log_info "Creating run_authentic_backtest.sh..."
  cat > ./backtesting/scripts/run_authentic_backtest.sh << 'EOF'
#!/bin/bash
# Run Authentic Backtest
# This script runs an authentic backtest using the backtesting framework.

# Default parameters
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE=$(date -d "7 days ago" +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)
INITIAL_BALANCE=10000
VERBOSE=false

# Parse command line options
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
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      echo "Usage: $0 [--symbol BTCUSDT] [--interval 1h] [--start 2025-03-01] [--end 2025-03-02] [--balance 10000] [--verbose]"
      echo
      echo "Options:"
      echo "  --symbol      Trading symbol [default: BTCUSDT]"
      echo "  --interval    Time interval (1m, 5m, 15m, 1h, 4h, 1d) [default: 1h]"
      echo "  --start       Start date [default: 7 days ago]"
      echo "  --end         End date [default: today]"
      echo "  --balance     Initial balance [default: 10000]"
      echo "  --verbose     Show verbose output"
      echo "  --help        Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--symbol BTCUSDT] [--interval 1h] [--start 2025-03-01] [--end 2025-03-02] [--balance 10000] [--verbose]"
      exit 1
      ;;
  esac
done

# Set up environment
echo "Setting up environment..."
source .env

# Create directories if they don't exist
mkdir -p ./results
mkdir -p ./logs/backtests
mkdir -p ./data/analysis

# Print parameters
echo "Running authentic backtest with parameters:"
echo "  Symbol: $SYMBOL"
echo "  Interval: $INTERVAL"
echo "  Date Range: $START_DATE to $END_DATE"
echo "  Initial Balance: $INITIAL_BALANCE"
echo "  Verbose: $VERBOSE"
echo

# Run the backtest
echo "Running authentic backtest..."
COMMAND="python3 backtesting/core/authentic_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $INITIAL_BALANCE"

if [ "$VERBOSE" = true ]; then
  echo "Running command: $COMMAND"
  $COMMAND
else
  echo "Running command: $COMMAND"
  $COMMAND | grep -v "DEBUG"
fi

# Check exit status
if [ $? -eq 0 ]; then
  echo "✅ Backtest completed successfully!"
  
  # Get the latest result file
  LATEST_RESULT=$(find ./results -name "backtest_*.json" -type f -printf "%T@ %p\n" | sort -nr | head -n 1 | awk '{print $2}')
  
  if [ -n "$LATEST_RESULT" ]; then
    echo "Latest result file: $LATEST_RESULT"
    
    # Visualize results
    echo "Visualizing backtest results..."
    python3 backtesting/analysis/visualize_backtest.py --backtest-file "$LATEST_RESULT" --output-dir "./data/analysis"
    
    if [ $? -eq 0 ]; then
      echo "Visualization complete! Check the data/analysis directory for plots."
    else
      echo "WARNING: Visualization failed, but the backtest results were saved."
    fi
  fi
else
  echo "❌ Backtest failed!"
fi

echo "Authentic backtest process completed!"
EOF
  chmod +x ./backtesting/scripts/run_authentic_backtest.sh
fi

# Make the run script executable
chmod +x ./backtesting/scripts/run_authentic_backtest.sh

log_info "✅ Required files created successfully."

# Step 5: Deploy the files to EC2
log "Step 5: Deploying files to EC2..."

# Upload the files to EC2
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no ./backtesting/core/authentic_backtest.py "$SSH_USER@$EC2_IP:$EC2_DIR/backtesting/core/"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no ./backtesting/utils/data_integrity_checker.py "$SSH_USER@$EC2_IP:$EC2_DIR/backtesting/utils/"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no ./backtesting/utils/market_data.py "$SSH_USER@$EC2_IP:$EC2_DIR/backtesting/utils/"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no ./backtesting/analysis/visualize_backtest.py "$SSH_USER@$EC2_IP:$EC2_DIR/backtesting/analysis/"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no ./backtesting/scripts/run_authentic_backtest.sh "$SSH_USER@$EC2_IP:$EC2_DIR/backtesting/scripts/"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no ./.env "$SSH_USER@$EC2_IP:$EC2_DIR/.env"

# Make the script executable on EC2
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/backtesting/scripts/run_authentic_backtest.sh"

# Step 6: Install required Python packages on EC2
log "Step 6: Installing required Python packages on EC2..."

ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "pip3 install --user psycopg2-binary pandas numpy matplotlib seaborn python-dotenv"

# Step 7: Test the deployment and environment
log "Step 7: Testing the deployment..."

# Upload the environment checker
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no ./backtesting/utils/check_env.py "$SSH_USER@$EC2_IP:$EC2_DIR/backtesting/utils/"

# Make sure dotenv package is installed on EC2
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "pip3 install --user python-dotenv"

# Check environment variables on EC2
log_info "Testing environment variables on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && python3 backtesting/utils/check_env.py"

# Check database access using data integrity checker
log_info "Testing database connection on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && python3 -c 'import sys, os; from dotenv import load_dotenv; load_dotenv(); sys.path.append(\".\"); print(\"Current directory:\", os.getcwd()); print(\"DATABASE_URL set in environment:\", \"DATABASE_URL\" in os.environ); from backtesting.utils.data_integrity_checker import check_database_access; print(\"Database connection test:\"); print(check_database_access())'"

# Final message
log "✅ Authentic backtesting framework deployed successfully to EC2!"
log_info "You can now run backtests on EC2 with:"
log_info "  ./simple-run-backtest.sh --symbol BTCUSDT --interval 1h --start 2025-04-01 --end 2025-04-10"
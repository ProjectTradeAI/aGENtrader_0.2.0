#!/bin/bash
# Script to create a market data adapter for authentic backtesting

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
log "🔄 Creating Market Data Adapter"
log "==================================================="

# Step 1: Set up EC2 connection
log "Step 1: Setting up EC2 connection..."

# Set parameters
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Create key file if it doesn't exist
if [ ! -f "$KEY_PATH" ]; then
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
fi

# Test the connection
log "Testing connection to EC2 instance at $EC2_IP..."
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'"; then
  log_error "Failed to connect to EC2 instance. Check your EC2_PUBLIC_IP variable."
  exit 1
fi

log_info "✅ Connection to EC2 established successfully."

# Step 2: Create a market data adapter on EC2
log "Step 2: Creating a market data adapter on EC2..."

# Create Python file content
cat > market_data_adapter.py << 'EOF'
#!/usr/bin/env python3
"""
Market Data Adapter for Authentic Backtesting

This script adapts the market_data table to be used with the authentic_backtest.py script.
It creates a view or temporary table that matches the expected schema.
"""
import os
import sys
import logging
import psycopg2
import psycopg2.extras
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("market_data_adapter")

def create_market_data_adapter():
    """
    Create a market data adapter table or view for authentic backtesting.
    Adapts the market_data table to the expected klines_* schema.
    """
    try:
        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL not set")
            return False
        
        # Connect to the database
        logger.info(f"Connecting to database: {db_url[:10]}...{db_url[-10:]}")
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Create views for each interval
        intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        
        for interval in intervals:
            # Create a view for this interval
            logger.info(f"Creating view for interval: {interval}")
            view_name = f"klines_{interval.replace('m', 'min').replace('h', 'hour').replace('d', 'day')}"
            
            # Drop view if it exists
            cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
            
            # Create view
            create_view_sql = f"""
            CREATE VIEW {view_name} AS
            SELECT 
                timestamp,
                symbol,
                open,
                high,
                low,
                close,
                volume
            FROM 
                market_data
            WHERE
                interval = '{interval}'
            """
            
            cursor.execute(create_view_sql)
            logger.info(f"Created view: {view_name}")
        
        # Close database connection
        cursor.close()
        conn.close()
        
        logger.info("Market data adapter created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating market data adapter: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if create_market_data_adapter():
        print("✅ Market data adapter created successfully")
    else:
        print("❌ Failed to create market data adapter")
        sys.exit(1)
EOF

# Copy script to EC2
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no market_data_adapter.py "$SSH_USER@$EC2_IP:$EC2_DIR/market_data_adapter.py"

# Run the script on EC2
log_info "Running market data adapter script on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && DATABASE_URL=\"\${DATABASE_URL}\" python3 market_data_adapter.py"

# Create a wrapper script that runs the adapter before backtesting
log "Step 3: Creating a wrapper script on EC2..."

ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cat > $EC2_DIR/run_adapted_backtest.sh << 'EOL'
#!/bin/bash
# Wrapper script to run adapted authentic_backtest.py

# Set DATABASE_URL directly in the environment
export DATABASE_URL=\"\${DATABASE_URL}\"
export ALPACA_API_KEY=\"\${ALPACA_API_KEY}\"
export ALPACA_API_SECRET=\"\${ALPACA_API_SECRET}\"

# Print confirmation
echo \"Running with DATABASE_URL: \${DATABASE_URL:0:10}...\${DATABASE_URL: -10}\"

# First, run the market data adapter
echo \"Creating market data adapter...\"
python3 market_data_adapter.py

# Then run the authentic_backtest.py with all arguments passed to this script
echo \"Running authentic backtest...\"
python3 backtesting/core/authentic_backtest.py \"\$@\"
EOL"

# Make the wrapper script executable
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/run_adapted_backtest.sh"

# Clean up local files
rm market_data_adapter.py

# Step 4: Create a local run script
log "Step 4: Creating local run script..."

cat > ./run-adapted-backtest.sh << 'EOL'
#!/bin/bash
# Run script for the adapted authentic backtesting

# Set parameters
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Get database URL
DB_URL=$(node -e "console.log(process.env.DATABASE_URL || '')")

if [ -z "$DB_URL" ]; then
  echo "ERROR: DATABASE_URL environment variable is not set!"
  exit 1
fi

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
VERBOSE="false"

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
      VERBOSE="true"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "🚀 Running Adapted Authentic Backtest on EC2"
echo "==================================================="
echo "Parameters:"
echo "- Symbol: $SYMBOL"
echo "- Interval: $INTERVAL"
echo "- Date Range: $START_DATE to $END_DATE"
echo "- Initial Balance: $INITIAL_BALANCE"
echo "- Verbose: $VERBOSE"
echo ""

# Run the backtest on EC2
echo "Running backtest on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && DATABASE_URL=\"$DB_URL\" ./run_adapted_backtest.sh --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $INITIAL_BALANCE"

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
  
  # Display a summary
  if [ "$VERBOSE" == "true" ]; then
    echo "Result summary:"
    cat "$LOCAL_RESULT" | jq
  fi
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
  
  # Display the log
  if [ "$VERBOSE" == "true" ]; then
    echo "Log content:"
    cat "$LOCAL_LOG"
  fi
fi

echo "✅ Backtest process completed!"
EOL

chmod +x ./run-adapted-backtest.sh

log_info "✅ Local run script created."
log "The market data adapter has been created. You can now run backtests with:"
log "   ./run-adapted-backtest.sh --symbol BTCUSDT --interval 1h --start 2025-04-01 --end 2025-04-10"
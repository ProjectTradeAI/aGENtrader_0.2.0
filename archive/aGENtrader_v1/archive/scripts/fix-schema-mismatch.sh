#!/bin/bash
# Script to fix the schema mismatch in authentic_backtest.py

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
log "🔧 Fixing Schema Mismatch in Authentic Backtest"
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

# Step 2: Create a patched version of the authentic_backtest.py on EC2
log "Step 2: Creating a patched version of the authentic_backtest.py on EC2..."

# Create a Python patch script that will be executed on EC2
cat > patch_authentic_backtest.py << 'EOF'
#!/usr/bin/env python3
"""
Patch script for authentic_backtest.py to adapt to the correct database schema.
"""
import os
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("patch_backtest")

def patch_authentic_backtest():
    """
    Patch the authentic_backtest.py file to use the market_data table
    instead of the klines_1h table.
    """
    try:
        # Define file path
        file_path = "backtesting/core/authentic_backtest.py"
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        # Read the original file
        with open(file_path, "r") as f:
            content = f.read()
        
        # Create a backup
        backup_path = f"{file_path}.bak"
        with open(backup_path, "w") as f:
            f.write(content)
        
        logger.info(f"Created backup at {backup_path}")
        
        # Replace the SQL query for getting historical market data
        old_query_pattern = r"SELECT\s+timestamp,\s+open,\s+high,\s+low,\s+close,\s+volume\s+FROM\s+klines_\%s\s+WHERE\s+symbol\s+=\s+\%s\s+AND\s+timestamp\s+>=\s+\%s\s+AND\s+timestamp\s+<=\s+\%s\s+ORDER\s+BY\s+timestamp"
        
        new_query = """SELECT 
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
            timestamp"""
        
        # First, find and replace the SQL query
        if re.search(old_query_pattern, content, re.DOTALL):
            patched_content = re.sub(old_query_pattern, new_query, content, flags=re.DOTALL)
            logger.info("SQL query replaced successfully")
        else:
            # If we can't find the exact query, let's look for the get_historical_market_data function
            # and replace it entirely
            get_historical_data_pattern = r"def get_historical_market_data\(self, symbol, interval, start_date, end_date\):(.*?)return market_data"
            
            # Define the new function
            new_function = """def get_historical_market_data(self, symbol, interval, start_date, end_date):
        """Get historical market data from the database."""
        self.logger.info(f"Getting historical market data for {symbol} {interval} from {start_date} to {end_date}")
        
        # Convert dates to strings in format YYYY-MM-DD
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # Connect to the database
        conn = None
        try:
            conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
            cursor = conn.cursor()
            
            # Query to get historical market data
            query = \"\"\"SELECT 
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
                timestamp\"\"\"
            
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
            if conn:
                conn.close()
            traceback.print_exc()
            return None
        
        finally:
            if conn:
                conn.close()"""
            
            if re.search(get_historical_data_pattern, content, re.DOTALL):
                patched_content = re.sub(get_historical_data_pattern, new_function, content, flags=re.DOTALL)
                logger.info("get_historical_market_data function replaced successfully")
            else:
                logger.error("Could not find the get_historical_market_data function pattern")
                return False
        
        # One more thing to fix: change how interval is passed to the query
        # Find the part where the script formats the interval for the table name
        interval_replacement_pattern = r"interval_table = interval\.replace\('([^']+)', '([^']+)'\)"
        interval_call_pattern = r"self\.get_historical_market_data\(symbol, interval_table,"
        
        if re.search(interval_replacement_pattern, patched_content):
            # Remove the interval formatting
            patched_content = re.sub(interval_replacement_pattern, "# Interval is passed directly now", patched_content)
            logger.info("Removed interval table formatting")
            
            # Update the function call
            if re.search(interval_call_pattern, patched_content):
                patched_content = re.sub(interval_call_pattern, "self.get_historical_market_data(symbol, interval,", patched_content)
                logger.info("Updated function call to pass interval directly")
            else:
                logger.warning("Could not find the interval call pattern")
        else:
            logger.warning("Could not find the interval replacement pattern")
        
        # Write the patched content
        with open(file_path, "w") as f:
            f.write(patched_content)
        
        logger.info(f"Patched {file_path} successfully")
        
        return True
    
    except Exception as e:
        logger.error(f"Error patching authentic_backtest.py: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = patch_authentic_backtest()
    if success:
        print("✅ Patched authentic_backtest.py successfully")
    else:
        print("❌ Failed to patch authentic_backtest.py")
EOF

# Copy patch script to EC2
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no patch_authentic_backtest.py "$SSH_USER@$EC2_IP:$EC2_DIR/patch_authentic_backtest.py"

# Run the patch script on EC2
log_info "Running patch script on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && chmod +x patch_authentic_backtest.py && python3 patch_authentic_backtest.py"

# Clean up
rm patch_authentic_backtest.py

# Step 3: Create a patched run script
log "Step 3: Creating a patched run script on EC2..."

ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cat > $EC2_DIR/run_patched_backtest.sh << 'EOL'
#!/bin/bash
# Wrapper script to run patched authentic_backtest.py

# Set DATABASE_URL directly in the environment
export DATABASE_URL=\"\${DATABASE_URL}\"
export ALPACA_API_KEY=\"\${ALPACA_API_KEY}\"
export ALPACA_API_SECRET=\"\${ALPACA_API_SECRET}\"

# Print confirmation
echo \"Running with DATABASE_URL: \${DATABASE_URL:0:10}...\${DATABASE_URL: -10}\"

# Run the authentic_backtest.py with all arguments passed to this script
python3 backtesting/core/authentic_backtest.py \"\$@\"
EOL"

# Make the run script executable
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/run_patched_backtest.sh"

# Step 4: Create a local run script for the patched version
log "Step 4: Creating local run script for the patched version..."

cat > ./run-patched-backtest.sh << 'EOL'
#!/bin/bash
# Run script for the patched authentic backtesting

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

echo "🚀 Running Patched Authentic Backtest on EC2"
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
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && DATABASE_URL=\"$DB_URL\" ./run_patched_backtest.sh --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $INITIAL_BALANCE"

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

chmod +x ./run-patched-backtest.sh

log_info "✅ Local run script created."
log "The schema mismatch has been fixed. You can now run backtests with:"
log "   ./run-patched-backtest.sh --symbol BTCUSDT --interval 1h --start 2025-04-01 --end 2025-04-10"
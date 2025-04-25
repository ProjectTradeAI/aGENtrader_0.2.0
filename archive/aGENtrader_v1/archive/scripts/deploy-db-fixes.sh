#!/bin/bash
# Deploy fixes for the database adapter and authentic_backtest.py to EC2

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

# Step 1: Generate the fixed scripts
log "Step 1: Generating fixed scripts"
python3 fix-market-data-adapter.py

if [ ! -f "fixed_market_data_adapter.py" ] || [ ! -f "simple_backtest_patch.py" ]; then
  log_error "Failed to generate fixed scripts"
  exit 1
fi

log_info "✅ Fixed scripts generated successfully"

# Step 2: Set up EC2 connection
log "Step 2: Setting up EC2 connection..."

# Set parameters
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Create key file using the hardcoded key if it doesn't exist
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

# Step 3: Upload the fixed scripts
log "Step 3: Uploading fixed scripts to EC2..."

SCP_CMD="scp -i $KEY_PATH -o StrictHostKeyChecking=no"
SSH_CMD="ssh -i $KEY_PATH -o StrictHostKeyChecking=no $SSH_USER@$EC2_IP"

$SCP_CMD fixed_market_data_adapter.py "$SSH_USER@$EC2_IP:$EC2_DIR/fixed_market_data_adapter.py"
$SCP_CMD simple_backtest_patch.py "$SSH_USER@$EC2_IP:$EC2_DIR/simple_backtest_patch.py"

log_info "✅ Fixed scripts uploaded to EC2"

# Step 4: Run the fixed scripts on EC2
log "Step 4: Running fixed scripts on EC2..."

# Get database URL
DB_URL=$(node -e "console.log(process.env.DATABASE_URL || '')")
ALPACA_API_KEY=$(node -e "console.log(process.env.ALPACA_API_KEY || '')")
ALPACA_API_SECRET=$(node -e "console.log(process.env.ALPACA_API_SECRET || '')")
OPENAI_API_KEY=$(node -e "console.log(process.env.OPENAI_API_KEY || '')")

if [ -z "$DB_URL" ]; then
  log_error "DATABASE_URL environment variable is not set!"
  exit 1
fi

# Run the fixed market data adapter
log_info "Running fixed market data adapter on EC2..."
$SSH_CMD "cd $EC2_DIR && DATABASE_URL=\"$DB_URL\" python3 fixed_market_data_adapter.py"

# Run the simple backtest patch
log_info "Running simple backtest patch on EC2..."
$SSH_CMD "cd $EC2_DIR && python3 simple_backtest_patch.py"

# Step 5: Update run script
log "Step 5: Updating run script on EC2..."

# Create a new run script
cat > new_run_full_backtest.sh << 'EOF'
#!/bin/bash
# Run the full authentic multi-agent backtesting (FIXED VERSION)

# Set default values
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-15"
END_DATE="2025-03-25"
BALANCE=10000

# Parse command line arguments
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

# Ensure the environment variables are set
if [ -z "$DATABASE_URL" ]; then
  echo "ERROR: DATABASE_URL environment variable is not set."
  exit 1
fi

# Check that directory exists
if [ ! -d "backtesting/core" ]; then
  echo "Creating directory structure..."
  mkdir -p backtesting/core
fi

# Create a startup script that will run in Python to ensure environment is set up
cat > check_env.py << 'EOF2'
import sys
import os
import importlib.util

def check_module(module_name, import_path=None):
    """Check if a module can be imported"""
    try:
        if import_path:
            spec = importlib.util.spec_from_file_location(module_name, import_path)
            if not spec:
                return False
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            __import__(module_name)
        return True
    except Exception as e:
        print(f"Error importing {module_name}: {str(e)}")
        return False

# Print Python version
print(f"Python version: {sys.version}")

# Check environment variables
print(f"DATABASE_URL set: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")
print(f"ALPACA_API_KEY set: {'Yes' if os.environ.get('ALPACA_API_KEY') else 'No'}")
print(f"OPENAI_API_KEY set: {'Yes' if os.environ.get('OPENAI_API_KEY') else 'No'}")

# Check for required modules
print(f"psycopg2 available: {'Yes' if check_module('psycopg2') else 'No'}")

# Check for authentic backtest module
print(f"AuthenticBacktest available: {'Yes' if check_module('AuthenticBacktest', 'backtesting/core/authentic_backtest.py') else 'No'}")

# Check directories
for directory in ["logs/backtests", "results", "data/logs/decisions"]:
    if not os.path.exists(directory):
        print(f"Creating directory: {directory}")
        os.makedirs(directory, exist_ok=True)
EOF2

# Run environment check
echo "Running environment check..."
python3 check_env.py

# Run the authentic backtest
echo "Running authentic multi-agent backtest with params:"
echo "- Symbol: $SYMBOL"
echo "- Interval: $INTERVAL"
echo "- Date Range: $START_DATE to $END_DATE"
echo "- Initial Balance: $BALANCE"

# Run the authentic_backtest.py script
python3 backtesting/core/authentic_backtest.py \
  --symbol $SYMBOL \
  --interval $INTERVAL \
  --start_date $START_DATE \
  --end_date $END_DATE \
  --initial_balance $BALANCE

# Check if results directory exists
if [ -d "results" ]; then
  echo "Latest results:"
  ls -la results | grep backtest | tail -5
fi
EOF

# Upload the new run script
$SCP_CMD new_run_full_backtest.sh "$SSH_USER@$EC2_IP:$EC2_DIR/run_full_backtest.sh"

# Make the script executable
$SSH_CMD "chmod +x $EC2_DIR/run_full_backtest.sh"

# Step 6: Update local run script
log "Step 6: Updating local run script..."

# Create an updated local run script
cat > run-agent-backtest-fixed.sh << 'EOL'
#!/bin/bash
# Run agent backtest on EC2 with fixed scripts

# Set parameters
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Get database URL
DB_URL=$(node -e "console.log(process.env.DATABASE_URL || '')")
ALPACA_API_KEY=$(node -e "console.log(process.env.ALPACA_API_KEY || '')")
ALPACA_API_SECRET=$(node -e "console.log(process.env.ALPACA_API_SECRET || '')")
OPENAI_API_KEY=$(node -e "console.log(process.env.OPENAI_API_KEY || '')")

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

# Parse command line arguments
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-15"
END_DATE="2025-03-25"
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

echo "🚀 Running Multi-Agent Backtest on EC2"
echo "==================================================="
echo "Parameters:"
echo "- Symbol: $SYMBOL"
echo "- Interval: $INTERVAL"
echo "- Date Range: $START_DATE to $END_DATE"
echo "- Initial Balance: $BALANCE"
echo ""

# Reset the environment on EC2 (to ensure fresh variables)
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && DATABASE_URL=\"$DB_URL\" ALPACA_API_KEY=\"$ALPACA_API_KEY\" ALPACA_API_SECRET=\"$ALPACA_API_SECRET\" OPENAI_API_KEY=\"$OPENAI_API_KEY\" ./run_full_backtest.sh --symbol $SYMBOL --interval $INTERVAL --start $START_DATE --end $END_DATE --balance $BALANCE"

# Download the latest results from EC2
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
  
  # Check if results are valid JSON
  if [ -f "$LOCAL_RESULT" ]; then
    if python3 -m json.tool "$LOCAL_RESULT" > /dev/null 2>&1; then
      echo "✅ Valid JSON results downloaded successfully"
      
      # Extract key performance metrics
      FINAL_EQUITY=$(cat $LOCAL_RESULT | python3 -c "import json, sys; data=json.load(sys.stdin); print(f\"Final Equity: \${data.get('performance_metrics', {}).get('final_equity', 0):.2f}\")")
      TOTAL_RETURN=$(cat $LOCAL_RESULT | python3 -c "import json, sys; data=json.load(sys.stdin); print(f\"Total Return: {data.get('performance_metrics', {}).get('total_return_pct', 0):.2f}%\")")
      WIN_RATE=$(cat $LOCAL_RESULT | python3 -c "import json, sys; data=json.load(sys.stdin); print(f\"Win Rate: {data.get('performance_metrics', {}).get('win_rate', 0):.2f}%\")")
      MAX_DD=$(cat $LOCAL_RESULT | python3 -c "import json, sys; data=json.load(sys.stdin); print(f\"Max Drawdown: {data.get('performance_metrics', {}).get('max_drawdown_pct', 0):.2f}%\")")
      
      echo "=== PERFORMANCE SUMMARY ==="
      echo $FINAL_EQUITY
      echo $TOTAL_RETURN
      echo $WIN_RATE
      echo $MAX_DD
      echo "==========================="
    else
      echo "❌ Downloaded file is not valid JSON. Check logs for errors."
    fi
  fi
fi

# Download the latest log file from EC2
LATEST_LOG=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "ls -t $EC2_DIR/logs/backtests/backtest_*.log 2>/dev/null | head -n 1")

if [ -n "$LATEST_LOG" ]; then
  echo "Latest log file on EC2: $LATEST_LOG"
  
  # Download the log file
  echo "Downloading log file from EC2..."
  mkdir -p ./logs/backtests
  LOCAL_LOG="./logs/backtests/$(basename $LATEST_LOG)"
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$LATEST_LOG" "$LOCAL_LOG"
  echo "Downloaded log file to: $LOCAL_LOG"
  
  # Display end of log file
  echo "=== LOG FILE SUMMARY (last 10 lines) ==="
  tail -10 "$LOCAL_LOG"
  echo "========================================"
fi

echo "✅ Multi-agent backtest process completed!"
EOL

chmod +x ./run-agent-backtest-fixed.sh

# Step 7: Clean up
log "Step 7: Cleaning up..."
rm -f fixed_market_data_adapter.py simple_backtest_patch.py new_run_full_backtest.sh

log "✅ Deployment of fixes completed!"
log "You can now run a backtest with the fixed system using:"
log "  ./run-agent-backtest-fixed.sh --symbol BTCUSDT --interval 1h --start 2025-03-15 --end 2025-03-25 --balance 10000"
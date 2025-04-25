#!/bin/bash
# Unified Backtesting Script
# This script provides a single entry point for running various types of backtests

# Default values
SYMBOL="BTCUSDT"
INTERVAL="1h"
DAYS=7
START_DATE=""
END_DATE=""
MODE="standard"
STRATEGY="multi_agent"
VERBOSE=0
OUTPUT_DIR="./results/backtests"
LOG_DIR="./logs/backtests"
EC2_MODE=0
EC2_IP="51.20.250.135"
EC2_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
EC2_KEY="/tmp/backtest_key.pem"

# Function to display usage information
usage() {
  echo "Unified Backtesting Script"
  echo ""
  echo "Usage: ./backtesting/scripts/run_backtest.sh [options]"
  echo ""
  echo "Options:"
  echo "  --symbol SYMBOL      Symbol to backtest (default: BTCUSDT)"
  echo "  --interval INTERVAL  Time interval (1m, 5m, 15m, 1h, 4h, 1d) (default: 1h)"
  echo "  --days DAYS          Number of days to backtest (default: 7)"
  echo "  --start DATE         Start date (YYYY-MM-DD) (overrides --days)"
  echo "  --end DATE           End date (YYYY-MM-DD) (default: today)"
  echo "  --mode MODE          Backtest mode: standard, authentic, full (default: standard)"
  echo "  --strategy STRATEGY  Trading strategy to use (default: multi_agent)"
  echo "  --verbose            Enable verbose output"
  echo "  --output-dir DIR     Directory for output files (default: ./results/backtests)"
  echo "  --log-dir DIR        Directory for log files (default: ./logs/backtests)"
  echo "  --ec2                Run on EC2 instead of locally"
  echo "  --help               Display this help and exit"
  echo ""
  echo "Examples:"
  echo "  ./backtesting/scripts/run_backtest.sh --symbol BTCUSDT --interval 1h --days 30"
  echo "  ./backtesting/scripts/run_backtest.sh --mode authentic --start 2025-03-01 --end 2025-04-01"
  echo "  ./backtesting/scripts/run_backtest.sh --ec2 --strategy multi_agent --verbose"
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --symbol)
      SYMBOL="$2"
      shift 2
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --days)
      DAYS="$2"
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
    --mode)
      MODE="$2"
      shift 2
      ;;
    --strategy)
      STRATEGY="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --log-dir)
      LOG_DIR="$2"
      shift 2
      ;;
    --ec2)
      EC2_MODE=1
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

# Create output and log directories if they don't exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$LOG_DIR"

# Generate a timestamp for output files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/backtest_${TIMESTAMP}.log"
RESULT_FILE="${OUTPUT_DIR}/backtest_${TIMESTAMP}.json"

# Function to get the appropriate backtest script based on mode
get_backtest_script() {
  case "$MODE" in
    standard)
      echo "backtesting/core/standard_backtest.py"
      ;;
    authentic)
      echo "backtesting/core/authentic_backtest.py"
      ;;
    full)
      echo "backtesting/core/full_agent_backtest.py"
      ;;
    *)
      echo "Unknown mode: $MODE"
      exit 1
      ;;
  esac
}

# Function to build the command line for the backtest
build_command() {
  SCRIPT=$(get_backtest_script)
  CMD="python3 $SCRIPT --symbol $SYMBOL --interval $INTERVAL"
  
  if [ -n "$START_DATE" ]; then
    CMD="$CMD --start $START_DATE"
  else
    CMD="$CMD --days $DAYS"
  fi
  
  if [ -n "$END_DATE" ]; then
    CMD="$CMD --end $END_DATE"
  fi
  
  CMD="$CMD --strategy $STRATEGY --output $RESULT_FILE"
  
  if [ $VERBOSE -eq 1 ]; then
    CMD="$CMD --verbose"
  fi
  
  echo "$CMD"
}

# Function to run on EC2
run_on_ec2() {
  echo "Running backtest on EC2 instance..."
  
  # Create EC2 key file if needed
  if [ ! -f "$EC2_KEY" ]; then
    echo "Creating EC2 key file..."
    cat > "$EC2_KEY" << 'KEYEOF'
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
    chmod 600 "$EC2_KEY"
  fi
  
  # Build the command
  REMOTE_CMD=$(build_command)
  
  # Test connection
  echo "Testing connection to EC2..."
  if ! ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "echo 'Connection successful'" > /dev/null 2>&1; then
    echo "❌ Failed to connect to EC2. Please check your connection settings."
    exit 1
  fi
  
  # Create output directories on EC2
  ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "cd $EC2_DIR && mkdir -p $OUTPUT_DIR $LOG_DIR"
  
  # Run the command on EC2
  echo "Running command on EC2: $REMOTE_CMD"
  ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "cd $EC2_DIR && export PYTHONPATH=$EC2_DIR && $REMOTE_CMD > $LOG_FILE 2>&1"
  
  # Download the result file
  echo "Downloading result file from EC2..."
  mkdir -p $(dirname "$RESULT_FILE")
  scp -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP:$EC2_DIR/$RESULT_FILE" "$RESULT_FILE"
  
  # Download the log file
  echo "Downloading log file from EC2..."
  mkdir -p $(dirname "$LOG_FILE")
  scp -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP:$EC2_DIR/$LOG_FILE" "$LOG_FILE"
}

# Function to run locally
run_locally() {
  echo "Running backtest locally..."
  
  # Build the command
  CMD=$(build_command)
  
  # Run the command
  echo "Running command: $CMD"
  eval "$CMD > $LOG_FILE 2>&1"
}

# Main function
main() {
  echo "========================================"
  echo "UNIFIED BACKTESTING SCRIPT"
  echo "========================================"
  echo "Symbol: $SYMBOL"
  echo "Interval: $INTERVAL"
  
  if [ -n "$START_DATE" ]; then
    echo "Start date: $START_DATE"
  else
    echo "Days: $DAYS"
  fi
  
  if [ -n "$END_DATE" ]; then
    echo "End date: $END_DATE"
  else
    echo "End date: today"
  fi
  
  echo "Mode: $MODE"
  echo "Strategy: $STRATEGY"
  echo "Verbose: $([ $VERBOSE -eq 1 ] && echo "yes" || echo "no")"
  echo "Output directory: $OUTPUT_DIR"
  echo "Log directory: $LOG_DIR"
  echo "Output file: $RESULT_FILE"
  echo "Log file: $LOG_FILE"
  echo "Running on: $([ $EC2_MODE -eq 1 ] && echo "EC2" || echo "local")"
  echo "========================================"
  
  # Run the backtest
  if [ $EC2_MODE -eq 1 ]; then
    run_on_ec2
  else
    run_locally
  fi
  
  # Check if the backtest was successful
  if [ $? -eq 0 ]; then
    echo "✅ Backtest completed successfully!"
    echo "Results saved to: $RESULT_FILE"
    echo "Log saved to: $LOG_FILE"
    
    # If we have a result file, display a summary
    if [ -f "$RESULT_FILE" ]; then
      echo -e "\n===== BACKTEST SUMMARY ====="
      python3 -c "import json; data = json.load(open('$RESULT_FILE')); print(f\"Symbol: {data.get('symbol', 'Unknown')}\"); print(f\"Period: {data.get('start_date', 'Unknown')} to {data.get('end_date', 'Unknown')}\"); print(f\"Total trades: {len(data.get('trades', []))}\"); print(f\"Final balance: {data.get('final_balance', 'Unknown')}\"); print(f\"Return: {data.get('return_percentage', 'Unknown')}%\");" 2>/dev/null
    fi
  else
    echo "❌ Backtest failed. Check the log file for details: $LOG_FILE"
  fi
}

# Run the main function
main

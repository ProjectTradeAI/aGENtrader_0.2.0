#!/bin/bash
# Run Authentic Backtest
# This script runs the authentic backtesting framework locally or on EC2

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

# Default parameters
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE=$(date -d "7 days ago" +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)
INITIAL_BALANCE=10000
RUN_ON_EC2=false
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
    --ec2)
      RUN_ON_EC2=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      echo "Usage: $0 [--symbol BTCUSDT] [--interval 1h] [--start 2025-03-01] [--end 2025-03-02] [--balance 10000] [--ec2] [--verbose]"
      echo
      echo "Options:"
      echo "  --symbol      Trading symbol [default: BTCUSDT]"
      echo "  --interval    Time interval (1m, 5m, 15m, 1h, 4h, 1d) [default: 1h]"
      echo "  --start       Start date [default: 7 days ago]"
      echo "  --end         End date [default: today]"
      echo "  --balance     Initial balance [default: 10000]"
      echo "  --ec2         Run the backtest on EC2 instead of locally"
      echo "  --verbose     Show verbose output"
      echo "  --help        Show this help message"
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      echo "Usage: $0 [--symbol BTCUSDT] [--interval 1h] [--start 2025-03-01] [--end 2025-03-02] [--balance 10000] [--ec2] [--verbose]"
      exit 1
      ;;
  esac
done

# Print parameters
log "Running authentic backtest with parameters:"
log_info "Symbol: $SYMBOL"
log_info "Interval: $INTERVAL"
log_info "Date Range: $START_DATE to $END_DATE"
log_info "Initial Balance: $INITIAL_BALANCE"
log_info "Run on EC2: $RUN_ON_EC2"
log_info "Verbose: $VERBOSE"
echo

# Function to run the backtest locally
run_local_backtest() {
  log "Running authentic backtest locally..."
  
  # Create necessary directories
  mkdir -p ./results
  mkdir -p ./logs/backtests
  
  # Run the backtest
  COMMAND="python backtesting/core/authentic_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $INITIAL_BALANCE"
  
  if [ "$VERBOSE" = true ]; then
    log_info "Running command: $COMMAND"
    eval $COMMAND
  else
    log_info "Running command: $COMMAND"
    eval $COMMAND | grep -v "DEBUG"
  fi
  
  # Check exit status
  if [ $? -eq 0 ]; then
    log "✅ Backtest completed successfully!"
    
    # Check for results
    LATEST_RESULT=$(ls -t ./results/backtest_*.json 2>/dev/null | head -n 1)
    if [ -n "$LATEST_RESULT" ]; then
      log_info "Latest result file: $LATEST_RESULT"
    fi
    
    # Check for logs
    LATEST_LOG=$(ls -t ./logs/backtests/backtest_*.log 2>/dev/null | head -n 1)
    if [ -n "$LATEST_LOG" ]; then
      log_info "Latest log file: $LATEST_LOG"
    fi
  else
    log_error "❌ Backtest failed!"
  fi
}

# Function to run the backtest on EC2
run_ec2_backtest() {
  log "Preparing to run authentic backtest on EC2..."
  
  # Ensure we have EC2_PUBLIC_IP
  if [ -z "$EC2_PUBLIC_IP" ]; then
    log_error "EC2_PUBLIC_IP environment variable is not set."
    log_error "Please set it by running: export EC2_PUBLIC_IP=<your-ec2-ip>"
    exit 1
  fi
  
  # Set up SSH key
  KEY_PATH="/tmp/ec2_backtest_key.pem"
  
  # Check if we have the key in an environment variable
  if [ -n "$EC2_KEY" ]; then
    log_info "Using EC2_KEY from environment variable"
    echo "$EC2_KEY" > "$KEY_PATH"
    chmod 600 "$KEY_PATH"
  elif [ -n "$EC2_SSH_KEY" ]; then
    log_info "Using EC2_SSH_KEY from environment variable"
    echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
    echo "$EC2_SSH_KEY" | fold -w 64 >> "$KEY_PATH"
    echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
    chmod 600 "$KEY_PATH"
  elif [ -n "$EC2_PRIVATE_KEY" ]; then
    log_info "Using EC2_PRIVATE_KEY from environment variable"
    echo "$EC2_PRIVATE_KEY" > "$KEY_PATH"
    chmod 600 "$KEY_PATH"
  else
    log_error "No EC2 SSH key found. Please set EC2_KEY, EC2_SSH_KEY or EC2_PRIVATE_KEY environment variable."
    exit 1
  fi
  
  # Create directories for results
  mkdir -p ./results
  mkdir -p ./logs/backtests
  
  # Upload authentic_backtest.py to EC2
  log "Uploading authentic backtest files to EC2..."
  
  # First ensure backtesting structure exists on EC2
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "mkdir -p /home/ec2-user/aGENtrader/backtesting/core /home/ec2-user/aGENtrader/backtesting/scripts /home/ec2-user/aGENtrader/results /home/ec2-user/aGENtrader/logs/backtests"
  
  # Upload the authentic_backtest.py file
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no ./backtesting/core/authentic_backtest.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/backtesting/core/
  
  # Run the backtest on EC2
  log "Running authentic backtest on EC2..."
  COMMAND="cd /home/ec2-user/aGENtrader && python3 backtesting/core/authentic_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $INITIAL_BALANCE"
  
  if [ "$VERBOSE" = true ]; then
    log_info "Running command on EC2: $COMMAND"
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "$COMMAND"
  else
    log_info "Running command on EC2: $COMMAND"
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "$COMMAND" | grep -v "DEBUG"
  fi
  
  # Check exit status
  if [ $? -eq 0 ]; then
    log "✅ Backtest completed successfully on EC2!"
    
    # Get latest result file
    LATEST_RESULT=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "ls -t /home/ec2-user/aGENtrader/results/backtest_*.json 2>/dev/null | head -n 1")
    
    if [ -n "$LATEST_RESULT" ]; then
      log_info "Latest result file on EC2: $LATEST_RESULT"
      
      # Download the result file
      log "Downloading result file from EC2..."
      LOCAL_RESULT="./results/$(basename $LATEST_RESULT)"
      scp -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP:$LATEST_RESULT $LOCAL_RESULT
      log_info "Downloaded result file to: $LOCAL_RESULT"
    fi
    
    # Get latest log file
    LATEST_LOG=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "ls -t /home/ec2-user/aGENtrader/logs/backtests/backtest_*.log 2>/dev/null | head -n 1")
    
    if [ -n "$LATEST_LOG" ]; then
      log_info "Latest log file on EC2: $LATEST_LOG"
      
      # Download the log file
      log "Downloading log file from EC2..."
      LOCAL_LOG="./logs/backtests/$(basename $LATEST_LOG)"
      scp -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP:$LATEST_LOG $LOCAL_LOG
      log_info "Downloaded log file to: $LOCAL_LOG"
    fi
  else
    log_error "❌ Backtest failed on EC2!"
  fi
}

# Run the backtest
if [ "$RUN_ON_EC2" = true ]; then
  run_ec2_backtest
else
  run_local_backtest
fi

log "Authentic backtest process completed!"
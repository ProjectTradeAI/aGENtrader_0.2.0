#!/bin/bash
# Script to run backtests on EC2

# Configuration
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
KEY_PATH="/tmp/ec2_key.pem"
EC2_DIR="/home/ec2-user/aGENtrader"

# Create key file from secret
if [ ! -f "$KEY_PATH" ]; then
  echo "Creating key file from EC2_KEY secret..."
  echo "$EC2_KEY" > "$KEY_PATH"
  chmod 600 "$KEY_PATH"
fi

# Default values
TYPE="simplified"
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-01"
END_DATE="2025-04-01"
POSITION_SIZE="50"
BALANCE="10000"
RISK="0.02"
LOCAL_LLM=""

# Function to display help
show_help() {
  echo "EC2 Backtest Runner"
  echo "==================="
  echo "Usage: $0 [options]"
  echo
  echo "Options:"
  echo "  --help               Show this help message"
  echo "  --type TYPE          Type of backtest (simplified, enhanced, full-scale)"
  echo "  --symbol SYMBOL      Trading symbol (default: BTCUSDT)"
  echo "  --interval INTERVAL  Trading interval (default: 1h)"
  echo "  --start DATE         Start date (format: YYYY-MM-DD)"
  echo "  --end DATE           End date (format: YYYY-MM-DD)"
  echo "  --position_size SIZE Position size for simplified backtest (default: 50)"
  echo "  --balance AMOUNT     Initial balance for enhanced backtest (default: 10000)"
  echo "  --risk PERCENTAGE    Risk percentage as decimal (default: 0.02)"
  echo "  --local-llm          Use local Mixtral model instead of OpenAI"
  echo
  echo "Examples:"
  echo "  $0 --type simplified --symbol BTCUSDT --interval 1h --local-llm"
  echo "  $0 --type enhanced --symbol ETHUSDT --interval 4h --start 2025-02-01 --end 2025-03-01"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --help)
      show_help
      exit 0
      ;;
    --type)
      TYPE="$2"
      shift 2
      ;;
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
    --position_size)
      POSITION_SIZE="$2"
      shift 2
      ;;
    --balance)
      BALANCE="$2"
      shift 2
      ;;
    --risk)
      RISK="$2"
      shift 2
      ;;
    --local-llm)
      LOCAL_LLM="--local-llm"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# Construct the command based on the backtest type
if [[ "$TYPE" == "simplified" ]]; then
  BACKTEST_CMD="./ec2-multi-agent-backtest.sh --type $TYPE --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --position_size $POSITION_SIZE $LOCAL_LLM"
else
  BACKTEST_CMD="./ec2-multi-agent-backtest.sh --type $TYPE --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --balance $BALANCE --risk $RISK --decision_interval 2 --min_confidence 75 $LOCAL_LLM"
fi

# Display the backtest configuration
echo "==================================================="
echo "  Running $TYPE Backtest on EC2"
echo "==================================================="
echo "Symbol: $SYMBOL"
echo "Interval: $INTERVAL"
echo "Date Range: $START_DATE to $END_DATE"
if [[ "$TYPE" == "simplified" ]]; then
  echo "Position Size: $POSITION_SIZE"
else
  echo "Initial Balance: $BALANCE"
  echo "Risk Percentage: $RISK"
fi
if [[ -n "$LOCAL_LLM" ]]; then
  echo "Using: Local Mixtral model"
else
  echo "Using: OpenAI API"
fi
echo

# Run the backtest
echo "Running backtest on EC2..."
echo "---------------------------------------------------"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && $BACKTEST_CMD"
RESULT=$?

if [ $RESULT -eq 0 ]; then
  echo "---------------------------------------------------"
  echo "✅ Backtest completed successfully!"
  echo
  echo "To retrieve results, run:"
  echo "./connect-ec2.sh \"cd $EC2_DIR && ls -la results/\""
  echo "./connect-ec2.sh \"cd $EC2_DIR && cat results/backtest_result_XXXXXXXX_XXXXXX.json\""
else
  echo "---------------------------------------------------"
  echo "❌ Backtest failed with error code $RESULT"
fi

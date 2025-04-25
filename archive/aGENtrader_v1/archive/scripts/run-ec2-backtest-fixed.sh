#!/bin/bash
# Script to run full-scale backtest on EC2 with the fixed decision_session_fixed.py

# Default values
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-01"
END_DATE="2025-03-10"
INITIAL_BALANCE=10000
RISK_PER_TRADE=0.02
MAX_POSITION_SIZE=0.5
DECISION_INTERVAL=12
MIN_CONFIDENCE=60
STOP_LOSS_PCT=0.03
TAKE_PROFIT_PCT=0.05
USE_STOP_LOSS=true
USE_TAKE_PROFIT=true
OUTPUT_DIR="data/backtests"
OUTPUT_FILE=""

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
    --start_date)
      START_DATE="$2"
      shift 2
      ;;
    --end_date)
      END_DATE="$2"
      shift 2
      ;;
    --initial_balance)
      INITIAL_BALANCE="$2"
      shift 2
      ;;
    --risk_per_trade)
      RISK_PER_TRADE="$2"
      shift 2
      ;;
    --max_position_size)
      MAX_POSITION_SIZE="$2"
      shift 2
      ;;
    --decision_interval)
      DECISION_INTERVAL="$2"
      shift 2
      ;;
    --min_confidence)
      MIN_CONFIDENCE="$2"
      shift 2
      ;;
    --stop_loss_pct)
      STOP_LOSS_PCT="$2"
      shift 2
      ;;
    --take_profit_pct)
      TAKE_PROFIT_PCT="$2"
      shift 2
      ;;
    --no_stop_loss)
      USE_STOP_LOSS=false
      shift
      ;;
    --no_take_profit)
      USE_TAKE_PROFIT=false
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

# Set output file name
if [ -z "$OUTPUT_FILE" ]; then
  OUTPUT_FILE="${OUTPUT_DIR}/ec2_full_backtest_${SYMBOL}_${INTERVAL}_$(date +%Y%m%d_%H%M%S).json"
fi

# Check if EC2_PUBLIC_IP and EC2_SSH_KEY are set
if [ -z "$EC2_PUBLIC_IP" ]; then
  echo "ERROR: EC2_PUBLIC_IP environment variable is not set"
  exit 1
fi

if [ -z "$EC2_SSH_KEY" ]; then
  echo "ERROR: EC2_SSH_KEY environment variable is not set"
  exit 1
fi

# Temporary file for SSH key with proper formatting
KEY_FILE=$(mktemp)
echo "Creating properly formatted SSH key..."
echo -e "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_FILE"
echo "$EC2_SSH_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY-----//g' | sed 's/-----END RSA PRIVATE KEY-----//g' | tr -d '\n' | fold -w 64 >> "$KEY_FILE"
echo -e "\n-----END RSA PRIVATE KEY-----" >> "$KEY_FILE"
chmod 600 "$KEY_FILE"

# Build command with all arguments
CMD="cd /home/ec2-user/aGENtrader && python3 run_full_scale_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $INITIAL_BALANCE --risk_per_trade $RISK_PER_TRADE --max_position_size $MAX_POSITION_SIZE --decision_interval $DECISION_INTERVAL --min_confidence $MIN_CONFIDENCE"

if [ "$USE_STOP_LOSS" = true ]; then
  CMD="$CMD --use_stop_loss --stop_loss_pct $STOP_LOSS_PCT"
fi

if [ "$USE_TAKE_PROFIT" = true ]; then
  CMD="$CMD --use_take_profit --take_profit_pct $TAKE_PROFIT_PCT"
fi

CMD="$CMD --output_file $OUTPUT_FILE"

echo "======================================"
echo "Running Full-Scale Backtest on EC2"
echo "======================================"
echo "Symbol:          $SYMBOL"
echo "Interval:        $INTERVAL"
echo "Date Range:      $START_DATE to $END_DATE"
echo "Initial Balance: $INITIAL_BALANCE"
echo "Decision Interval: Every $DECISION_INTERVAL candles"
echo "Minimum Confidence: $MIN_CONFIDENCE%"
echo "Stop Loss:       $([ "$USE_STOP_LOSS" = true ] && echo "Yes ($STOP_LOSS_PCT%)" || echo "No")"
echo "Take Profit:     $([ "$USE_TAKE_PROFIT" = true ] && echo "Yes ($TAKE_PROFIT_PCT%)" || echo "No")"
echo "Output File:     $OUTPUT_FILE"
echo "======================================"
echo "Testing SSH connection..."

if ! ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "echo Connected successfully"; then
  echo "Error: Failed to connect to EC2 instance"
  rm "$KEY_FILE"
  exit 1
fi

echo "Connection successful!"
echo "======================================"
echo "Creating output directory on EC2..."
ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "mkdir -p /home/ec2-user/aGENtrader/$OUTPUT_DIR"

echo "======================================"
echo "Executing command on EC2 instance..."
echo "$CMD"
echo "======================================"

# Execute the command on EC2
ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "$CMD"
EXIT_CODE=$?

# Clean up the temporary key file
rm "$KEY_FILE"

if [ $EXIT_CODE -ne 0 ]; then
  echo "Error: Backtest execution failed with exit code $EXIT_CODE"
  exit $EXIT_CODE
fi

echo "======================================"
echo "Backtest completed successfully on EC2!"
echo "Results are stored in $OUTPUT_FILE on EC2."
echo "======================================"

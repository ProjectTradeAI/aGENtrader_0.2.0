#!/bin/bash
# Script to run a full-scale backtest on EC2

# Default values
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE=$(date -d "30 days ago" +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)
INITIAL_BALANCE=10000
RISK_PER_TRADE=0.02
MAX_POSITION_SIZE=0.5
USE_STOP_LOSS=false
STOP_LOSS_PCT=0.02
USE_TAKE_PROFIT=false
TAKE_PROFIT_PCT=0.04
DECISION_INTERVAL=24
MIN_CONFIDENCE=65
VERBOSE=false

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
    --use_stop_loss)
      USE_STOP_LOSS=true
      shift
      ;;
    --stop_loss_pct)
      STOP_LOSS_PCT="$2"
      shift 2
      ;;
    --use_take_profit)
      USE_TAKE_PROFIT=true
      shift
      ;;
    --take_profit_pct)
      TAKE_PROFIT_PCT="$2"
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
    --verbose)
      VERBOSE=true
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

# Check if EC2_PUBLIC_IP and EC2_SSH_KEY are set
if [ -z "$EC2_PUBLIC_IP" ]; then
  echo "ERROR: EC2_PUBLIC_IP environment variable is not set"
  exit 1
fi

if [ -z "$EC2_SSH_KEY" ]; then
  echo "ERROR: EC2_SSH_KEY environment variable is not set"
  exit 1
fi

# Temporary file for SSH key
KEY_FILE=$(mktemp)
echo "$EC2_SSH_KEY" > "$KEY_FILE"
chmod 600 "$KEY_FILE"

# Build the command with all arguments
BACKTEST_CMD="cd /home/ec2-user/aGENtrader && python run_full_scale_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $INITIAL_BALANCE --risk_per_trade $RISK_PER_TRADE --max_position_size $MAX_POSITION_SIZE --decision_interval $DECISION_INTERVAL --min_confidence $MIN_CONFIDENCE"

# Add optional flags
if [ "$USE_STOP_LOSS" = true ]; then
  BACKTEST_CMD="$BACKTEST_CMD --use_stop_loss --stop_loss_pct $STOP_LOSS_PCT"
fi

if [ "$USE_TAKE_PROFIT" = true ]; then
  BACKTEST_CMD="$BACKTEST_CMD --use_take_profit --take_profit_pct $TAKE_PROFIT_PCT"
fi

if [ "$VERBOSE" = true ]; then
  BACKTEST_CMD="$BACKTEST_CMD --verbose"
fi

# Create output file name
OUTPUT_FILE="data/backtests/ec2_full_backtest_${SYMBOL}_${INTERVAL}_$(date +%Y%m%d_%H%M%S).json"
BACKTEST_CMD="$BACKTEST_CMD --output_file $OUTPUT_FILE"

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
echo "Executing command on EC2 instance..."
echo "$BACKTEST_CMD"
echo "======================================"

# Execute the command on EC2
ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "$BACKTEST_CMD"
EXIT_CODE=$?

# Clean up the temporary key file
rm "$KEY_FILE"

if [ $EXIT_CODE -ne 0 ]; then
  echo "Error: Backtest execution failed with exit code $EXIT_CODE"
  exit $EXIT_CODE
fi

echo "======================================"
echo "Backtest executed successfully!"
echo "======================================"
echo "Retrieving results file from EC2..."

# Create a temporary SCP key
SCP_KEY_FILE=$(mktemp)
echo "$EC2_SSH_KEY" > "$SCP_KEY_FILE"
chmod 600 "$SCP_KEY_FILE"

# Create local directory if it doesn't exist
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Download the results file using SCP
scp -o StrictHostKeyChecking=no -i "$SCP_KEY_FILE" ec2-user@"$EC2_PUBLIC_IP":"/home/ec2-user/aGENtrader/$OUTPUT_FILE" "$OUTPUT_FILE"
SCP_EXIT_CODE=$?

# Clean up the temporary key file
rm "$SCP_KEY_FILE"

if [ $SCP_EXIT_CODE -ne 0 ]; then
  echo "Error: Failed to download results file with exit code $SCP_EXIT_CODE"
  exit $SCP_EXIT_CODE
fi

echo "======================================"
echo "Results downloaded successfully to $OUTPUT_FILE"
echo "======================================"
echo "Generating summary..."

# Analyze the results file
python -c "
import json
import sys

try:
    with open('$OUTPUT_FILE', 'r') as f:
        results = json.load(f)
    
    print('\nBACKTEST SUMMARY')
    print('====================================')
    print(f'Symbol:          {results.get(\"symbol\", \"UNKNOWN\")}')
    print(f'Period:          {results.get(\"start_date\", \"UNKNOWN\")} to {results.get(\"end_date\", \"UNKNOWN\")}')
    print(f'Initial Balance: ${results.get(\"initial_balance\", 0):.2f}')
    print(f'Final Balance:   ${results.get(\"final_balance\", 0):.2f}')
    print(f'Net Profit:      ${results.get(\"net_profit\", 0):.2f} ({results.get(\"net_profit_pct\", 0):.2f}%)')
    print(f'Total Trades:    {results.get(\"total_trades\", 0)}')
    print(f'Win Rate:        {results.get(\"win_rate\", 0):.2f}%')
    print(f'Profit Factor:   {results.get(\"profit_factor\", 0):.2f}')
    print(f'Max Drawdown:    {results.get(\"max_drawdown\", 0):.2f}%')
    print(f'Sharpe Ratio:    {results.get(\"sharpe_ratio\", 0):.2f}')
    
    # Decision analysis
    if 'decision_analysis' in results:
        analysis = results['decision_analysis']
        print('\nDECISION ANALYSIS')
        print('====================================')
        print(f'Total Decisions:  {analysis.get(\"total_decisions\", 0)}')
        print(f'Buy Decisions:    {analysis.get(\"buy_decisions\", 0)}')
        print(f'Sell Decisions:   {analysis.get(\"sell_decisions\", 0)}')
        print(f'Hold Decisions:   {analysis.get(\"hold_decisions\", 0)}')
        print(f'Avg Confidence:   {analysis.get(\"avg_confidence\", 0):.2f}%')
    
    print('\nFor detailed results, please examine the JSON output file.')
except Exception as e:
    print(f'Error analyzing results file: {str(e)}')
    sys.exit(1)
"

echo "======================================"
echo "Full-scale backtest completed!"
echo "======================================"
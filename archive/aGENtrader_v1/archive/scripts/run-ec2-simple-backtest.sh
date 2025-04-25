#!/bin/bash
# Script to run a simplified backtest on EC2

# Default values
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-01"
END_DATE="2025-03-10"
ANALYSIS_TIMEOUT=120
RISK_PER_TRADE=0.02
INITIAL_BALANCE=10000

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
    --analysis_timeout)
      ANALYSIS_TIMEOUT="$2"
      shift 2
      ;;
    --risk_per_trade)
      RISK_PER_TRADE="$2"
      shift 2
      ;;
    --initial_balance)
      INITIAL_BALANCE="$2"
      shift 2
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

# Temporary file for SSH key with proper formatting
KEY_FILE=$(mktemp)
echo "Creating properly formatted SSH key..."
echo -e "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_FILE"
echo "$EC2_SSH_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY-----//g' | sed 's/-----END RSA PRIVATE KEY-----//g' | tr -d '\n' | fold -w 64 >> "$KEY_FILE"
echo -e "\n-----END RSA PRIVATE KEY-----" >> "$KEY_FILE"
chmod 600 "$KEY_FILE"

# Create output file name
OUTPUT_DIR="data/backtest_results"
OUTPUT_FILE="${OUTPUT_DIR}/ec2_backtest_${SYMBOL}_${INTERVAL}_$(date +%Y%m%d_%H%M%S).json"

# Build the command with all arguments
BACKTEST_CMD="cd /home/ec2-user/aGENtrader && python3 run_backtest_with_local_llm.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --analysis_timeout $ANALYSIS_TIMEOUT --risk_per_trade $RISK_PER_TRADE --initial_balance $INITIAL_BALANCE --output_dir $OUTPUT_DIR"

echo "======================================"
echo "Running Simplified Backtest on EC2"
echo "======================================"
echo "Symbol:          $SYMBOL"
echo "Interval:        $INTERVAL"
echo "Date Range:      $START_DATE to $END_DATE"
echo "Initial Balance: $INITIAL_BALANCE"
echo "Analysis Timeout: $ANALYSIS_TIMEOUT seconds"
echo "Risk per Trade:  $RISK_PER_TRADE"
echo "Output Directory: $OUTPUT_DIR"
echo "======================================"
echo "Testing SSH connection..."

if ! ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "echo Connected successfully"; then
  echo "Error: Failed to connect to EC2 instance"
  cat "$KEY_FILE" | head -1
  cat "$KEY_FILE" | tail -1
  wc -l "$KEY_FILE"
  rm "$KEY_FILE"
  exit 1
fi

echo "Connection successful!"
echo "======================================"
echo "Creating output directory on EC2..."
ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "mkdir -p /home/ec2-user/aGENtrader/$OUTPUT_DIR"

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
echo "Backtest completed successfully on EC2!"
echo "Results are stored in the $OUTPUT_DIR directory on EC2."
echo "======================================"

# Ask user if they want to retrieve the results
read -p "Do you want to download the results from EC2? (y/n): " download_results

if [[ $download_results == [yY] || $download_results == [yY][eE][sS] ]]; then
  echo "======================================"
  echo "Creating properly formatted SSH key for SCP..."
  SCP_KEY_FILE=$(mktemp)
  echo -e "-----BEGIN RSA PRIVATE KEY-----" > "$SCP_KEY_FILE"
  echo "$EC2_SSH_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY-----//g' | sed 's/-----END RSA PRIVATE KEY-----//g' | tr -d '\n' | fold -w 64 >> "$SCP_KEY_FILE"
  echo -e "\n-----END RSA PRIVATE KEY-----" >> "$SCP_KEY_FILE"
  chmod 600 "$SCP_KEY_FILE"

  echo "======================================"
  echo "Creating local output directory..."
  mkdir -p "$OUTPUT_DIR"

  echo "======================================"
  echo "Finding latest result file..."
  LATEST_FILE=$(ssh -o StrictHostKeyChecking=no -i "$SCP_KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "ls -t /home/ec2-user/aGENtrader/$OUTPUT_DIR/ec2_backtest_${SYMBOL}_${INTERVAL}_*.json | head -1")

  if [ -z "$LATEST_FILE" ]; then
    echo "Error: Could not find any result files on EC2"
    rm "$SCP_KEY_FILE"
    exit 1
  fi

  echo "Found latest result file: $LATEST_FILE"
  LOCAL_FILE=$(basename "$LATEST_FILE")

  echo "======================================"
  echo "Downloading result file from EC2..."
  scp -o StrictHostKeyChecking=no -i "$SCP_KEY_FILE" ec2-user@"$EC2_PUBLIC_IP":"$LATEST_FILE" "$OUTPUT_DIR/$LOCAL_FILE"
  SCP_EXIT_CODE=$?

  # Clean up the temporary key file
  rm "$SCP_KEY_FILE"

  if [ $SCP_EXIT_CODE -ne 0 ]; then
    echo "Error: Failed to download results file with exit code $SCP_EXIT_CODE"
    exit $SCP_EXIT_CODE
  fi

  echo "======================================"
  echo "Results downloaded successfully to $OUTPUT_DIR/$LOCAL_FILE"
  echo "======================================"
  echo "Generating summary..."

  # Analyze the results file
  python -c "
  import json
  import sys

  try:
      with open('$OUTPUT_DIR/$LOCAL_FILE', 'r') as f:
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
      
      print('\nFor detailed results, please examine the JSON output file.')
  except Exception as e:
      print(f'Error analyzing results file: {str(e)}')
      sys.exit(1)
  "
fi

echo "======================================"
echo "Simplified backtest process completed!"
echo "======================================"

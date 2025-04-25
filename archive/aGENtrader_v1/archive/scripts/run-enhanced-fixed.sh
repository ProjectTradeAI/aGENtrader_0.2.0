#!/bin/bash
# Script to run enhanced backtest with proper parameter handling

# Setup SSH key
KEY_PATH="/tmp/enhanced_key.pem"
echo "Setting up SSH key..."
echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Get parameters
SYMBOL=${1:-BTCUSDT}
INTERVAL=${2:-1h}
START_DATE=${3:-2025-03-01}
END_DATE=${4:-2025-03-02}
BALANCE=${5:-10000}
RISK=${6:-0.02}
TAKE_PROFIT=${7:-10.0}
STOP_LOSS=${8:-5.0}

echo "Running enhanced backtest with parameters:"
echo "Symbol: $SYMBOL"
echo "Interval: $INTERVAL"
echo "Date Range: $START_DATE to $END_DATE"
echo "Balance: $BALANCE"
echo "Risk: $RISK"
echo "Take Profit: $TAKE_PROFIT%"
echo "Stop Loss: $STOP_LOSS%"
echo

# Run the wrapper
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 run_enhanced_wrapper.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $BALANCE --risk_per_trade $RISK --take_profit_pct $TAKE_PROFIT --stop_loss_pct $STOP_LOSS --use_local_llm"

echo
echo "Checking latest results..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && ls -la results/ | tail -n 5"

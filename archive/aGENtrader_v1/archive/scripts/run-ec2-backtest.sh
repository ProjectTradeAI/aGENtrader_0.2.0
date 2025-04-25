#!/bin/bash
# Script to run backtests on EC2 with the original key

# Configuration
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
KEY_PATH="/tmp/original_ec2_key.pem"
EC2_DIR="/home/ec2-user/aGENtrader"

# Create the key file if it doesn't exist
if [ ! -f "$KEY_PATH" ]; then
    echo "Creating key file from ORIGINAL_EC2_KEY secret..."
    echo "$ORIGINAL_EC2_KEY" > "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

# Function to display help
function show_help() {
    echo "EC2 Backtest Runner"
    echo "==================="
    echo "This script runs backtests on your EC2 instance."
    echo
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  --help               Display this help message"
    echo "  --type TYPE          Type of backtest (simplified, enhanced, full-scale)"
    echo "  --symbol SYMBOL      Trading symbol (default: BTCUSDT)"
    echo "  --interval INTERVAL  Trading interval (default: 1h)"
    echo "  --start DATE         Start date (format: YYYY-MM-DD, default: 2025-03-01)"
    echo "  --end DATE           End date (format: YYYY-MM-DD, default: 2025-04-01)"
    echo "  --balance AMOUNT     Initial balance (default: 10000)"
    echo "  --risk PERCENTAGE    Risk percentage as decimal (default: 0.02)"
    echo "  --local-llm          Use local Mixtral model instead of OpenAI"
    echo
    echo "Examples:"
    echo "  $0 --type simplified --symbol BTCUSDT --interval 1h --local-llm"
    echo "  $0 --type enhanced --symbol ETHUSDT --interval 4h --start 2025-02-01 --end 2025-03-01"
    echo "  $0 --type full-scale --risk 0.03 --balance 50000"
}

# Default values
TYPE="simplified"
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-01"
END_DATE="2025-04-01"
BALANCE="10000"
RISK="0.02"
LOCAL_LLM=""

# Process command line arguments
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

# Validate backtest type
if [[ "$TYPE" != "simplified" && "$TYPE" != "enhanced" && "$TYPE" != "full-scale" ]]; then
    echo "Error: Invalid backtest type. Must be 'simplified', 'enhanced', or 'full-scale'."
    exit 1
fi

# Construct the backtest command
if [[ "$TYPE" == "simplified" ]]; then
    # Simplified backtest uses position_size instead of balance/risk
    POSITION_SIZE="50"
    BACKTEST_CMD="./ec2-multi-agent-backtest.sh --type $TYPE --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --position_size $POSITION_SIZE $LOCAL_LLM"
else
    # Enhanced and full-scale use balance and risk
    BACKTEST_CMD="./ec2-multi-agent-backtest.sh --type $TYPE --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --balance $BALANCE --risk $RISK --decision_interval 2 --min_confidence 75 $LOCAL_LLM"
fi

# Run the backtest
echo "==================================================="
echo "  Running $TYPE backtest on EC2"
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

echo "Executing backtest on EC2..."
echo "---------------------------------------------------"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && $BACKTEST_CMD"
RESULT=$?
echo "---------------------------------------------------"

if [ $RESULT -eq 0 ]; then
    echo "✅ Backtest completed successfully!"
else
    echo "❌ Backtest failed with error code $RESULT"
fi

echo
echo "To view results, run:"
echo "./connect-original-key.sh \"cd $EC2_DIR && ls -la results/\""

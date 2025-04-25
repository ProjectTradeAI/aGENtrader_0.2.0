#!/bin/bash
# Data Integrity Wrapper for Smart Backtest Runner
# This script ensures data integrity is applied before running any backtests

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# First apply the data integrity fix - make sure it can be found from any directory
cd ~/aGENtrader
python3 direct_fix.py

# Determine script to run
if [ -z "$1" ]; then
    echo "Error: You must provide the path to your smart-backtest-runner.sh"
    echo "Usage: $0 path/to/smart-backtest-runner.sh [additional args]"
    exit 1
fi

BACKTEST_SCRIPT="$1"
shift  # Remove the first argument (the script path)

# Run the original script with remaining arguments
echo "Running: $BACKTEST_SCRIPT $@"
exec "$BACKTEST_SCRIPT" "$@"

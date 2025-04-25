#!/usr/bin/env python3
"""
Script to create a patched wrapper for smart-backtest-runner.sh
"""

import os
import sys

# Create the wrapper script
wrapper_script = """#!/bin/bash
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
"""

def main():
    # Create the wrapper script
    with open("smart_backtest_wrapper.sh", "w") as f:
        f.write(wrapper_script)
    
    # Make it executable
    os.chmod("smart_backtest_wrapper.sh", 0o755)
    
    print("=" * 80)
    print("Created smart_backtest_wrapper.sh")
    print("=" * 80)
    print("\nTo use this wrapper:")
    print("1. Upload it to your EC2 instance")
    print("2. Run your backtest with:")
    print("   ./smart_backtest_wrapper.sh /path/to/your/smart-backtest-runner.sh [args]")
    print("\nThis ensures data integrity is applied before running any backtests.")

if __name__ == "__main__":
    main()

#!/bin/bash
# Script to run aGENtrader v2 in extended test mode

# Set the directory where the script is located as the working directory
cd "$(dirname "$0")"

# Ensure required directories exist
mkdir -p logs reports trades config

# Export environment variables if needed 
# Use the environment variables from .env file
source .env

echo "$(date): Starting aGENtrader v2 in extended test mode for 24-hour testing..."

# Run the application with test parameters
python aGENtrader_v2/run.py --mode test --symbol BTC/USDT --interval 1h --duration 24h > logs/extended_test_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# Save the process ID for later termination if needed
echo $! > test_run.pid

echo "Test initiated with PID $(cat test_run.pid)"
echo "Logs will be saved to logs/extended_test_*.log"
echo "To stop the test before completion, run: kill $(cat test_run.pid)"
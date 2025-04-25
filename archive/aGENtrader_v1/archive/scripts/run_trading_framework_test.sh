#!/bin/bash
# Run the trading agent framework test

# Ensure logs directory exists
mkdir -p data/logs/framework_tests

# Parse arguments
mode="sequential"
symbol="BTCUSDT"

while getopts ":m:s:" opt; do
  case $opt in
    m) mode="$OPTARG"
      ;;
    s) symbol="$OPTARG"
      ;;
    \?) echo "Invalid option -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Validate mode
if [[ "$mode" != "sequential" && "$mode" != "group" && "$mode" != "both" ]]; then
    echo "Invalid mode: $mode. Valid options are: sequential, group, both"
    exit 1
fi

# Run the appropriate test
echo "Running trading agent framework test with mode: $mode, symbol: $symbol"
python test_trading_agent_framework.py --mode $mode --symbol $symbol

# Display results location
echo ""
echo "Test completed. Check logs in data/logs/framework_tests directory."

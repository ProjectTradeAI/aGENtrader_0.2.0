#!/bin/bash
# Run the structured decision agent test

# Ensure logs directory exists
mkdir -p data/logs/structured_decisions

# Check if an argument was provided
if [ $# -eq 1 ]; then
    symbol=$1
    echo "Running structured decision test for $symbol"
    python test_structured_decision_agent.py --symbol $symbol
else
    echo "Running structured decision test with default symbol (BTCUSDT)"
    python test_structured_decision_agent.py
fi

# Display results location
echo ""
echo "Test completed. Check logs in data/logs/structured_decisions directory."

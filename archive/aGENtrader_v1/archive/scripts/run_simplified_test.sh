#!/bin/bash

# Ensure required directories exist
mkdir -p data/logs/decision_sessions

# Set the symbol from command line argument or use default
SYMBOL=${1:-BTCUSDT}

# Run the simplified collaborative decision test with a timeout
echo "Running simplified collaborative decision test for $SYMBOL..."
timeout 300 python test_simplified_collaborative.py $SYMBOL
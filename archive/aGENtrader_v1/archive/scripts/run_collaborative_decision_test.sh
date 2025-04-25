#!/bin/bash

# Ensure required directories exist
mkdir -p data/logs/decision_sessions data/logs/agent_conversations

# Set the symbol from command line argument or use default
SYMBOL=${1:-BTCUSDT}

# Run the collaborative decision test
echo "Running collaborative decision test for $SYMBOL..."
python test_collaborative_decision.py $SYMBOL
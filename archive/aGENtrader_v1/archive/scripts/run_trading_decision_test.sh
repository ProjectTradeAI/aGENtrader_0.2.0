#!/bin/bash

# Ensure required directories exist
mkdir -p data/logs/decision_sessions data/logs/agent_conversations

# Run the trading decision test
python test_trading_decision.py
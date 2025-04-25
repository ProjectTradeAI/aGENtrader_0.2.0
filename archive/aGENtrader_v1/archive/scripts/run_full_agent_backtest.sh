#!/bin/bash

# Set Python path to include the current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "PYTHONPATH set to: $PYTHONPATH"

# Run the enhanced backtest
echo "Starting enhanced multi-agent backtest..."
python3 full_agent_backtest.py \
  --symbol "BTCUSDT" \
  --interval "1h" \
  --start_date "2025-03-20" \
  --end_date "2025-03-22" \
  --initial_balance "10000"

# Display the agent communications log
echo -e "\nRetrieving agent communications log..."
LATEST_LOG=$(find data/logs -name "agent_communications_*.log" | sort -r | head -n 1)

if [ -n "$LATEST_LOG" ]; then
  echo "Agent communications log: $LATEST_LOG"
  echo "Log content:"
  echo "====================================================="
  cat "$LATEST_LOG"
  echo "====================================================="
else
  echo "No agent communications log found."
fi

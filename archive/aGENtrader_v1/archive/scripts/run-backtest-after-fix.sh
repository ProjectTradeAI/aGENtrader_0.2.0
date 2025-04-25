#!/bin/bash
# Run backtest after applying direct agent fix

# Set Python path to include the current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "PYTHONPATH set to: $PYTHONPATH"

# Create needed directories
mkdir -p data/logs results

# Run the direct agent fix and save the summary
echo "Running direct agent fix..."
python3 direct-agent-fix.py | tee direct-fix-summary.txt

# If successful, run a real backtest with proper parameters
echo "Running backtest with full agent communications..."
python3 -m backtesting.core.authentic_backtest \
  --symbol "$1" \
  --interval "$2" \
  --start_date "$3" \
  --end_date "$4" \
  --initial_balance "$5" \
  --output_dir results | tee agent-backtest.log

# Check if agent communications log exists
echo "Checking for agent communications logs..."
LATEST_LOG=$(find data/logs -name "direct_agent_comms_*.log" | sort -r | head -n 1)

if [ -n "$LATEST_LOG" ]; then
  echo "Found agent communications log: $LATEST_LOG"
  echo "Agent communications excerpt (first 20 lines):"
  head -n 20 "$LATEST_LOG"
  echo "Agent communications excerpt (last 20 lines):"
  tail -n 20 "$LATEST_LOG"
  echo "(... more content in $LATEST_LOG ...)"
else
  echo "No agent communications log found."
fi

# Check for result files
echo "Checking for result files..."
LATEST_RESULT=$(find results -name "*backtest*.json" | sort -r | head -n 1)

if [ -n "$LATEST_RESULT" ]; then
  echo "Found result file: $LATEST_RESULT"
  echo "Backtest results summary:"
  cat "$LATEST_RESULT" | python -m json.tool
else
  echo "No result file found."
fi

echo "Done."

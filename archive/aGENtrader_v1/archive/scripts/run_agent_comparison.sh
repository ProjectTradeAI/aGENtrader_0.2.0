#!/bin/bash
# Agent Comparison Test Runner
# This script runs the agent comparison backtest with different options

# Default values
SYMBOL="BTCUSDT"
DAYS=7
INTERVAL="1h"
CAPITAL=10000.0
POSITION_SIZE=0.5
CONFIDENCE=55.0
MAX_TRADES=""
VERBOSE=""
SIMPLE_ONLY=""
MULTI_ONLY=""
SIMULATE_API=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --symbol=*)
      SYMBOL="${1#*=}"
      ;;
    --days=*)
      DAYS="${1#*=}"
      ;;
    --start=*)
      START_DATE="${1#*=}"
      ;;
    --end=*)
      END_DATE="${1#*=}"
      ;;
    --interval=*)
      INTERVAL="${1#*=}"
      ;;
    --capital=*)
      CAPITAL="${1#*=}"
      ;;
    --size=*)
      POSITION_SIZE="${1#*=}"
      ;;
    --confidence=*)
      CONFIDENCE="${1#*=}"
      ;;
    --max-trades=*)
      MAX_TRADES="--max_trades ${1#*=}"
      ;;
    --verbose)
      VERBOSE="--verbose"
      ;;
    --simple-only)
      SIMPLE_ONLY="--use_simple_only"
      ;;
    --multi-only)
      MULTI_ONLY="--use_multi_only"
      ;;
    --simulate-api)
      SIMULATE_API="--simulate_api"
      ;;
    --short)
      # Shortcut for quick test
      DAYS=3
      MAX_TRADES="--max_trades 3"
      ;;
    --help)
      echo "Agent Comparison Backtest Runner"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --symbol=SYMBOL      Trading symbol (default: BTCUSDT)"
      echo "  --days=DAYS          Number of days to backtest (default: 7)"
      echo "  --start=DATE         Start date (YYYY-MM-DD)"
      echo "  --end=DATE           End date (YYYY-MM-DD)"
      echo "  --interval=INTERVAL  Data interval (default: 1h)"
      echo "  --capital=AMOUNT     Initial capital (default: 10000.0)"
      echo "  --size=FRACTION      Position size as fraction (default: 0.5)"
      echo "  --confidence=VALUE   Confidence threshold (default: 55.0)"
      echo "  --max-trades=NUM     Maximum number of trades"
      echo "  --verbose            Enable verbose output"
      echo "  --simple-only        Only run simple session"
      echo "  --multi-only         Only run multi-agent session"
      echo "  --simulate-api       Use simulated API responses"
      echo "  --short              Shortcut for quick test (3 days, 3 trades max)"
      echo "  --help               Show this help"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help to see available options"
      exit 1
      ;;
  esac
  shift
done

# Build the command
CMD="python run_agent_comparison_test.py --symbol $SYMBOL --interval $INTERVAL --capital $CAPITAL --position_size $POSITION_SIZE --confidence_threshold $CONFIDENCE"

# Add date range
if [ -n "$START_DATE" ] && [ -n "$END_DATE" ]; then
  CMD="$CMD --start_date $START_DATE --end_date $END_DATE"
else
  CMD="$CMD --days $DAYS"
fi

# Add additional options
if [ -n "$MAX_TRADES" ]; then
  CMD="$CMD $MAX_TRADES"
fi

if [ -n "$VERBOSE" ]; then
  CMD="$CMD $VERBOSE"
fi

if [ -n "$SIMPLE_ONLY" ]; then
  CMD="$CMD $SIMPLE_ONLY"
fi

if [ -n "$MULTI_ONLY" ]; then
  CMD="$CMD $MULTI_ONLY"
fi

if [ -n "$SIMULATE_API" ]; then
  CMD="$CMD $SIMULATE_API"
fi

# Print the command
echo "Running: $CMD"

# Run the command
eval $CMD
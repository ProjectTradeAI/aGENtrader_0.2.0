#!/bin/bash
# Run Alpaca API tests

# Default parameters
TEST_TYPE="basic"
SYMBOL="BTCUSD"
INTERVAL="1h"
LIMIT=10
FORMAT="text"

# Parse command line options
while [[ $# -gt 0 ]]; do
  case $1 in
    --type)
      TEST_TYPE="$2"
      shift 2
      ;;
    --symbol)
      SYMBOL="$2"
      shift 2
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    --format)
      FORMAT="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--type basic|query|latest|stats|autogen] [--symbol BTCUSD] [--interval 1h] [--limit 10] [--format text|json|markdown]"
      echo
      echo "Options:"
      echo "  --type    Test type (basic, query, latest, stats, autogen) [default: basic]"
      echo "  --symbol  Trading symbol [default: BTCUSD]"
      echo "  --interval Time interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d) [default: 1h]"
      echo "  --limit   Number of data points to retrieve [default: 10]"
      echo "  --format  Output format (text, json, markdown) [default: text]"
      echo "  --help    Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Check if Alpaca API keys are set
if [ -z "$ALPACA_API_KEY" ] || [ -z "$ALPACA_API_SECRET" ]; then
  echo "Alpaca API keys not found in environment variables."
  echo "Setting up Alpaca API credentials..."
  python scripts/set_alpaca_credentials.py
  
  # Exit if credentials setup failed
  if [ $? -ne 0 ]; then
    echo "Failed to set up Alpaca API credentials."
    exit 1
  fi
fi

# Run the specified test
case $TEST_TYPE in
  basic)
    echo "Running basic Alpaca API test..."
    python scripts/test_alpaca_api.py --action status
    ;;
  query)
    echo "Running Alpaca API query test..."
    python scripts/test_alpaca_api.py --action query --symbol $SYMBOL --interval $INTERVAL --limit $LIMIT --format $FORMAT
    ;;
  latest)
    echo "Running Alpaca API latest price test..."
    python scripts/test_alpaca_api.py --action latest --symbol $SYMBOL --format $FORMAT
    ;;
  stats)
    echo "Running Alpaca API statistics test..."
    python scripts/test_alpaca_api.py --action stats --symbol $SYMBOL --interval $INTERVAL --format $FORMAT
    ;;
  autogen)
    echo "Running Alpaca API AutoGen integration test..."
    python scripts/alpaca_integration_test.py
    ;;
  *)
    echo "Unknown test type: $TEST_TYPE"
    echo "Use --help for usage information"
    exit 1
    ;;
esac

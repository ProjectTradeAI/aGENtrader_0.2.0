#!/bin/bash
# Run all agent tests

# Ensure necessary directories exist
mkdir -p data/logs/structured_decisions
mkdir -p data/logs/framework_tests

# Default options
symbol="BTCUSDT"
testtype="all"
mode="sequential"

# Display usage information
function show_usage {
  echo "Usage: $0 [OPTIONS]"
  echo "Run agent-based trading decision tests"
  echo ""
  echo "Options:"
  echo "  -s SYMBOL    Trading symbol to test (default: BTCUSDT)"
  echo "  -t TYPE      Test type: structured, framework, all (default: all)"
  echo "  -m MODE      Framework test mode: sequential, group, both (default: sequential)"
  echo "  -h           Display this help message"
}

# Parse command line options
while getopts "s:t:m:h" opt; do
  case $opt in
    s) symbol="$OPTARG"
      ;;
    t) testtype="$OPTARG"
      ;;
    m) mode="$OPTARG"
      ;;
    h) show_usage
       exit 0
      ;;
    \?) echo "Invalid option -$OPTARG" >&2
       show_usage
       exit 1
      ;;
  esac
done

# Validate test type
if [[ "$testtype" != "structured" && "$testtype" != "framework" && "$testtype" != "all" ]]; then
    echo "Invalid test type: $testtype. Valid options are: structured, framework, all"
    exit 1
fi

# Validate framework mode
if [[ "$mode" != "sequential" && "$mode" != "group" && "$mode" != "both" ]]; then
    echo "Invalid framework mode: $mode. Valid options are: sequential, group, both"
    exit 1
fi

# Display header
echo "===================================================================="
echo "               Trading Agent Tests - $(date)"
echo "===================================================================="
echo "Symbol: $symbol"
echo "Test type: $testtype"
if [[ "$testtype" == "framework" || "$testtype" == "all" ]]; then
    echo "Framework mode: $mode"
fi
echo "===================================================================="
echo ""

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OpenAI API key not found in environment variables."
    echo "Please set the OPENAI_API_KEY environment variable and try again."
    exit 1
fi

# Run structured decision test if requested
if [[ "$testtype" == "structured" || "$testtype" == "all" ]]; then
    echo "Running structured decision agent test for $symbol..."
    python test_structured_decision_agent.py --symbol $symbol
    echo ""
fi

# Run trading framework test if requested
if [[ "$testtype" == "framework" || "$testtype" == "all" ]]; then
    echo "Running trading agent framework test for $symbol with mode $mode..."
    python test_trading_agent_framework.py --mode $mode --symbol $symbol
    echo ""
fi

# Display completion message
echo "===================================================================="
echo "                    All tests completed"
echo "===================================================================="
if [[ "$testtype" == "structured" || "$testtype" == "all" ]]; then
    echo "Structured decision logs: data/logs/structured_decisions"
fi
if [[ "$testtype" == "framework" || "$testtype" == "all" ]]; then
    echo "Framework test logs: data/logs/framework_tests"
fi
echo "===================================================================="

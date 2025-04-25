#!/bin/bash

# Paper Trading Test Runner
# Runs paper trading tests with the multi-agent trading system

# Set up environment
echo "Setting up environment..."
mkdir -p data/logs/paper_trading_tests
mkdir -p data/paper_trading

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY environment variable is not set.${NC}"
    echo "Please set the OPENAI_API_KEY environment variable and try again."
    exit 1
fi

# Function to run a test and check its result
run_test() {
    test_name=$1
    test_script=$2
    
    echo -e "\n${YELLOW}Running $test_name...${NC}"
    echo "=========================================================="
    
    start_time=$(date +%s)
    python "$test_script" $3 $4 $5
    exit_code=$?
    end_time=$(date +%s)
    
    duration=$((end_time - start_time))
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}$test_name completed successfully in $duration seconds.${NC}"
        return 0
    else
        echo -e "${RED}$test_name failed with exit code $exit_code after $duration seconds.${NC}"
        return 1
    fi
}

# Parse command line arguments
SYMBOL="BTCUSDT"
RUN_ALL=true
RUN_BASIC=false
RUN_AGENT=false
RUN_INTEGRATION=false
RUN_EXECUTION=false
RUN_SIMULATION=false

# Process command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --symbol)
            SYMBOL="$2"
            shift 2
            ;;
        --basic)
            RUN_ALL=false
            RUN_BASIC=true
            shift
            ;;
        --agent)
            RUN_ALL=false
            RUN_AGENT=true
            shift
            ;;
        --integration)
            RUN_ALL=false
            RUN_INTEGRATION=true
            shift
            ;;
        --execution)
            RUN_ALL=false
            RUN_EXECUTION=true
            shift
            ;;
        --simulation)
            RUN_ALL=false
            RUN_SIMULATION=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}Paper Trading Tests${NC}"
echo "Symbol: $SYMBOL"
echo "=========================================================="

# Run the selected tests
SUCCESS=true

if [ "$RUN_ALL" = true ] || [ "$RUN_BASIC" = true ]; then
    run_test "Basic Paper Trading Test" "test_paper_trading.py"
    if [ $? -ne 0 ]; then
        SUCCESS=false
    fi
fi

if [ "$RUN_ALL" = true ] || [ "$RUN_AGENT" = true ]; then
    run_test "Paper Trading with Agent Decisions" "test_paper_trading.py" "--agent" "--symbol" "$SYMBOL"
    if [ $? -ne 0 ]; then
        SUCCESS=false
    fi
fi

if [ "$RUN_ALL" = true ] || [ "$RUN_INTEGRATION" = true ]; then
    run_test "Paper Trading Integration Test" "test_paper_trading.py" "--integration" "--symbol" "$SYMBOL"
    if [ $? -ne 0 ]; then
        SUCCESS=false
    fi
fi

if [ "$RUN_ALL" = true ] || [ "$RUN_EXECUTION" = true ]; then
    run_test "Trading with Execution Test" "test_trading_with_execution.py" "--symbol" "$SYMBOL"
    if [ $? -ne 0 ]; then
        SUCCESS=false
    fi
fi

if [ "$RUN_ALL" = true ] || [ "$RUN_SIMULATION" = true ]; then
    run_test "Paper Trading Simulation" "run_paper_trading_simulation.py" "--symbol" "$SYMBOL" "--cycles" "2"
    if [ $? -ne 0 ]; then
        SUCCESS=false
    fi
fi

# Display summary
echo -e "\n${YELLOW}Test Summary${NC}"
echo "=========================================================="

if [ "$SUCCESS" = true ]; then
    echo -e "${GREEN}All tests completed successfully!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please check the logs for details.${NC}"
    exit 1
fi
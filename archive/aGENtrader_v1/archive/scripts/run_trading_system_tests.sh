#!/bin/bash
# Trading System Test Runner Script

# Set default values
TEST_TYPE="all"
SYMBOL="BTCUSDT"
TIMEOUT=300
LOG_DIR="data/logs/current_tests"

# Display help
show_help() {
    echo "Trading System Test Runner"
    echo ""
    echo "Usage: ./run_trading_system_tests.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --test TYPE     Test type to run (single, multi, workflow, all)"
    echo "  -s, --symbol SYM    Trading symbol to use (default: BTCUSDT)"
    echo "  -o, --timeout SEC   Timeout in seconds (default: 300)"
    echo "  -l, --log-dir DIR   Directory for logs (default: data/logs/current_tests)"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_trading_system_tests.sh -t single -s ETHUSDT"
    echo "  ./run_trading_system_tests.sh -t workflow -o 600"
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--test)
            TEST_TYPE="$2"
            shift 2
            ;;
        -s|--symbol)
            SYMBOL="$2"
            shift 2
            ;;
        -o|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -l|--log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate test type
if [[ ! "$TEST_TYPE" =~ ^(single|multi|workflow|all)$ ]]; then
    echo "Error: Invalid test type '$TEST_TYPE'"
    echo "Valid types: single, multi, workflow, all"
    exit 1
fi

# Ensure the log directory exists
mkdir -p "$LOG_DIR"

# Print test configuration
echo "=========================================================="
echo "  Trading System Test Configuration"
echo "=========================================================="
echo "  Test type:   $TEST_TYPE"
echo "  Symbol:      $SYMBOL"
echo "  Timeout:     $TIMEOUT seconds"
echo "  Log dir:     $LOG_DIR"
echo "=========================================================="
echo ""

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set."
    echo "Please set the OPENAI_API_KEY environment variable to run the tests."
    exit 1
fi

# Define timestamp for log files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOGFILE="${LOG_DIR}/test_run_${TIMESTAMP}.log"

# Run the test
echo "Starting test at $(date)..."
echo "Logs will be saved to $LOGFILE"
echo ""

python run_trading_tests.py --test "$TEST_TYPE" --symbol "$SYMBOL" --timeout "$TIMEOUT" --log-dir "$LOG_DIR" 2>&1 | tee -a "$LOGFILE"

# Check the exit code
EXIT_CODE=${PIPESTATUS[0]}
if [ $EXIT_CODE -eq 0 ]; then
    echo "Tests completed successfully!"
else
    echo "Tests failed with exit code $EXIT_CODE"
fi

echo "See $LOGFILE for details"
exit $EXIT_CODE
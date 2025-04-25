#!/bin/bash

# Run Replit-Optimized Tests
# This script runs tests optimized for the Replit environment

# Set default variables
SYMBOL="BTCUSDT"
TEST_TYPE="single"
LOG_DIR="data/logs/replit_tests"
MAX_TURNS=3

# Display help message
show_help() {
    echo "Usage: ./run_replit_tests.sh [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help               Show this help message"
    echo "  -t, --test-type TYPE     Test type to run: single, simplified (default: single)"
    echo "  -s, --symbol SYMBOL      Trading symbol to use (default: BTCUSDT)"
    echo "  -l, --log-dir DIR        Directory to store logs (default: data/logs/replit_tests)"
    echo "  -m, --max-turns NUM      Maximum turns for agent conversations (default: 3)"
    echo
    echo "Examples:"
    echo "  ./run_replit_tests.sh                      # Run single agent test with default params"
    echo "  ./run_replit_tests.sh -t simplified        # Run simplified collaborative test"
    echo "  ./run_replit_tests.sh -m 2                 # Run with max 2 turns to reduce API usage"
    echo
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--test-type)
            TEST_TYPE="$2"
            shift
            shift
            ;;
        -s|--symbol)
            SYMBOL="$2"
            shift
            shift
            ;;
        -l|--log-dir)
            LOG_DIR="$2"
            shift
            shift
            ;;
        -m|--max-turns)
            MAX_TURNS="$2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Verify test type is valid
if [[ "$TEST_TYPE" != "single" && "$TEST_TYPE" != "simplified" ]]; then
    echo "Error: Invalid test type '$TEST_TYPE'"
    echo "Valid test types: single, simplified"
    exit 1
fi

# Create log directory
mkdir -p "$LOG_DIR"

# Display test configuration
echo "============================================================"
echo "Running Replit-Optimized Tests"
echo "============================================================"
echo "Test Type:    $TEST_TYPE"
echo "Symbol:       $SYMBOL"
echo "Log Directory: $LOG_DIR"
echo "Max Turns:    $MAX_TURNS"
echo "Start Time:   $(date)"
echo "============================================================"

# Run the optimized test script
python run_replit_tests.py \
    --test-type "$TEST_TYPE" \
    --symbol "$SYMBOL" \
    --log-dir "$LOG_DIR" \
    --max-turns "$MAX_TURNS"

# Display summary message
echo
echo "============================================================"
echo "Test Execution Completed"
echo "End Time: $(date)"
echo "Check the log directory for detailed results:"
echo "$LOG_DIR"
echo "============================================================"
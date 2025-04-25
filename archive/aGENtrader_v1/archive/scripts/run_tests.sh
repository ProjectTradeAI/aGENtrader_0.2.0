#!/bin/bash

# Run Comprehensive Tests
# This script runs the comprehensive test suite with various options

# Set default variables
SYMBOL="BTCUSDT"
TEST_TYPE="all"
LOG_DIR="data/logs/comprehensive_tests"
MAX_AGENTS=3

# Display help message
show_help() {
    echo "Usage: ./run_tests.sh [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help               Show this help message"
    echo "  -t, --test-type TYPE     Test type to run: single, simplified, collaborative, decision, all (default: all)"
    echo "  -s, --symbol SYMBOL      Trading symbol to use (default: BTCUSDT)"
    echo "  -l, --log-dir DIR        Directory to store logs (default: data/logs/comprehensive_tests)"
    echo "  -m, --max-agents NUM     Maximum number of agents for collaborative tests (default: 3)"
    echo
    echo "Examples:"
    echo "  ./run_tests.sh                            # Run all tests with default symbol"
    echo "  ./run_tests.sh -t single                  # Run only single agent test"
    echo "  ./run_tests.sh -t collaborative -s ETHUSDT # Run collaborative test with ETHUSDT"
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
        -m|--max-agents)
            MAX_AGENTS="$2"
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
if [[ "$TEST_TYPE" != "single" && "$TEST_TYPE" != "simplified" && "$TEST_TYPE" != "collaborative" && "$TEST_TYPE" != "decision" && "$TEST_TYPE" != "all" ]]; then
    echo "Error: Invalid test type '$TEST_TYPE'"
    echo "Valid test types: single, simplified, collaborative, decision, all"
    exit 1
fi

# Create log directory
mkdir -p "$LOG_DIR"

# Display test configuration
echo "============================================================"
echo "Running Comprehensive Trading Agent Tests"
echo "============================================================"
echo "Test Type:    $TEST_TYPE"
echo "Symbol:       $SYMBOL"
echo "Log Directory: $LOG_DIR"
echo "Max Agents:   $MAX_AGENTS"
echo "Start Time:   $(date)"
echo "============================================================"

# Run the test script
python run_comprehensive_tests.py \
    --test-type "$TEST_TYPE" \
    --symbol "$SYMBOL" \
    --log-dir "$LOG_DIR" \
    --max-agents "$MAX_AGENTS"

# Display summary message
echo
echo "============================================================"
echo "Test Execution Completed"
echo "End Time: $(date)"
echo "Check the log directory for detailed results:"
echo "$LOG_DIR"
echo "============================================================"
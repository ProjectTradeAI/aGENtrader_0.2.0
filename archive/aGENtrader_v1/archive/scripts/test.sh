#!/bin/bash

# Consolidated Test Runner
# A user-friendly script to run tests and view results

# Display help message
show_help() {
    echo "Trading System Test Runner"
    echo "=========================="
    echo
    echo "Usage: ./test.sh [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  run            Run a test (default command if omitted)"
    echo "  view           View test results"
    echo "  check          Check test progress"
    echo "  help           Show this help message"
    echo
    echo "Run Options:"
    echo "  --type, -t     Test type: full, replit, offline (default: replit)"
    echo "  --mode, -m     Test mode: single, simplified, collaborative, decision, all (default: single)"
    echo "  --symbol, -s   Trading symbol (default: BTCUSDT)"
    echo "  --turns        Maximum conversation turns (default: 3)"
    echo
    echo "View Options:"
    echo "  --latest, -l   View latest test result"
    echo "  --session, -i  View specific session by ID"
    echo "  --list         List available test sessions"
    echo
    echo "Check Options:"
    echo "  --watch, -w    Watch mode - continuously update"
    echo "  --logs         Show test logs"
    echo "  --results      Show test results"
    echo
    echo "Examples:"
    echo "  ./test.sh run                      # Run default test (replit + single)"
    echo "  ./test.sh run -t full -m all       # Run all comprehensive tests"
    echo "  ./test.sh run -t offline           # Run offline test"
    echo "  ./test.sh view --latest            # View latest test result"
    echo "  ./test.sh check --watch            # Watch test progress"
    echo
}

# Default values
COMMAND="run"
TEST_TYPE="replit"
TEST_MODE="single"
SYMBOL="BTCUSDT"
MAX_TURNS=3
VIEW_LATEST=false
VIEW_SESSION=""
VIEW_LIST=false
CHECK_WATCH=false
CHECK_LOGS=false
CHECK_RESULTS=false

# Parse command
if [[ $# -gt 0 ]]; then
    case "$1" in
        run|view|check|help)
            COMMAND="$1"
            shift
            ;;
    esac
fi

# Show help if requested
if [[ "$COMMAND" == "help" ]]; then
    show_help
    exit 0
fi

# Parse options
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --type|-t)
            TEST_TYPE="$2"
            shift
            shift
            ;;
        --mode|-m)
            TEST_MODE="$2"
            shift
            shift
            ;;
        --symbol|-s)
            SYMBOL="$2"
            shift
            shift
            ;;
        --turns)
            MAX_TURNS="$2"
            shift
            shift
            ;;
        --latest|-l)
            VIEW_LATEST=true
            shift
            ;;
        --session|-i)
            VIEW_SESSION="$2"
            shift
            shift
            ;;
        --list)
            VIEW_LIST=true
            shift
            ;;
        --watch|-w)
            CHECK_WATCH=true
            shift
            ;;
        --logs)
            CHECK_LOGS=true
            shift
            ;;
        --results)
            CHECK_RESULTS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate test type
if [[ "$TEST_TYPE" != "full" && "$TEST_TYPE" != "replit" && "$TEST_TYPE" != "offline" ]]; then
    echo "Error: Invalid test type '$TEST_TYPE'"
    echo "Valid test types: full, replit, offline"
    exit 1
fi

# Validate test mode
if [[ "$TEST_MODE" != "single" && "$TEST_MODE" != "simplified" && "$TEST_MODE" != "collaborative" && "$TEST_MODE" != "decision" && "$TEST_MODE" != "all" ]]; then
    echo "Error: Invalid test mode '$TEST_MODE'"
    echo "Valid test modes: single, simplified, collaborative, decision, all"
    exit 1
fi

# Execute command

if [[ "$COMMAND" == "run" ]]; then
    echo "======================================"
    echo "    TRADING SYSTEM TEST RUNNER"
    echo "======================================"
    echo "Test Type: $TEST_TYPE"
    echo "Test Mode: $TEST_MODE"
    echo "Symbol: $SYMBOL"
    echo "Max Turns: $MAX_TURNS"
    echo "Start Time: $(date)"
    echo "======================================"
    echo
    
    if [[ "$TEST_TYPE" == "full" ]]; then
        # Run comprehensive test
        ./run_tests.sh -t "$TEST_MODE" -s "$SYMBOL" -m "$MAX_TURNS"
    elif [[ "$TEST_TYPE" == "replit" ]]; then
        # Run Replit-optimized test
        if [[ "$TEST_MODE" == "collaborative" || "$TEST_MODE" == "decision" || "$TEST_MODE" == "all" ]]; then
            echo "Warning: For Replit-optimized tests, only 'single' and 'simplified' modes are supported."
            echo "Defaulting to 'simplified' mode."
            TEST_MODE="simplified"
        fi
        ./run_replit_tests.sh -t "$TEST_MODE" -s "$SYMBOL" -m "$MAX_TURNS"
    elif [[ "$TEST_TYPE" == "offline" ]]; then
        # Run offline test
        ./run_offline_test.py
    fi
elif [[ "$COMMAND" == "view" ]]; then
    VIEW_ARGS=""
    
    if [[ "$VIEW_LATEST" == true ]]; then
        VIEW_ARGS="$VIEW_ARGS --latest"
    fi
    
    if [[ -n "$VIEW_SESSION" ]]; then
        VIEW_ARGS="$VIEW_ARGS --session-id $VIEW_SESSION"
    fi
    
    if [[ "$VIEW_LIST" == true ]]; then
        VIEW_ARGS="$VIEW_ARGS --list-only"
    fi
    
    # Determine log directory based on test type
    if [[ "$TEST_TYPE" == "full" ]]; then
        VIEW_ARGS="$VIEW_ARGS --log-dir data/logs/comprehensive_tests"
    elif [[ "$TEST_TYPE" == "replit" ]]; then
        VIEW_ARGS="$VIEW_ARGS --log-dir data/logs/replit_tests"
    elif [[ "$TEST_TYPE" == "offline" ]]; then
        VIEW_ARGS="$VIEW_ARGS --log-dir data/logs/offline_tests"
    fi
    
    # Run view command
    ./view_test_results.py $VIEW_ARGS
elif [[ "$COMMAND" == "check" ]]; then
    CHECK_ARGS=""
    
    if [[ "$CHECK_WATCH" == true ]]; then
        CHECK_ARGS="$CHECK_ARGS --watch"
    fi
    
    if [[ "$CHECK_LOGS" == true ]]; then
        CHECK_ARGS="$CHECK_ARGS --show-logs"
    fi
    
    if [[ "$CHECK_RESULTS" == true ]]; then
        CHECK_ARGS="$CHECK_ARGS --show-results"
    fi
    
    # Determine log directory based on test type
    if [[ "$TEST_TYPE" == "full" ]]; then
        CHECK_ARGS="$CHECK_ARGS --log-dir data/logs/comprehensive_tests"
    elif [[ "$TEST_TYPE" == "replit" ]]; then
        CHECK_ARGS="$CHECK_ARGS --log-dir data/logs/replit_tests"
    elif [[ "$TEST_TYPE" == "offline" ]]; then
        CHECK_ARGS="$CHECK_ARGS --log-dir data/logs/offline_tests"
    fi
    
    # Add test mode as test type filter if specified
    if [[ "$TEST_MODE" != "all" ]]; then
        CHECK_ARGS="$CHECK_ARGS --test-type $TEST_MODE"
    fi
    
    # Run check command
    ./check_test_progress.py $CHECK_ARGS
fi
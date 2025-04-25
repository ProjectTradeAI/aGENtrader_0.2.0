#!/bin/bash
# Multi-Agent Backtesting script for EC2
# This script runs different types of backtests on the EC2 instance

set -e

# Default values
TYPE="simplified"  # simplified, enhanced, or full-scale
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-01"
END_DATE="2025-04-01"
BALANCE=10000
RISK=0.02
DECISION_INTERVAL=2
MIN_CONFIDENCE=75
POSITION_SIZE=50
LLM_TYPE="openai"
OUTPUT_DIR="data/backtest_results"
LOG_DIR="data/logs"
USE_LOCAL_LLM=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --type) TYPE="$2"; shift ;;
        --symbol) SYMBOL="$2"; shift ;;
        --interval) INTERVAL="$2"; shift ;;
        --start_date) START_DATE="$2"; shift ;;
        --end_date) END_DATE="$2"; shift ;;
        --balance) BALANCE="$2"; shift ;;
        --risk) RISK="$2"; shift ;;
        --decision_interval) DECISION_INTERVAL="$2"; shift ;;
        --min_confidence) MIN_CONFIDENCE="$2"; shift ;;
        --position_size) POSITION_SIZE="$2"; shift ;;
        --llm_type) LLM_TYPE="$2"; shift ;;
        --output_dir) OUTPUT_DIR="$2"; shift ;;
        --log_dir) LOG_DIR="$2"; shift ;;
        --local-llm) USE_LOCAL_LLM=true ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --type TYPE                Type of backtest (simplified, enhanced, or full-scale)"
            echo "  --symbol SYMBOL            Trading symbol (e.g. BTCUSDT)"
            echo "  --interval INTERVAL        Trading interval (e.g. 1h, 4h, 1d)"
            echo "  --start_date START_DATE    Start date for backtest (YYYY-MM-DD)"
            echo "  --end_date END_DATE        End date for backtest (YYYY-MM-DD)"
            echo "  --balance BALANCE          Initial balance for backtest"
            echo "  --risk RISK                Risk percentage for backtest"
            echo "  --decision_interval INTERVAL  Decision interval for backtest"
            echo "  --min_confidence MIN_CONF  Minimum confidence for backtest"
            echo "  --position_size SIZE       Position size for simplified test"
            echo "  --llm_type TYPE            LLM type (openai or local)"
            echo "  --output_dir DIR           Output directory"
            echo "  --log_dir DIR              Log directory"
            echo "  --local-llm                Use local LLM (Mixtral)"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Create directories if they don't exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$LOG_DIR"

# Set timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/${TYPE}_backtest_${TIMESTAMP}.log"

# Print configuration
echo "======================================================================"
echo "                    Multi-Agent Backtesting Tool                      "
echo "======================================================================"
echo 
echo "Configuration:"
echo "  Type:                 $TYPE"
echo "  Symbol:               $SYMBOL"
echo "  Interval:             $INTERVAL"
echo "  Period:               $START_DATE to $END_DATE"
echo "  LLM Type:             $LLM_TYPE"
if [ "$USE_LOCAL_LLM" = true ]; then
    echo "  Using Local LLM:      Yes (Mixtral)"
else
    echo "  Using Local LLM:      No (OpenAI)"
fi
echo

# Execute the appropriate backtest script based on the type
if [ "$USE_LOCAL_LLM" = true ]; then
    # Use the local LLM version
    echo "Running backtest with local LLM (Mixtral)..."
    python3 run_backtest_with_local_llm.py \
        --symbol "$SYMBOL" \
        --interval "$INTERVAL" \
        --start_date "$START_DATE" \
        --end_date "$END_DATE" \
        --position_size "$POSITION_SIZE" \
        --output_dir "$OUTPUT_DIR" 2>&1 | tee "$LOG_FILE"
elif [ "$TYPE" == "simplified" ]; then
    echo "Running simplified backtest..."
    python3 run_simplified_backtest.py \
        --symbol "$SYMBOL" \
        --interval "$INTERVAL" \
        --start_date "$START_DATE" \
        --end_date "$END_DATE" \
        --position_size "$POSITION_SIZE" \
        --output_dir "$OUTPUT_DIR" 2>&1 | tee "$LOG_FILE"
elif [ "$TYPE" == "enhanced" ]; then
    echo "Running enhanced backtest..."
    python3 run_enhanced_backtest.py \
        --symbol "$SYMBOL" \
        --interval "$INTERVAL" \
        --start_date "$START_DATE" \
        --end_date "$END_DATE" \
        --balance "$BALANCE" \
        --risk "$RISK" \
        --decision_interval "$DECISION_INTERVAL" \
        --min_confidence "$MIN_CONFIDENCE" \
        --output_dir "$OUTPUT_DIR" 2>&1 | tee "$LOG_FILE"
elif [ "$TYPE" == "full-scale" ]; then
    echo "Running full-scale backtest..."
    python3 run_full_scale_backtest.py \
        --symbol "$SYMBOL" \
        --interval "$INTERVAL" \
        --start_date "$START_DATE" \
        --end_date "$END_DATE" \
        --balance "$BALANCE" \
        --risk "$RISK" \
        --decision_interval "$DECISION_INTERVAL" \
        --min_confidence "$MIN_CONFIDENCE" \
        --output_dir "$OUTPUT_DIR" 2>&1 | tee "$LOG_FILE"
else
    echo "Error: Invalid backtest type specified. Use 'simplified', 'enhanced', or 'full-scale'."
    exit 1
fi

echo
echo "Backtest completed. Results saved to $OUTPUT_DIR"
echo "Log file: $LOG_FILE"

#!/bin/bash
# EC2 Strategy Comparison Script
# This script runs backtests for multiple strategies on EC2 and downloads the results for comparison

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
START_DATE="2025-02-15"
END_DATE="2025-03-15"
INTERVAL="1h"
BALANCE=10000
RISK=0.02
OUTPUT_DIR="ec2_results/comparison_$(date +%Y%m%d_%H%M%S)"

# Show usage
show_usage() {
    echo -e "${BLUE}EC2 Strategy Comparison Tool${NC}"
    echo "=============================="
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --start YYYY-MM-DD    Start date for backtest (default: $START_DATE)"
    echo "  --end YYYY-MM-DD      End date for backtest (default: $END_DATE)"
    echo "  --interval INT        Data interval (1m, 5m, 15m, 1h, 4h, 1d) (default: $INTERVAL)"
    echo "  --balance N           Initial balance (default: $BALANCE)"
    echo "  --risk N              Risk per trade (e.g., 0.02 for 2%) (default: $RISK)"
    echo "  --output DIR          Output directory (default: $OUTPUT_DIR)"
    echo "  --help                Show this help message"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --start)
            START_DATE="$2"
            shift 2
            ;;
        --end)
            END_DATE="$2"
            shift 2
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --balance)
            BALANCE="$2"
            shift 2
            ;;
        --risk)
            RISK="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option - $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Header for summary
echo "# Strategy Comparison Results" > "$OUTPUT_DIR/README.md"
echo "Start Date: $START_DATE" >> "$OUTPUT_DIR/README.md"
echo "End Date: $END_DATE" >> "$OUTPUT_DIR/README.md"
echo "Interval: $INTERVAL" >> "$OUTPUT_DIR/README.md"
echo "Initial Balance: \$$BALANCE" >> "$OUTPUT_DIR/README.md"
echo "Risk Per Trade: ${RISK}%" >> "$OUTPUT_DIR/README.md"
echo "Run Date: $(date)" >> "$OUTPUT_DIR/README.md"
echo "" >> "$OUTPUT_DIR/README.md"

# Define strategies to test
STRATEGIES=("ma_crossover" "rsi" "combined")

echo -e "${BLUE}Starting strategy comparison with the following parameters:${NC}"
echo -e "  Start Date: ${YELLOW}$START_DATE${NC}"
echo -e "  End Date: ${YELLOW}$END_DATE${NC}"
echo -e "  Interval: ${YELLOW}$INTERVAL${NC}"
echo -e "  Initial Balance: ${YELLOW}\$$BALANCE${NC}"
echo -e "  Risk Per Trade: ${YELLOW}${RISK}%${NC}"
echo -e "  Output Directory: ${YELLOW}$OUTPUT_DIR${NC}"
echo ""

# Run backtest for each strategy
for STRATEGY in "${STRATEGIES[@]}"; do
    echo -e "${BLUE}Running backtest for ${YELLOW}$STRATEGY${BLUE} strategy...${NC}"
    
    # Run backtest on EC2
    COMMAND="cd /home/ec2-user/aGENtrader && python3 improved_simplified_test.py --strategy $STRATEGY --start_date $START_DATE --end_date $END_DATE --interval $INTERVAL --initial_balance $BALANCE --risk_per_trade $RISK"
    
    echo -e "${YELLOW}Executing:${NC} $COMMAND"
    ./direct-ssh-command.sh "$COMMAND"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Backtest failed for $STRATEGY strategy${NC}"
        continue
    fi
    
    # Get the latest result file for this strategy
    LATEST_RESULT=$(./direct-ssh-command.sh "cd /home/ec2-user/aGENtrader && ls -t results/BTCUSDT_${STRATEGY}_backtest_*.json | head -1" | grep -v "STEP" | grep -v "Connected" | grep -v "Executing" | tr -d '\r')
    
    if [ -z "$LATEST_RESULT" ]; then
        echo -e "${RED}Error: Could not find result file for $STRATEGY strategy${NC}"
        continue
    fi
    
    echo -e "${GREEN}Found result file: $LATEST_RESULT${NC}"
    
    # Download the result file
    RESULT_FILENAME=$(basename "$LATEST_RESULT")
    echo -e "${BLUE}Downloading result file...${NC}"
    ./direct-ssh-command.sh "cat /home/ec2-user/aGENtrader/$LATEST_RESULT" | grep -v "STEP" | grep -v "Connected" | grep -v "Executing" > "$OUTPUT_DIR/$RESULT_FILENAME"
    
    echo -e "${GREEN}Downloaded to: $OUTPUT_DIR/$RESULT_FILENAME${NC}"
    echo ""
done

# Run analysis on the results
echo -e "${BLUE}Analyzing results...${NC}"
python ec2_results_analyzer.py --dir "$OUTPUT_DIR" --pattern "*.json" --output "$OUTPUT_DIR/summary.md"

# Print a summary table to the console and append to README
echo -e "${GREEN}Strategy Comparison Complete!${NC}"
echo -e "${BLUE}Results saved to:${NC} $OUTPUT_DIR"
echo -e "${BLUE}Summary report:${NC} $OUTPUT_DIR/summary.md"

# Append summary to README
echo "## Summary Results" >> "$OUTPUT_DIR/README.md"
echo "" >> "$OUTPUT_DIR/README.md"
echo '```' >> "$OUTPUT_DIR/README.md"
cat "$OUTPUT_DIR/summary.md" >> "$OUTPUT_DIR/README.md"
echo '```' >> "$OUTPUT_DIR/README.md"

echo -e "${GREEN}Done!${NC}"
exit 0
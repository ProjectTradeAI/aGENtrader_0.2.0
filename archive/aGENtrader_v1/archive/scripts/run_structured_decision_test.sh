#!/bin/bash

# Shell script to run structured trading decision tests with database integration

# Define colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create necessary directories
echo -e "${YELLOW}Creating output directories...${NC}"
mkdir -p data/logs/structured_decisions
mkdir -p data/decisions

# Check database connection
echo -e "${YELLOW}Checking database connection...${NC}"
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}Error: DATABASE_URL environment variable is not set${NC}"
    echo "Please set the DATABASE_URL environment variable and try again"
    echo "Example: export DATABASE_URL=postgresql://username:password@host:port/dbname"
    exit 1
fi

# Parse command line arguments
SYMBOL="BTCUSDT"
OUTPUT_DIR="data/logs/structured_decisions"

while [[ $# -gt 0 ]]; do
    case $1 in
        --symbol)
            SYMBOL="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            shift
            ;;
    esac
done

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Run the test
output_file="${OUTPUT_DIR}/structured_decision_${SYMBOL}_$(date +%Y%m%d_%H%M%S).log"

echo -e "${GREEN}Running structured decision test for ${SYMBOL}...${NC}"
echo -e "${YELLOW}Output will be saved to ${output_file}${NC}"

python test_structured_decision_db.py "$SYMBOL" | tee "$output_file"

# Check the exit code
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}Test completed successfully${NC}"
    echo -e "Log saved to: ${output_file}"
    
    # Extract decision from log file if available
    decision_file=$(grep -o 'Decision saved to: .*\.json' "$output_file" | cut -d' ' -f4)
    
    if [ -n "$decision_file" ] && [ -f "$decision_file" ]; then
        echo -e "${GREEN}Decision file: ${decision_file}${NC}"
        cat "$decision_file"
    fi
else
    echo -e "${RED}Test failed${NC}"
    echo -e "Check the log in ${output_file} for details"
fi
#!/bin/bash

# Run Formatted Trading Decision Test
# This script executes the formatted trading decision test with proper error handling

# Set up colored output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}     Formatted Trading Decision Test Runner         ${NC}"
echo -e "${BLUE}====================================================${NC}"

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OpenAI API key not found in environment variables${NC}"
    echo "Please set the OPENAI_API_KEY environment variable and try again"
    exit 1
fi

# Create output directories
mkdir -p data/logs/structured_decisions
mkdir -p data/decisions

# Determine if we should run multi-symbol test
if [ "$1" == "--multi" ]; then
    echo -e "${GREEN}Running multi-symbol test...${NC}"
    python test_formatted_trading_decision.py --multi
else
    # Get symbol from argument or use default
    SYMBOL=${1:-BTCUSDT}
    echo -e "${GREEN}Running single-symbol test for $SYMBOL...${NC}"
    python test_formatted_trading_decision.py --symbol $SYMBOL
fi

# Check exit status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Test completed successfully.${NC}"
    echo "Results saved to data/decisions/"
else
    echo -e "${RED}Test failed. See error messages above.${NC}"
fi
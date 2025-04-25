#!/bin/bash

# Shell script to run the collaborative market analysis test
# This script handles the environment setup and dependencies

# Define colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create necessary directories
echo -e "${YELLOW}Creating output directories...${NC}"
mkdir -p data/logs/current_tests
mkdir -p data/logs/decisions
mkdir -p data/decisions

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY environment variable is not set${NC}"
    echo "Please set the OPENAI_API_KEY environment variable and try again"
    echo "Example: export OPENAI_API_KEY=your-api-key"
    exit 1
fi

# Check for required Python packages
echo -e "${YELLOW}Checking dependencies...${NC}"
required_packages=("psycopg2" "autogen" "pandas" "numpy")
missing_packages=()

for package in "${required_packages[@]}"; do
    python -c "import $package" 2>/dev/null
    if [ $? -ne 0 ]; then
        missing_packages+=("$package")
    fi
done

# Install missing packages if needed
if [ ${#missing_packages[@]} -ne 0 ]; then
    echo -e "${YELLOW}Installing missing packages: ${missing_packages[*]}${NC}"
    pip install ${missing_packages[*]} --quiet
    
    # Verify installation
    for package in "${missing_packages[@]}"; do
        python -c "import $package" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install $package${NC}"
            exit 1
        fi
    done
    echo -e "${GREEN}Dependencies installed successfully${NC}"
fi

# Parse command line arguments
SYMBOL="BTCUSDT"
OUTPUT_DIR="data/logs/current_tests"

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

# Run the test
echo -e "${GREEN}Running collaborative market analysis test for $SYMBOL${NC}"
echo -e "${YELLOW}Output will be saved to $OUTPUT_DIR${NC}"
echo ""

python run_collaborative_test.py --symbol $SYMBOL --output-dir $OUTPUT_DIR

# Check the exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Test completed successfully${NC}"
    echo "To view results, run: python view_test_results.py --log-dir $OUTPUT_DIR"
else
    echo -e "${RED}Test failed${NC}"
    echo "Check the logs in $OUTPUT_DIR for details"
fi
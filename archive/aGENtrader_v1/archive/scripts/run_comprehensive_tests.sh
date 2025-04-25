#!/bin/bash

# Shell script to run comprehensive tests for the trading system
# This script runs multiple test types and generates a full test report

# Define colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create necessary directories
echo -e "${YELLOW}Creating output directories...${NC}"
mkdir -p data/logs/comprehensive_tests
mkdir -p data/logs/current_tests
mkdir -p data/logs/decisions

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
TESTS="all"
SYMBOL="BTCUSDT"
OUTPUT_DIR="data/logs/comprehensive_tests"

while [[ $# -gt 0 ]]; do
    case $1 in
        --tests)
            TESTS="$2"
            shift 2
            ;;
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

# Run the tests
echo -e "${GREEN}Running comprehensive tests for $SYMBOL${NC}"
echo -e "${YELLOW}Tests to run: $TESTS${NC}"
echo -e "${YELLOW}Output will be saved to $OUTPUT_DIR${NC}"
echo ""

# Create timestamp for this test run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FINAL_OUTPUT_DIR="${OUTPUT_DIR}/${TIMESTAMP}"
mkdir -p "$FINAL_OUTPUT_DIR"

# Run the main test script
python run_comprehensive_tests.py --tests "$TESTS" --symbol "$SYMBOL" --output-dir "$FINAL_OUTPUT_DIR"

# Check the exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Comprehensive tests completed successfully${NC}"
    echo "To view results, run: python view_test_results.py --log-dir $FINAL_OUTPUT_DIR"
else
    echo -e "${RED}Comprehensive tests failed${NC}"
    echo "Check the logs in $FINAL_OUTPUT_DIR for details"
fi

# Generate a summary report
echo -e "${YELLOW}Generating test summary report...${NC}"
echo "# Comprehensive Test Results - $(date)" > "$FINAL_OUTPUT_DIR/summary_report.md"
echo "" >> "$FINAL_OUTPUT_DIR/summary_report.md"
echo "## Test Configuration" >> "$FINAL_OUTPUT_DIR/summary_report.md"
echo "- Symbol: $SYMBOL" >> "$FINAL_OUTPUT_DIR/summary_report.md"
echo "- Tests: $TESTS" >> "$FINAL_OUTPUT_DIR/summary_report.md"
echo "- Timestamp: $(date)" >> "$FINAL_OUTPUT_DIR/summary_report.md"
echo "" >> "$FINAL_OUTPUT_DIR/summary_report.md"

echo "## Test Results" >> "$FINAL_OUTPUT_DIR/summary_report.md"
echo "See comprehensive_results.json for detailed results." >> "$FINAL_OUTPUT_DIR/summary_report.md"
echo "" >> "$FINAL_OUTPUT_DIR/summary_report.md"

echo "## Available Test Sessions" >> "$FINAL_OUTPUT_DIR/summary_report.md"
find "$FINAL_OUTPUT_DIR" -name "*_result.json" | sort | while read file; do
    session_id=$(basename "$file" | cut -d'_' -f1)
    echo "- Session: $session_id - $(basename "$file")" >> "$FINAL_OUTPUT_DIR/summary_report.md"
done

echo -e "${GREEN}Test summary report generated at $FINAL_OUTPUT_DIR/summary_report.md${NC}"
echo "Comprehensive testing complete"
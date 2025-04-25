#!/bin/bash

# Master script to run all tests for the trading system
# This creates a comprehensive test report combining results from all test types

# Define colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create necessary directories
echo -e "${YELLOW}Creating output directories...${NC}"
timestamp=$(date +%Y%m%d_%H%M%S)
base_output_dir="data/logs/test_runs/${timestamp}"
mkdir -p "${base_output_dir}"
mkdir -p "${base_output_dir}/single"
mkdir -p "${base_output_dir}/collaborative"
mkdir -p "${base_output_dir}/integration"
mkdir -p "${base_output_dir}/decision"
mkdir -p "${base_output_dir}/structured_decision"
mkdir -p "${base_output_dir}/db_test"
mkdir -p "${base_output_dir}/comprehensive"

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY environment variable is not set${NC}"
    echo "Please set the OPENAI_API_KEY environment variable and try again"
    echo "Example: export OPENAI_API_KEY=your-api-key"
    exit 1
fi

# Parse command line arguments
SYMBOL="BTCUSDT"
SKIPS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --symbol)
            SYMBOL="$2"
            shift 2
            ;;
        --skip)
            SKIPS="$SKIPS $2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            shift
            ;;
    esac
done

# Function to check if a test should be skipped
should_skip() {
    local test_name="$1"
    if [[ $SKIPS == *"$test_name"* ]]; then
        return 0  # True, should skip
    else
        return 1  # False, should not skip
    fi
}

# Create test report header
report_file="${base_output_dir}/test_report.md"
echo "# Comprehensive Test Report" > "$report_file"
echo "" >> "$report_file"
echo "Generated: $(date)" >> "$report_file"
echo "Symbol: $SYMBOL" >> "$report_file"
echo "" >> "$report_file"
echo "## Test Results Summary" >> "$report_file"
echo "" >> "$report_file"
echo "| Test Type | Status | Duration | Results Location |" >> "$report_file"
echo "|-----------|--------|----------|------------------|" >> "$report_file"

# Run single agent test
if ! should_skip "single"; then
    echo -e "\n${GREEN}Running Single Agent Tests${NC}"
    single_start=$(date +%s)
    
    # Run the test
    output_dir="${base_output_dir}/single"
    ./run_simplified_test.sh --symbol "$SYMBOL" --output-dir "$output_dir"
    single_status=$?
    
    single_end=$(date +%s)
    single_duration=$((single_end - single_start))
    
    if [ $single_status -eq 0 ]; then
        single_status_text="✅ Success"
    else
        single_status_text="❌ Failed"
    fi
    
    # Add to report
    echo "| Single Agent | $single_status_text | ${single_duration}s | [Results](${output_dir}) |" >> "$report_file"
else
    echo -e "\n${YELLOW}Skipping Single Agent Tests${NC}"
    echo "| Single Agent | ⏩ Skipped | - | - |" >> "$report_file"
fi

# Run collaborative test
if ! should_skip "collaborative"; then
    echo -e "\n${GREEN}Running Collaborative Tests${NC}"
    collab_start=$(date +%s)
    
    # Run the test
    output_dir="${base_output_dir}/collaborative"
    ./run_collaborative_test.sh --symbol "$SYMBOL" --output-dir "$output_dir"
    collab_status=$?
    
    collab_end=$(date +%s)
    collab_duration=$((collab_end - collab_start))
    
    if [ $collab_status -eq 0 ]; then
        collab_status_text="✅ Success"
    else
        collab_status_text="❌ Failed"
    fi
    
    # Add to report
    echo "| Collaborative | $collab_status_text | ${collab_duration}s | [Results](${output_dir}) |" >> "$report_file"
else
    echo -e "\n${YELLOW}Skipping Collaborative Tests${NC}"
    echo "| Collaborative | ⏩ Skipped | - | - |" >> "$report_file"
fi

# Run integration test
if ! should_skip "integration"; then
    echo -e "\n${GREEN}Running Integration Tests${NC}"
    integration_start=$(date +%s)
    
    # Run the test
    output_dir="${base_output_dir}/integration"
    ./run_collaborative_integration.sh --symbol "$SYMBOL" --output-dir "$output_dir"
    integration_status=$?
    
    integration_end=$(date +%s)
    integration_duration=$((integration_end - integration_start))
    
    if [ $integration_status -eq 0 ]; then
        integration_status_text="✅ Success"
    else
        integration_status_text="❌ Failed"
    fi
    
    # Add to report
    echo "| Integration | $integration_status_text | ${integration_duration}s | [Results](${output_dir}) |" >> "$report_file"
else
    echo -e "\n${YELLOW}Skipping Integration Tests${NC}"
    echo "| Integration | ⏩ Skipped | - | - |" >> "$report_file"
fi

# Run decision test
if ! should_skip "decision"; then
    echo -e "\n${GREEN}Running Decision Tests${NC}"
    decision_start=$(date +%s)
    
    # Run the test
    output_dir="${base_output_dir}/decision"
    ./run_trading_decision.sh --symbol "$SYMBOL" --output-dir "$output_dir"
    decision_status=$?
    
    decision_end=$(date +%s)
    decision_duration=$((decision_end - decision_start))
    
    if [ $decision_status -eq 0 ]; then
        decision_status_text="✅ Success"
    else
        decision_status_text="❌ Failed"
    fi
    
    # Add to report
    echo "| Decision | $decision_status_text | ${decision_duration}s | [Results](${output_dir}) |" >> "$report_file"
else
    echo -e "\n${YELLOW}Skipping Decision Tests${NC}"
    echo "| Decision | ⏩ Skipped | - | - |" >> "$report_file"
fi

# Run structured decision test
if ! should_skip "structured_decision"; then
    echo -e "\n${GREEN}Running Structured Decision Tests${NC}"
    structured_decision_start=$(date +%s)
    
    # Run the test
    output_dir="${base_output_dir}/structured_decision"
    ./run_structured_decision_test.sh --symbol "$SYMBOL" --output-dir "$output_dir"
    structured_decision_status=$?
    
    structured_decision_end=$(date +%s)
    structured_decision_duration=$((structured_decision_end - structured_decision_start))
    
    if [ $structured_decision_status -eq 0 ]; then
        structured_decision_status_text="✅ Success"
    else
        structured_decision_status_text="❌ Failed"
    fi
    
    # Add to report
    echo "| Structured Decision | $structured_decision_status_text | ${structured_decision_duration}s | [Results](${output_dir}) |" >> "$report_file"
else
    echo -e "\n${YELLOW}Skipping Structured Decision Tests${NC}"
    echo "| Structured Decision | ⏩ Skipped | - | - |" >> "$report_file"
fi

# Run database test
if ! should_skip "db_test"; then
    echo -e "\n${GREEN}Running Database Integration Tests${NC}"
    db_test_start=$(date +%s)
    
    # Run the test
    output_dir="${base_output_dir}/db_test"
    ./run_db_test.sh --output-dir "$output_dir"
    db_test_status=$?
    
    db_test_end=$(date +%s)
    db_test_duration=$((db_test_end - db_test_start))
    
    if [ $db_test_status -eq 0 ]; then
        db_test_status_text="✅ Success"
    else
        db_test_status_text="❌ Failed"
    fi
    
    # Add to report
    echo "| Database Integration | $db_test_status_text | ${db_test_duration}s | [Results](${output_dir}) |" >> "$report_file"
else
    echo -e "\n${YELLOW}Skipping Database Integration Tests${NC}"
    echo "| Database Integration | ⏩ Skipped | - | - |" >> "$report_file"
fi

# Run comprehensive test
if ! should_skip "comprehensive"; then
    echo -e "\n${GREEN}Running Comprehensive Tests${NC}"
    comprehensive_start=$(date +%s)
    
    # Run the test
    output_dir="${base_output_dir}/comprehensive"
    ./run_comprehensive_tests.sh --tests simplified --symbol "$SYMBOL" --output-dir "$output_dir"
    comprehensive_status=$?
    
    comprehensive_end=$(date +%s)
    comprehensive_duration=$((comprehensive_end - comprehensive_start))
    
    if [ $comprehensive_status -eq 0 ]; then
        comprehensive_status_text="✅ Success"
    else
        comprehensive_status_text="❌ Failed"
    fi
    
    # Add to report
    echo "| Comprehensive | $comprehensive_status_text | ${comprehensive_duration}s | [Results](${output_dir}) |" >> "$report_file"
else
    echo -e "\n${YELLOW}Skipping Comprehensive Tests${NC}"
    echo "| Comprehensive | ⏩ Skipped | - | - |" >> "$report_file"
fi

# Add market data overview to report
echo -e "\n${GREEN}Adding Market Data Information to Report${NC}"
echo "" >> "$report_file"
echo "## Market Data Overview" >> "$report_file"
echo "" >> "$report_file"

# Run market data availability check
python check_market_data_availability.py --symbol "$SYMBOL" --format json --output "${base_output_dir}/market_data_info.json"

# Add summary to report
echo "Symbol: $SYMBOL" >> "$report_file"
echo "Details: [Market Data Information](${base_output_dir}/market_data_info.json)" >> "$report_file"
echo "" >> "$report_file"

# Finish the report
total_end=$(date +%s)
total_duration=$((total_end - single_start))

echo "" >> "$report_file"
echo "## Summary" >> "$report_file"
echo "" >> "$report_file"
echo "Total test execution time: ${total_duration}s" >> "$report_file"
echo "Completed at: $(date)" >> "$report_file"
echo "" >> "$report_file"
echo "To view detailed test results, use the view_test_results.py script:" >> "$report_file"
echo "\`\`\`bash" >> "$report_file"
echo "python view_test_results.py --log-dir ${base_output_dir}/[test_type]" >> "$report_file"
echo "\`\`\`" >> "$report_file"

echo -e "${GREEN}All tests completed${NC}"
echo "Test report saved to: $report_file"
echo ""
echo -e "${YELLOW}To view test results:${NC}"
echo "python view_test_results.py --log-dir ${base_output_dir}"
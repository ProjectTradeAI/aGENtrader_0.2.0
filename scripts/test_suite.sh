#!/bin/bash
#
# aGENtrader Test Suite
# A modular test framework for aGENtrader system components
#
# Usage:
#   ./scripts/test_suite.sh              # Run all tests
#   ./scripts/test_suite.sh agents       # Run only agent tests
#   ./scripts/test_suite.sh technical    # Run single test module by name

# ANSI color codes for colorful output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get version from package.json or similar
VERSION=$(grep -o '"version": *"[^"]*"' package.json 2>/dev/null | cut -d'"' -f4)
if [ -z "$VERSION" ]; then
    VERSION="0.2.0" # Default version if not found
fi

# Timestamp for logging
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/test_results_${TIMESTAMP}.log"
REPORT_FILE="logs/test_report_${TIMESTAMP}.txt"

# Track test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
DEPRECATED_TESTS=0
SKIPPED_TESTS=0

# Ensure log directory exists
mkdir -p logs

# Print logo and header
print_header() {
    echo -e "${BOLD}${BLUE}"
    echo "██╗  ██╗ ██████╗ ███████╗███╗   ██╗████████╗██████╗  █████╗ ██████╗ ███████╗██████╗ "
    echo "██║  ██║██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗"
    echo "███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝███████║██║  ██║█████╗  ██████╔╝"
    echo "██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗██╔══██║██║  ██║██╔══╝  ██╔══██╗"
    echo "██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ██║  ██║██║  ██║██████╔╝███████╗██║  ██║"
    echo "╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝"
    echo -e "${NC}"
    echo -e "${BOLD}=== aGENtrader Test Suite v${VERSION} ===${NC}"
    echo -e "Started: $(date)\n"
    
    # Write to log file too
    echo "=== aGENtrader Test Suite v${VERSION} ===" >> "$LOG_FILE"
    echo "Started: $(date)" >> "$LOG_FILE"
    echo "=============================================" >> "$LOG_FILE"
}

# Show usage information
show_usage() {
    echo -e "${BOLD}Usage:${NC}"
    echo "  ./scripts/test_suite.sh              # Run all tests"
    echo "  ./scripts/test_suite.sh agents       # Run only agent tests"
    echo "  ./scripts/test_suite.sh technical    # Run single test module by name"
    echo ""
    echo -e "${BOLD}Available test categories:${NC}"
    echo "  agents      - Test agent components"
    echo "  core        - Test core system functions"
    echo "  integration - Test system integration points"
    echo "  all         - Run all tests (default)"
    echo ""
}

# Run a single test file
run_test() {
    local test_file=$1
    local test_name=$(basename "$test_file")
    
    # Check if test is marked as deprecated
    if grep -q "@deprecated" "$test_file"; then
        echo -e "${YELLOW}⚠ [DEPRECATED] $test_name${NC}"
        echo "[DEPRECATED] $test_name" >> "$LOG_FILE"
        DEPRECATED_TESTS=$((DEPRECATED_TESTS + 1))
        return
    fi
    
    # Get the test description if it exists
    local description=$(grep -o "# Description: .*" "$test_file" | cut -d":" -f2- | xargs)
    
    echo -e "${CYAN}Running: $test_name${NC}"
    echo "Running: $test_name" >> "$LOG_FILE"
    echo "Timestamp: $(date)" >> "$LOG_FILE"
    
    # Run the test and capture output
    TEST_OUTPUT=$(python "$test_file" 2>&1)
    TEST_RESULT=$?
    
    # Record result
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Record output to log file
    echo "$TEST_OUTPUT" >> "$LOG_FILE"
    echo "Exit code: $TEST_RESULT" >> "$LOG_FILE"
    
    # Display result
    if [ $TEST_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ [PASS] $test_name${NC}"
        [ ! -z "$description" ] && echo -e "   ${CYAN}$description${NC}"
        echo "[PASS] $test_name" >> "$LOG_FILE"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ [FAIL] $test_name${NC}"
        [ ! -z "$description" ] && echo -e "   ${CYAN}$description${NC}"
        echo -e "${RED}$TEST_OUTPUT${NC}" | head -n 10
        [ $(echo "$TEST_OUTPUT" | wc -l) -gt 10 ] && echo -e "${YELLOW}... (see log for full output)${NC}"
        echo "[FAIL] $test_name" >> "$LOG_FILE"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    echo "------------------------------------" >> "$LOG_FILE"
}

# Find and run tests based on pattern
find_and_run_tests() {
    local pattern=$1
    local test_count=0
    
    for test_file in $(find tests -name "test_*${pattern}*.py" | sort); do
        run_test "$test_file"
        test_count=$((test_count + 1))
    done
    
    if [ $test_count -eq 0 ]; then
        echo -e "${YELLOW}No tests found matching: $pattern${NC}"
        echo "No tests found matching: $pattern" >> "$LOG_FILE"
    fi
}

# Run tests by category
run_tests_by_category() {
    local category=$1
    
    echo -e "\n${BOLD}${PURPLE}=== Running $category tests ===${NC}"
    echo "=== Running $category tests ===" >> "$LOG_FILE"
    
    case $category in
        "agents")
            find_and_run_tests "$(find tests/agents -name "test_*.py" | sort)"
            ;;
        "core")
            find_and_run_tests "$(find tests/core -name "test_*.py" | sort)"
            ;;
        "integration")
            find_and_run_tests "$(find tests/integration -name "test_*.py" | sort)"
            ;;
        *)
            echo -e "${YELLOW}Unknown category: $category${NC}"
            echo "Unknown category: $category" >> "$LOG_FILE"
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
            ;;
    esac
}

# Print test report summary
print_summary() {
    echo -e "\n${BOLD}${BLUE}=== Test Summary ===${NC}"
    echo -e "${BOLD}Total tests:     ${TOTAL_TESTS}${NC}"
    echo -e "${GREEN}Passed tests:    ${PASSED_TESTS}${NC}"
    echo -e "${RED}Failed tests:    ${FAILED_TESTS}${NC}"
    echo -e "${YELLOW}Deprecated tests: ${DEPRECATED_TESTS}${NC}"
    echo -e "${CYAN}Skipped tests:   ${SKIPPED_TESTS}${NC}"
    
    # Save summary to log file
    echo "" >> "$LOG_FILE"
    echo "=== Test Summary ===" >> "$LOG_FILE"
    echo "Total tests:     ${TOTAL_TESTS}" >> "$LOG_FILE"
    echo "Passed tests:    ${PASSED_TESTS}" >> "$LOG_FILE"
    echo "Failed tests:    ${FAILED_TESTS}" >> "$LOG_FILE"
    echo "Deprecated tests: ${DEPRECATED_TESTS}" >> "$LOG_FILE"
    echo "Skipped tests:   ${SKIPPED_TESTS}" >> "$LOG_FILE"
    echo "Test run completed at: $(date)" >> "$LOG_FILE"
    
    # Create a brief report file
    echo "aGENtrader Test Report" > "$REPORT_FILE"
    echo "======================" >> "$REPORT_FILE"
    echo "Date: $(date)" >> "$REPORT_FILE"
    echo "Version: ${VERSION}" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "Results:" >> "$REPORT_FILE"
    echo "  Total:      ${TOTAL_TESTS}" >> "$REPORT_FILE"
    echo "  Passed:     ${PASSED_TESTS}" >> "$REPORT_FILE"
    echo "  Failed:     ${FAILED_TESTS}" >> "$REPORT_FILE"
    echo "  Deprecated: ${DEPRECATED_TESTS}" >> "$REPORT_FILE"
    echo "  Skipped:    ${SKIPPED_TESTS}" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "Detailed log: ${LOG_FILE}" >> "$REPORT_FILE"
    
    echo -e "\nLog saved to: ${LOG_FILE}"
    echo -e "Report saved to: ${REPORT_FILE}"
    
    # Return appropriate exit code
    if [ $FAILED_TESTS -gt 0 ]; then
        return 1
    else
        return 0
    fi
}

# Check if tests directory exists
check_environment() {
    if [ ! -d "tests" ]; then
        echo -e "${RED}Error: 'tests' directory not found!${NC}"
        echo "Make sure you're running this script from the project root directory."
        exit 1
    fi
}

# Interactive test selection menu
show_test_menu() {
    echo -e "${BOLD}${PURPLE}Select test category:${NC}"
    echo -e " ${BOLD}1)${NC} Run all tests"
    echo -e " ${BOLD}2)${NC} Run agent tests"
    echo -e " ${BOLD}3)${NC} Run core tests"
    echo -e " ${BOLD}4)${NC} Run integration tests"
    echo -e " ${BOLD}5)${NC} Run a specific test"
    echo -e " ${BOLD}0)${NC} Exit"
    echo -e "\nEnter your choice: "
    read -r choice
    
    case $choice in
        1)
            run_all_tests
            ;;
        2)
            run_tests_by_category "agents"
            ;;
        3)
            run_tests_by_category "core"
            ;;
        4)
            run_tests_by_category "integration"
            ;;
        5)
            echo -e "\nEnter test name or keyword: "
            read -r test_pattern
            find_and_run_tests "$test_pattern"
            ;;
        0)
            echo -e "${YELLOW}Exiting...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice!${NC}"
            ;;
    esac
}

# Run all tests
run_all_tests() {
    echo -e "\n${BOLD}${PURPLE}=== Running all tests ===${NC}"
    echo "=== Running all tests ===" >> "$LOG_FILE"
    
    # Run agents tests
    echo -e "\n${BOLD}${BLUE}== Agent Tests ==${NC}"
    for test_file in $(find tests/agents -name "test_*.py" | sort); do
        run_test "$test_file"
    done
    
    # Run core tests
    echo -e "\n${BOLD}${BLUE}== Core Tests ==${NC}"
    for test_file in $(find tests/core -name "test_*.py" | sort); do
        run_test "$test_file"
    done
    
    # Run integration tests
    echo -e "\n${BOLD}${BLUE}== Integration Tests ==${NC}"
    for test_file in $(find tests/integration -name "test_*.py" | sort); do
        run_test "$test_file"
    done
}

# Main function
main() {
    check_environment
    print_header
    
    # Process command line arguments
    if [ $# -eq 0 ]; then
        # No arguments, show menu
        show_test_menu
    else
        case "$1" in
            "agents")
                run_tests_by_category "agents"
                ;;
            "core")
                run_tests_by_category "core"
                ;;
            "integration")
                run_tests_by_category "integration"
                ;;
            "all")
                run_all_tests
                ;;
            "help"|"-h"|"--help")
                show_usage
                exit 0
                ;;
            *)
                # Assume it's a test pattern
                find_and_run_tests "$1"
                ;;
        esac
    fi
    
    print_summary
    exit $?
}

# Execute main function
main "$@"
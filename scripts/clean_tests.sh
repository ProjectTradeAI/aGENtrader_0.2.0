#!/bin/bash
#
# aGENtrader Test Cleanup Utility
# Manages and cleans up deprecated test files
#
# Usage:
#   ./scripts/clean_tests.sh             # Show deprecated tests
#   ./scripts/clean_tests.sh --remove    # Remove deprecated tests
#   ./scripts/clean_tests.sh --archive   # Archive deprecated tests

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default action is just to list deprecated tests
REMOVE_TESTS=false
ARCHIVE_TESTS=false
ARCHIVE_DIR="tests/archive"

# Process command line arguments
if [ "$1" == "--remove" ]; then
    REMOVE_TESTS=true
elif [ "$1" == "--archive" ]; then
    ARCHIVE_TESTS=true
    mkdir -p "$ARCHIVE_DIR"
fi

# Print header
echo -e "${BOLD}${BLUE}=== aGENtrader Test Cleanup Utility ===${NC}"
echo -e "Started: $(date)\n"

# Find all deprecated tests
echo -e "${BOLD}Searching for deprecated tests...${NC}"
DEPRECATED_TESTS=$(grep -l "@deprecated" $(find tests -name "test_*.py"))
DEPRECATED_COUNT=$(echo "$DEPRECATED_TESTS" | grep -v "^$" | wc -l)

# Process deprecated tests
if [ $DEPRECATED_COUNT -eq 0 ]; then
    echo -e "${GREEN}No deprecated tests found.${NC}"
else
    echo -e "${YELLOW}Found $DEPRECATED_COUNT deprecated test(s):${NC}"
    
    for test_file in $DEPRECATED_TESTS; do
        # Extract reason for deprecation
        reason=$(grep "@deprecated" "$test_file" | sed 's/.*@deprecated: \(.*\)/\1/')
        echo -e "${YELLOW}• ${test_file}${NC} - $reason"
        
        if [ "$REMOVE_TESTS" = true ]; then
            rm "$test_file"
            echo -e "  ${RED}Removed${NC}"
        elif [ "$ARCHIVE_TESTS" = true ]; then
            # Create subdir structure
            rel_path=$(echo "$test_file" | sed 's|^tests/||')
            archive_path="$ARCHIVE_DIR/$(dirname "$rel_path")"
            mkdir -p "$archive_path"
            
            # Move file to archive
            mv "$test_file" "$archive_path/$(basename "$test_file")"
            echo -e "  ${BLUE}Archived to $archive_path/$(basename "$test_file")${NC}"
        fi
    done
    
    # Print summary
    if [ "$REMOVE_TESTS" = true ]; then
        echo -e "\n${GREEN}Removed $DEPRECATED_COUNT deprecated test file(s).${NC}"
    elif [ "$ARCHIVE_TESTS" = true ]; then
        echo -e "\n${GREEN}Archived $DEPRECATED_COUNT deprecated test file(s) to $ARCHIVE_DIR.${NC}"
    else
        echo -e "\n${YELLOW}Run with --remove to delete these files.${NC}"
        echo -e "${YELLOW}Run with --archive to move them to $ARCHIVE_DIR.${NC}"
    fi
fi

exit 0
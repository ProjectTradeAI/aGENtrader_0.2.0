#!/bin/bash

# Shell script to run database integration tests

# Define colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create necessary directories
echo -e "${YELLOW}Creating output directories...${NC}"
mkdir -p data/logs/db_tests

# Check database connection
echo -e "${YELLOW}Checking database connection...${NC}"
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}Error: DATABASE_URL environment variable is not set${NC}"
    echo "Please set the DATABASE_URL environment variable and try again"
    echo "Example: export DATABASE_URL=postgresql://username:password@host:port/dbname"
    exit 1
fi

# Parse command line arguments
OUTPUT_DIR="data/logs/db_tests"

while [[ $# -gt 0 ]]; do
    case $1 in
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

# Run the tests
timestamp=$(date +%Y%m%d_%H%M%S)
output_file="${OUTPUT_DIR}/db_test_${timestamp}.log"

echo -e "${GREEN}Running database integration tests...${NC}"
echo -e "${YELLOW}Output will be saved to ${output_file}${NC}"

echo "Database Integration Test - $(date)" > "$output_file"
echo "=======================================" >> "$output_file"
echo "" >> "$output_file"

# Run the direct database test
echo -e "${GREEN}Testing basic database functions...${NC}"
python test_db_basic.py | tee -a "$output_file"

# Add separator
echo "" >> "$output_file"
echo "---------------------------------------" >> "$output_file"
echo "" >> "$output_file"

# Run the database retrieval tool test
echo -e "${GREEN}Testing database retrieval tool...${NC}"
python test_database_retrieval_tool.py | tee -a "$output_file"

# Add separator
echo "" >> "$output_file"
echo "---------------------------------------" >> "$output_file"
echo "" >> "$output_file"

# Run the DB serialization test
echo -e "${GREEN}Testing database serialization...${NC}"
python test_serialization.py | tee -a "$output_file"

# Check the exit code
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}All database tests completed successfully${NC}"
    echo -e "Log saved to: ${output_file}"
else
    echo -e "${RED}Some database tests failed${NC}"
    echo -e "Check the log in ${output_file} for details"
fi
#!/bin/bash
# Deploy and run EC2 test in one step

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
EC2_PUBLIC_IP="${EC2_PUBLIC_IP:-}"
EC2_SSH_KEY="${EC2_SSH_KEY:-}"
STRATEGY="combined"
COMPARE=false
ADVANCED=false
TRADES=40
WIN_RATE=0.6
START_DATE="2025-02-15"
END_DATE="2025-03-15"
INTERVAL="1h"
BALANCE=10000
RISK=0.02

# Show header
echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}  EC2 Trading Test: Deploy & Run${NC}"
echo -e "${BLUE}====================================${NC}"

# Function to show usage
show_usage() {
    echo -e "${YELLOW}Usage:${NC} $0 [options]"
    echo ""
    echo "Options:"
    echo "  --improved         Run the improved simplified test (default)"
    echo "  --advanced         Run the advanced test"
    echo "  --strategy STR     Specify strategy (ma_crossover, rsi, combined)"
    echo "  --compare          Compare all strategies"
    echo "  --trades N         Number of trades for advanced test"
    echo "  --win-rate N       Win rate for advanced test (e.g., 0.6)"
    echo "  --start YYYY-MM-DD Start date for backtest"
    echo "  --end YYYY-MM-DD   End date for backtest"
    echo "  --interval INT     Data interval (1m, 5m, 15m, 1h, 4h, 1d)"
    echo "  --balance N        Initial balance"
    echo "  --risk N           Risk per trade (e.g., 0.02 for 2%)"
    echo "  --help             Show this help message"
    echo ""
}

# Function to check if SSH key is available
check_credentials() {
    echo -e "${YELLOW}Checking credentials...${NC}"
    
    if [ -z "$EC2_PUBLIC_IP" ]; then
        echo -e "${RED}Error: EC2_PUBLIC_IP environment variable not set${NC}"
        echo "Please set the EC2_PUBLIC_IP environment variable with your EC2 instance's public IP address"
        return 1
    fi
    
    if [ -z "$EC2_SSH_KEY" ]; then
        echo -e "${RED}Error: EC2_SSH_KEY environment variable not set${NC}"
        echo "Please set the EC2_SSH_KEY environment variable with your EC2 SSH key"
        return 1
    fi
    
    echo -e "${GREEN}Credentials found!${NC}"
    
    # Create a temporary file for the SSH key
    SSH_KEY_FILE=$(mktemp)
    echo "$EC2_SSH_KEY" > "$SSH_KEY_FILE"
    chmod 600 "$SSH_KEY_FILE"
    
    return 0
}

# Function to run command on EC2
run_command() {
    local cmd="$1"
    
    echo -e "${YELLOW}Executing on EC2:${NC} $cmd"
    
    # Run the command on EC2
    ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no ec2-user@"$EC2_PUBLIC_IP" "cd /home/ec2-user/aGENtrader && $cmd"
    
    return $?
}

# Function to upload files to EC2
upload_file() {
    local source_file="$1"
    local dest_file="${2:-$source_file}"
    
    echo -e "${YELLOW}Uploading to EC2:${NC} $source_file -> $dest_file"
    
    # Run the command on EC2
    cat "$source_file" | ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no ec2-user@"$EC2_PUBLIC_IP" "cat > /home/ec2-user/aGENtrader/$dest_file && chmod +x /home/ec2-user/aGENtrader/$dest_file"
    
    return $?
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --improved)
            ADVANCED=false
            shift
            ;;
        --advanced)
            ADVANCED=true
            shift
            ;;
        --strategy)
            STRATEGY="$2"
            shift 2
            ;;
        --compare)
            COMPARE=true
            shift
            ;;
        --trades)
            TRADES="$2"
            shift 2
            ;;
        --win-rate)
            WIN_RATE="$2"
            shift 2
            ;;
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

# Check if EC2 credentials are available
check_credentials
if [ $? -ne 0 ]; then
    exit 1
fi

# Step 1: Upload improved_simplified_test.py to EC2
echo -e "\n${BLUE}Step 1: Uploading test scripts to EC2...${NC}"
if [ "$ADVANCED" = false ]; then
    upload_file "improved_simplified_test.py"
    TESTSCRIPT="improved_simplified_test.py"
else
    upload_file "advanced_test.py"
    TESTSCRIPT="advanced_test.py"
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to upload test script to EC2${NC}"
    rm -f "$SSH_KEY_FILE"
    exit 1
fi

# Step 2: Ensure results directory exists
echo -e "\n${BLUE}Step 2: Ensuring results directory exists...${NC}"
run_command "mkdir -p results"

# Step 3: Run test script
echo -e "\n${BLUE}Step 3: Running backtest on EC2...${NC}"

if [ "$ADVANCED" = false ]; then
    # Build the command for improved test
    CMD="python3 $TESTSCRIPT"
    
    # Add arguments
    if [ "$COMPARE" = true ]; then
        CMD="$CMD --compare"
    else
        CMD="$CMD --strategy $STRATEGY"
    fi
    
    CMD="$CMD --start_date $START_DATE --end_date $END_DATE --interval $INTERVAL"
    CMD="$CMD --initial_balance $BALANCE --risk_per_trade $RISK"
else
    # Build the command for advanced test
    CMD="python3 $TESTSCRIPT --trades $TRADES --win_rate $WIN_RATE --initial_balance $BALANCE"
fi

run_command "$CMD"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Backtest failed to complete${NC}"
    rm -f "$SSH_KEY_FILE"
    exit 1
fi

# Step 4: List results
echo -e "\n${BLUE}Step 4: Listing results...${NC}"
run_command "ls -lt results | head -10"

# Step 5: Create local results directory
echo -e "\n${BLUE}Step 5: Creating local results directory...${NC}"
mkdir -p ec2_results

# Step 6: Download latest result
echo -e "\n${BLUE}Step 6: Downloading latest result...${NC}"
LATEST_RESULT=$(ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no ec2-user@"$EC2_PUBLIC_IP" "cd /home/ec2-user/aGENtrader && ls -t results/*.json | head -1")

if [ -n "$LATEST_RESULT" ]; then
    echo -e "${GREEN}Found latest result: $LATEST_RESULT${NC}"
    
    # Extract filename
    FILENAME=$(basename "$LATEST_RESULT")
    
    # Download the file
    scp -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no ec2-user@"$EC2_PUBLIC_IP":"/home/ec2-user/aGENtrader/$LATEST_RESULT" "ec2_results/$FILENAME"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Downloaded to: ec2_results/$FILENAME${NC}"
        
        # Display summary using the analyzer
        if [ -f "ec2_results_analyzer.py" ]; then
            echo -e "\n${BLUE}Analyzing result...${NC}"
            python3 ec2_results_analyzer.py --dir ec2_results --pattern "$FILENAME"
        fi
    else
        echo -e "${RED}Error: Failed to download result${NC}"
    fi
else
    echo -e "${RED}No results found${NC}"
fi

# Clean up the temporary SSH key file
if [ -n "$SSH_KEY_FILE" ]; then
    rm -f "$SSH_KEY_FILE"
fi

echo -e "\n${GREEN}Done!${NC}"
exit 0
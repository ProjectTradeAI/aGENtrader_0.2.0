#!/bin/bash
# Run EC2 test using direct SSH command method

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
SSH_KEY_FILE="/tmp/ec2_ssh_key.pem"
STRATEGY="combined"
START_DATE="2025-02-15"
END_DATE="2025-03-15"
INTERVAL="1h"
BALANCE=10000
RISK=0.02
COMPARE=false

# Show usage
show_usage() {
    echo -e "${BLUE}EC2 Direct Test Runner${NC}"
    echo "===================="
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --strategy STR     Specify strategy (ma_crossover, rsi, combined)"
    echo "  --compare          Compare all strategies"
    echo "  --start YYYY-MM-DD Start date for backtest"
    echo "  --end YYYY-MM-DD   End date for backtest"
    echo "  --interval INT     Data interval (1m, 5m, 15m, 1h, 4h, 1d)"
    echo "  --balance N        Initial balance"
    echo "  --risk N           Risk per trade (e.g., 0.02 for 2%)"
    echo "  --help             Show this help message"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --strategy)
            STRATEGY="$2"
            shift 2
            ;;
        --compare)
            COMPARE=true
            shift
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

# Check if EC2_PUBLIC_IP is set
if [ -z "$EC2_PUBLIC_IP" ]; then
    echo -e "${RED}Error: EC2_PUBLIC_IP environment variable not set${NC}"
    echo "Please set the EC2_PUBLIC_IP environment variable with your EC2 instance's public IP address"
    exit 1
fi

# Create SSH key file
echo -e "${YELLOW}Setting up SSH key...${NC}"
echo "$EC2_SSH_KEY" > "$SSH_KEY_FILE"
chmod 600 "$SSH_KEY_FILE"

# Upload the test script to EC2
echo -e "\n${BLUE}Step 1: Uploading test script to EC2...${NC}"
cat improved_simplified_test.py | ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no ec2-user@"$EC2_PUBLIC_IP" "cat > /home/ec2-user/aGENtrader/improved_simplified_test.py && chmod +x /home/ec2-user/aGENtrader/improved_simplified_test.py"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to upload test script to EC2${NC}"
    rm -f "$SSH_KEY_FILE"
    exit 1
fi

# Ensure results directory exists
echo -e "\n${BLUE}Step 2: Ensuring results directory exists...${NC}"
ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no ec2-user@"$EC2_PUBLIC_IP" "mkdir -p /home/ec2-user/aGENtrader/results"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to create results directory on EC2${NC}"
    rm -f "$SSH_KEY_FILE"
    exit 1
fi

# Build the command
if [ "$COMPARE" = true ]; then
    CMD="python3 improved_simplified_test.py --compare"
else
    CMD="python3 improved_simplified_test.py --strategy $STRATEGY"
fi

CMD="$CMD --start_date $START_DATE --end_date $END_DATE --interval $INTERVAL"
CMD="$CMD --initial_balance $BALANCE --risk_per_trade $RISK"

# Run the backtest
echo -e "\n${BLUE}Step 3: Running backtest on EC2...${NC}"
echo -e "${YELLOW}Executing:${NC} $CMD"

ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no ec2-user@"$EC2_PUBLIC_IP" "cd /home/ec2-user/aGENtrader && $CMD"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Backtest failed to complete${NC}"
    rm -f "$SSH_KEY_FILE"
    exit 1
fi

# List results
echo -e "\n${BLUE}Step 4: Listing results...${NC}"
ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no ec2-user@"$EC2_PUBLIC_IP" "cd /home/ec2-user/aGENtrader && ls -lt results | head -10"

# Create local results directory
echo -e "\n${BLUE}Step 5: Creating local results directory...${NC}"
mkdir -p ec2_results

# Download latest result
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
        echo -e "\n${BLUE}Result content:${NC}"
        cat "ec2_results/$FILENAME" | head -20
        echo -e "..."
    else
        echo -e "${RED}Error: Failed to download result${NC}"
    fi
else
    echo -e "${RED}No results found${NC}"
fi

# Clean up the temporary SSH key file
rm -f "$SSH_KEY_FILE"

echo -e "\n${GREEN}Done!${NC}"
exit 0
#!/bin/bash
# Check backtest results on EC2 instance

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verify secrets are available
if [ -z "$EC2_SSH_KEY" ] || [ -z "$EC2_PUBLIC_IP" ]; then
    print_error "EC2_SSH_KEY or EC2_PUBLIC_IP secret is not set."
    exit 1
fi

# Configuration
EC2_HOST="ec2-user@$EC2_PUBLIC_IP"
REMOTE_PATH="/home/ec2-user/aGENtrader"

# Format the SSH key properly
print_step "Reformatting SSH key..."
KEY_CONTENT=$(echo "$EC2_SSH_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY-----//' | sed 's/-----END RSA PRIVATE KEY-----//')
FORMATTED_KEY="-----BEGIN RSA PRIVATE KEY-----"

# Split the key into chunks of 64 characters
for ((i=0; i<${#KEY_CONTENT}; i+=64)); do
    FORMATTED_KEY="$FORMATTED_KEY
${KEY_CONTENT:$i:64}"
done

FORMATTED_KEY="$FORMATTED_KEY
-----END RSA PRIVATE KEY-----"

# Create a temporary SSH key file
SSH_KEY_PATH="/tmp/ec2_key.pem"
echo "$FORMATTED_KEY" > "$SSH_KEY_PATH"
chmod 600 "$SSH_KEY_PATH"

print_step "Connecting to EC2 instance..."
if ! ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$EC2_HOST" "echo Connected successfully"; then
    print_error "Failed to connect to EC2 instance."
    exit 1
fi
print_step "Connection successful!"

# Check if the backtest is running
print_step "Checking if backtest is running..."
if ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "pgrep -f run_backtest_with_local_llm.py > /dev/null"; then
    print_step "Backtest is currently running."
    print_step "Last 20 lines of output:"
    ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "tail -n 20 $REMOTE_PATH/backtest_output.log"
else
    print_step "Backtest is not currently running."
    
    # Check for output log
    print_step "Checking backtest output log..."
    ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "if [ -f $REMOTE_PATH/backtest_output.log ]; then tail -n 50 $REMOTE_PATH/backtest_output.log; else echo 'No output log found'; fi"
    
    # Check for result files
    print_step "Checking for result files..."
    ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "find $REMOTE_PATH/results -name '*.json' 2>/dev/null || echo 'No result files found'"
fi

# Clean up
rm -f "$SSH_KEY_PATH"
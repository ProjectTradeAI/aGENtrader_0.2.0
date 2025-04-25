#!/bin/bash
# Force recreate the backtest script on EC2

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

print_step "Testing SSH connection..."
if ! ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$EC2_HOST" "echo Connected successfully"; then
    print_error "Failed to connect to EC2 instance."
    exit 1
fi
print_step "SSH connection successful!"

# Stop any running backtest
print_step "Stopping any running backtest..."
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "pkill -f run_backtest_with_local_llm.py || true"

# Force recreate the backtest script
print_step "Recreating backtest script on EC2..."
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "rm -f $REMOTE_PATH/run-backtest.sh"
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "cat > $REMOTE_PATH/run-backtest.sh << 'EOF'
#!/bin/bash
cd /home/ec2-user/aGENtrader
echo 'Starting backtest with local LLM integration...'
python3 run_backtest_with_local_llm.py --symbol BTCUSDT --start_date 2025-02-15 --end_date 2025-03-15 --use_mock_data --output_dir ./results
EOF"
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "chmod +x $REMOTE_PATH/run-backtest.sh"
print_step "Backtest script recreated!"

# Run the backtest
print_step "Starting backtest on EC2 instance..."
print_warning "This will run in the background on the EC2 instance."
print_warning "You can check results later using the check-ec2-results.sh script."

ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && rm -f ./backtest_output.log && nohup ./run-backtest.sh > ./backtest_output.log 2>&1 &"
print_step "Backtest started on EC2 instance!"
print_step "To check on the progress later, run: ./check-ec2-results.sh"

# Clean up
rm -f "$SSH_KEY_PATH"
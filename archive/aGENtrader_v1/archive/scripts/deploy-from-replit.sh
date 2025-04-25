#!/bin/bash
# EC2 Deployment Script from Replit Environment
# This script deploys the trading bot with local LLM to your EC2 instance

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
if [ -z "$EC2_SSH_KEY" ]; then
    print_error "EC2_SSH_KEY secret is not set. Please add it to your Replit secrets."
    exit 1
fi

if [ -z "$EC2_PUBLIC_IP" ]; then
    print_error "EC2_PUBLIC_IP secret is not set. Please add it to your Replit secrets."
    exit 1
fi

# Configuration
EC2_HOST="ec2-user@$EC2_PUBLIC_IP"
REMOTE_PATH="/home/ec2-user/aGENtrader"
LOCAL_PATH="$(pwd)"

# Create a temporary SSH key file
print_step "Setting up SSH key..."
mkdir -p ~/.ssh
SSH_KEY_PATH="/tmp/ec2_key.pem"
echo "$EC2_SSH_KEY" > "$SSH_KEY_PATH"
chmod 600 "$SSH_KEY_PATH"

# Test SSH connection
print_step "Testing SSH connection to your EC2 instance..."
if ! ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$EC2_HOST" "echo Connected successfully"; then
    print_error "Failed to connect to EC2 instance. Please check your EC2_PUBLIC_IP and EC2_SSH_KEY."
    rm -f "$SSH_KEY_PATH"
    exit 1
fi

# Prepare files for deployment
print_step "Preparing files for deployment..."

# Create deployment archive
print_step "Creating deployment archive..."
DEPLOY_DIR="/tmp/trading-bot-deploy"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy files
rsync -av --exclude=".git" --exclude="node_modules" --exclude="venv" --exclude="__pycache__" \
    --exclude=".vscode" --exclude="data/logs" --exclude="client/node_modules" \
    "$LOCAL_PATH/" "$DEPLOY_DIR/"

# Create deployment archive
cd /tmp
tar -czf trading-bot-deploy.tar.gz trading-bot-deploy
cd "$LOCAL_PATH"

# Transfer files to EC2
print_step "Transferring files to EC2 instance..."
scp -i "$SSH_KEY_PATH" /tmp/trading-bot-deploy.tar.gz "$EC2_HOST:/tmp/"

# Extract and set up on EC2
print_step "Setting up on EC2 instance..."
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "bash -s" << 'ENDSSH'
# Create directories
mkdir -p "$REMOTE_PATH"
mkdir -p "$REMOTE_PATH/logs"
mkdir -p "$REMOTE_PATH/data/logs"
mkdir -p "$REMOTE_PATH/data/backtest_results"
mkdir -p "$REMOTE_PATH/models/llm_models"

# Extract files
tar -xzf /tmp/trading-bot-deploy.tar.gz -C /tmp/
rsync -av /tmp/trading-bot-deploy/ "$REMOTE_PATH/"
rm -rf /tmp/trading-bot-deploy.tar.gz /tmp/trading-bot-deploy

# Set permissions
chmod +x "$REMOTE_PATH"/deploy-ec2.sh
chmod +x "$REMOTE_PATH"/prepare-aws-llm-integration.py

echo "Files transferred and extracted successfully."
ENDSSH

# Run preparation script on EC2
print_step "Running preparation script on EC2..."
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && python3 prepare-aws-llm-integration.py"

# Install dependencies
print_step "Installing dependencies on EC2..."
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && pip3 install --user -r requirements.txt"
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && pip3 install --user llama-cpp-python huggingface_hub psutil"

# Create run-backtest.sh script
print_step "Creating run-backtest.sh script..."
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && bash -s" << 'ENDSSH2'
cat > run-backtest.sh << 'SHEOF'
#!/bin/bash
# Script to easily run backtests with different parameters

# Default values
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-01"
END_DATE="2025-03-15"
TIMEOUT="120"
RISK="0.02"
BALANCE="10000"

# Usage function
usage() {
  echo "Usage: $0 [-s SYMBOL] [-i INTERVAL] [-f START_DATE] [-t END_DATE] [-o TIMEOUT] [-r RISK] [-b BALANCE]"
  echo "  -s SYMBOL      Trading symbol (default: BTCUSDT)"
  echo "  -i INTERVAL    Time interval (default: 1h)"
  echo "  -f START_DATE  Start date (default: 2025-03-01)"
  echo "  -t END_DATE    End date (default: 2025-03-15)"
  echo "  -o TIMEOUT     Analysis timeout in seconds (default: 120)"
  echo "  -r RISK        Risk per trade as decimal (default: 0.02)"
  echo "  -b BALANCE     Initial balance (default: 10000)"
  exit 1
}

# Parse command line arguments
while getopts "s:i:f:t:o:r:b:h" opt; do
  case $opt in
    s) SYMBOL=$OPTARG ;;
    i) INTERVAL=$OPTARG ;;
    f) START_DATE=$OPTARG ;;
    t) END_DATE=$OPTARG ;;
    o) TIMEOUT=$OPTARG ;;
    r) RISK=$OPTARG ;;
    b) BALANCE=$OPTARG ;;
    h) usage ;;
    \?) usage ;;
  esac
done

echo "Running backtest with:"
echo "Symbol: $SYMBOL"
echo "Interval: $INTERVAL"
echo "Start date: $START_DATE"
echo "End date: $END_DATE"
echo "Analysis timeout: $TIMEOUT"
echo "Risk per trade: $RISK"
echo "Initial balance: $BALANCE"
echo

# Run the backtest
python3 run_backtest_with_local_llm.py \
  --symbol $SYMBOL \
  --interval $INTERVAL \
  --start_date $START_DATE \
  --end_date $END_DATE \
  --analysis_timeout $TIMEOUT \
  --risk_per_trade $RISK \
  --initial_balance $BALANCE \
  --output_dir data/backtest_results
SHEOF

chmod +x run-backtest.sh
ENDSSH2

# Download LLM model (automatic yes for non-interactive environment)
print_step "Downloading LLM model on EC2..."
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && python3 -c \"
from huggingface_hub import hf_hub_download
import os

os.makedirs('models/llm_models', exist_ok=True)
print('Downloading model from Hugging Face...')
hf_hub_download('TheBloke/Llama-2-7B-Chat-GGUF', 
                'llama-2-7b-chat.Q4_K_M.gguf', 
                local_dir='models/llm_models')
print('Model downloaded successfully!')
\""

# Run a test backtest (automatic yes for non-interactive environment)
print_step "Running a quick test backtest..."
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && ./run-backtest.sh -f 2025-03-01 -t 2025-03-02 -o 60"

# Clean up
print_step "Cleaning up..."
rm -f "$SSH_KEY_PATH"
rm -rf /tmp/trading-bot-deploy.tar.gz
rm -rf "$DEPLOY_DIR"

print_step "Deployment completed successfully!"
echo "You can now run backtests on your EC2 instance by SSHing into it and running ./run-backtest.sh"
echo
echo "To monitor the EC2 instance remotely, you can SSH with:"
echo "  ssh ec2-user@$EC2_PUBLIC_IP"
echo "Then run: cd $REMOTE_PATH && ./run-backtest.sh"
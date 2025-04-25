#!/bin/bash
# Fix script for deploying the AutoGen GroupChatManager fix to EC2

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Log function
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
  echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Check if EC2_PUBLIC_IP is set
if [ -z "$EC2_PUBLIC_IP" ]; then
  log_error "EC2_PUBLIC_IP environment variable is not set. Please set it before running this script."
  exit 1
fi

# Set SSH key path
SSH_KEY="ec2_ssh_key.pem"
if [ ! -f "$SSH_KEY" ]; then
  log_error "SSH key file '$SSH_KEY' not found. Please ensure it exists in the current directory."
  exit 1
fi

# Set permissions on SSH key
chmod 400 "$SSH_KEY"

# Target EC2 paths
EC2_USER="ec2-user"
EC2_REPO_DIR="/home/ec2-user/aGENtrader"

# Script files to transfer
FIX_SCRIPT="fix_ec2_autogen_group_chat.py"

log "Starting deployment of AutoGen fix to EC2 at $EC2_PUBLIC_IP"

# Check if fix script exists
if [ ! -f "$FIX_SCRIPT" ]; then
  log_error "Fix script '$FIX_SCRIPT' not found. Please ensure it exists in the current directory."
  exit 1
fi

# Transfer fix script to EC2
log "Transferring fix script to EC2..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$FIX_SCRIPT" "$EC2_USER@$EC2_PUBLIC_IP:$EC2_REPO_DIR/"

if [ $? -ne 0 ]; then
  log_error "Failed to transfer fix script to EC2. Please check connectivity."
  exit 1
fi

log "Successfully transferred fix script to EC2"

# Run fix script on EC2
log "Running fix script on EC2 with --all option to fix all affected files..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_PUBLIC_IP" "cd $EC2_REPO_DIR && python3 $FIX_SCRIPT --all"

if [ $? -ne 0 ]; then
  log_warning "Fix script may have encountered issues. Please check the output."
else
  log "Fix script executed successfully"
fi

# Check if backtest works now
log "Testing backtesting to verify the fix..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_PUBLIC_IP" "cd $EC2_REPO_DIR && python3 test_structured_decision_making.py --test_type extractor"

if [ $? -ne 0 ]; then
  log_warning "Test may have encountered issues. Please check the output."
else
  log "Test executed successfully"
fi

log "Deployment complete!"
log "If you still encounter issues, try these manual steps on EC2:"
log "1. cd $EC2_REPO_DIR"
log "2. python3 $FIX_SCRIPT --all"
log "3. Run your backtesting script again"

exit 0
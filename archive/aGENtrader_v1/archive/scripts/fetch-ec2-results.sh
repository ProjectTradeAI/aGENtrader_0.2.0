#!/bin/bash
# Script to fetch backtest results from EC2

# Source the SSH key setup script if it exists
if [ -f "fix-ssh-key.sh" ]; then
    source fix-ssh-key.sh
fi

# Set variables
SSH_KEY_PATH="ec2_ssh_key.pem"
SSH_USER="ec2-user"
EC2_IP="${EC2_PUBLIC_IP}"

echo "Fetching latest backtest results from EC2 instance..."

# Create local directory for results if it doesn't exist
mkdir -p ec2_results

# Fetch list of result files
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "${SSH_USER}@${EC2_IP}" "cd ~/aGENtrader/results && ls -la"

# Copy the latest result files (adjust the file pattern as needed)
scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "${SSH_USER}@${EC2_IP}:~/aGENtrader/results/*.json" ec2_results/

echo "Results fetched to ec2_results directory. Latest files:"
ls -la ec2_results/ | tail -n 10

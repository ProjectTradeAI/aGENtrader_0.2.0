#!/bin/bash
# Script to run a full backtest on EC2 with the fixed indentation

# Source the SSH key setup script if it exists
if [ -f "fix-ssh-key.sh" ]; then
    source fix-ssh-key.sh
fi

# Set variables
SSH_KEY_PATH="ec2_ssh_key.pem"
SSH_USER="ec2-user"
EC2_IP="${EC2_PUBLIC_IP}"

echo "Starting full backtest on EC2 instance with fixed code..."

# Run the backtest command on EC2
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "${SSH_USER}@${EC2_IP}" "cd ~/aGENtrader && python3 run_simplified_full_backtest.py --symbol BTCUSDT --interval 1h --days 30 --initial_balance 10000 --output_dir results" 

# Get the latest results
echo "Retrieving the results..."
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "${SSH_USER}@${EC2_IP}" "cd ~/aGENtrader && ls -la results/ | tail -n 10"

echo "Full backtest completed on EC2 instance."

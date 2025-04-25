#!/bin/bash
# Utility script to run commands on EC2 reliably

# Check if command parameter is provided
if [ $# -eq 0 ]; then
  echo "Usage: $0 \"command to run on EC2\""
  exit 1
fi

# Set variables
SSH_KEY="ec2_ssh_key.pem"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"

# Ensure key has correct permissions
chmod 600 "$SSH_KEY"

# Connect to EC2 and run command
echo "Running on EC2: $1"
echo "----------------------------------------"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_PUBLIC_IP" "cd $EC2_DIR && $1"
echo "----------------------------------------"
echo "Command completed."

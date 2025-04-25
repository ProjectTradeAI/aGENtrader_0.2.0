#!/bin/bash
# Updated utility script to run commands on EC2 reliably using Replit Secret

# Check if command parameter is provided
if [ $# -eq 0 ]; then
  echo "Usage: $0 \"command to run on EC2\""
  exit 1
fi

# Set variables
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="$HOME/.ssh/ec2_key.pem"

# Ensure we have the key in place
if [ ! -f "$KEY_PATH" ]; then
    echo "Creating key file from Replit Secret..."
    mkdir -p ~/.ssh
    echo "$EC2_SSH_KEY" > "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

# Connect to EC2 and run command
echo "Running on EC2: $1"
echo "----------------------------------------"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && $1"
echo "----------------------------------------"
echo "Command completed."

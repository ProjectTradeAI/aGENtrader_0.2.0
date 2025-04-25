#!/bin/bash
# EC2 connection script with formatted key

# Configuration
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
KEY_PATH="/tmp/formatted_ec2_key.pem"
EC2_DIR="/home/ec2-user/aGENtrader"

# Try to connect
if [ $# -eq 0 ]; then
  # No command specified, just test connection
  echo "Testing connection to $EC2_IP with user $SSH_USER using formatted key..."
  ssh -v -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$EC2_IP" "echo Connection successful!"
  
  if [ $? -eq 0 ]; then
    echo "✅ Connection successful!"
    echo
    echo "You can now run commands on your EC2 instance."
  else
    echo "❌ Connection failed."
    echo
    echo "Please try using the AWS Console method as described in ec2-console-guide.md"
  fi
else
  # Run the provided command
  echo "Running command on EC2: $@"
  echo "---------------------------------------------------"
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "$@"
  echo "---------------------------------------------------"
fi

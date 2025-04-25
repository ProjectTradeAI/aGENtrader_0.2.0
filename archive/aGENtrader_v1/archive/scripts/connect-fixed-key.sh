#!/bin/bash
# Script to connect using a properly formatted key

# Variables
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
KEY_PATH="/tmp/manual_original_key.pem"
EC2_DIR="/home/ec2-user/aGENtrader"

if [ $# -eq 0 ]; then
    # No command provided, just test connection
    echo "Testing connection to $EC2_IP..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$EC2_IP" "echo Connection successful!"
    
    if [ $? -eq 0 ]; then
        echo
        echo "✅ Connection successful!"
        echo
        echo "Usage examples:"
        echo "  ./connect-fixed-key.sh \"ls -la\"                         # List files in home directory"
        echo "  ./connect-fixed-key.sh \"cd $EC2_DIR && ls -la\"           # List files in aGENtrader directory"
        echo "  ./connect-fixed-key.sh \"cd $EC2_DIR && ./ec2-multi-agent-backtest.sh --help\"  # Show backtest help"
    else
        echo
        echo "❌ Connection failed."
        echo "Please try the AWS Console method instead, as described in aws-console-connect.md"
    fi
else
    # Run the provided command
    echo "Running command on EC2: $@"
    echo "---------------------------------------------------"
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "$@"
    echo "---------------------------------------------------"
    echo "Command execution completed."
fi

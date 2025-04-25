#!/bin/bash
# EC2 connection script using the original key

# Configuration variables
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
KEY_PATH="/tmp/original_ec2_key.pem"
EC2_DIR="/home/ec2-user/aGENtrader"

# Create the key file from the secret
echo "Creating key file from ORIGINAL_EC2_KEY secret..."
echo "$ORIGINAL_EC2_KEY" > "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Validate key with OpenSSL
echo "Validating key format..."
if openssl rsa -in "$KEY_PATH" -check -noout > /dev/null 2>&1; then
    echo "✅ Key validation successful"
else
    echo "❌ Key validation failed - but we'll try to use it anyway"
fi

# Function to display help message
function show_help() {
    echo "EC2 Connection Helper (Original Key)"
    echo "==================================="
    echo "This script connects to your EC2 instance using the original key"
    echo
    echo "Usage:"
    echo "  $0 [command]"
    echo
    echo "Examples:"
    echo "  $0                                       # Test connection"
    echo "  $0 \"ls -la\"                              # List files in home directory"
    echo "  $0 \"cd $EC2_DIR && ls -la\"               # List files in project directory"
    echo "  $0 \"cd $EC2_DIR && ./ec2-multi-agent-backtest.sh --help\"  # Show backtest help"
    echo
    echo "To run backtests:"
    echo "  $0 \"cd $EC2_DIR && ./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --local-llm\""
}

# Check if help was requested
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    show_help
    exit 0
fi

# Try to connect
if [ $# -eq 0 ]; then
    # No command specified, just test connection
    echo "Testing connection to EC2 instance at $EC2_IP..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$EC2_IP" "echo Connected successfully as $SSH_USER!"
    
    if [ $? -eq 0 ]; then
        echo
        echo "✅ Connection successful!"
        echo
        echo "You can now run commands on the EC2 instance:"
        echo "  ./connect-original-key.sh \"command\""
        echo
        echo "Examples:"
        echo "  ./connect-original-key.sh \"cd $EC2_DIR && ls -la\""
        echo "  ./connect-original-key.sh \"cd $EC2_DIR && ./ec2-multi-agent-backtest.sh --help\""
    else
        echo
        echo "❌ Connection failed."
        echo
        echo "Please double-check:"
        echo "1. The EC2 instance is running"
        echo "2. The security group allows SSH from your IP"
        echo "3. You're using the correct key pair for this instance"
    fi
else
    # Run the specified command
    echo "Running command on EC2: $@"
    echo "---------------------------------------------------"
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "$@"
    
    if [ $? -eq 0 ]; then
        echo "---------------------------------------------------"
        echo "✅ Command executed successfully."
    else
        echo "---------------------------------------------------"
        echo "❌ Command execution failed."
    fi
fi

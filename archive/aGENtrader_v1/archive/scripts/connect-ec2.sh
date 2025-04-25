#!/bin/bash
# EC2 connection script using the newest EC2_KEY secret

# Configuration
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
KEY_PATH="/tmp/ec2_key.pem"
EC2_DIR="/home/ec2-user/aGENtrader"

# Create key file from secret
echo "Creating key file from EC2_KEY secret..."
echo "$EC2_KEY" > "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Function to show help text
show_help() {
  echo "EC2 Connection Helper"
  echo "===================="
  echo "Usage: ./connect-ec2.sh [command]"
  echo
  echo "Examples:"
  echo "  ./connect-ec2.sh                       # Just test connection"
  echo "  ./connect-ec2.sh \"ls -la\"               # List files in home dir"
  echo "  ./connect-ec2.sh \"cd $EC2_DIR && ls -la\" # List files in project dir"
  echo 
  echo "For running backtests:"
  echo "  ./connect-ec2.sh \"cd $EC2_DIR && ./ec2-multi-agent-backtest.sh --help\""
}

# Parse command line arguments
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
  show_help
  exit 0
fi

# Try to connect
if [ $# -eq 0 ]; then
  # No command specified, just test connection
  echo "Testing connection to $EC2_IP with user $SSH_USER..."
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$EC2_IP" "echo Connection successful! && whoami && pwd"
  
  if [ $? -eq 0 ]; then
    echo "✅ Connection successful!"
    echo
    echo "You can now run commands on your EC2 instance."
    echo "Examples:"
    echo "  ./connect-ec2.sh \"ls -la\"                           # List files in home directory"
    echo "  ./connect-ec2.sh \"cd $EC2_DIR && ls -la\"             # List files in project directory"
    echo
    echo "For backtesting:"
    echo "  ./connect-ec2.sh \"cd $EC2_DIR && ./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --local-llm\""
  else
    echo "❌ Connection failed."
    echo "Please check that:"
    echo "1. You've added the correct EC2_KEY to secrets"
    echo "2. The EC2 instance is running"
    echo "3. The security group allows SSH from your IP"
  fi
else
  # Run the provided command
  echo "Running command on EC2: $@"
  echo "---------------------------------------------------"
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "$@"
  
  if [ $? -eq 0 ]; then
    echo "---------------------------------------------------"
    echo "✅ Command completed successfully."
  else
    echo "---------------------------------------------------"
    echo "❌ Command execution failed with error code $?."
  fi
fi

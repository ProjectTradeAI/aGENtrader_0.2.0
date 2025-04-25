#!/bin/bash
# Script to use the EC2_SSH_KEY from Replit Secrets

# Create a clean key file from the secret
echo "Creating key file from Replit Secret..."
mkdir -p ~/.ssh
echo "$EC2_SSH_KEY" > ~/.ssh/ec2_key.pem
chmod 600 ~/.ssh/ec2_key.pem

# Check key format
echo "Checking key format..."
if grep -q "BEGIN" ~/.ssh/ec2_key.pem && grep -q "END" ~/.ssh/ec2_key.pem; then
    echo "Key has proper BEGIN/END markers."
else
    echo "Key lacks proper BEGIN/END markers - adding them..."
    
    # Save current key content
    mv ~/.ssh/ec2_key.pem ~/.ssh/ec2_key_raw.pem
    
    # Add proper PEM headers
    echo "-----BEGIN RSA PRIVATE KEY-----" > ~/.ssh/ec2_key.pem
    cat ~/.ssh/ec2_key_raw.pem >> ~/.ssh/ec2_key.pem
    echo "-----END RSA PRIVATE KEY-----" >> ~/.ssh/ec2_key.pem
    chmod 600 ~/.ssh/ec2_key.pem
    rm ~/.ssh/ec2_key_raw.pem
fi

# Test connection
echo "Testing SSH connection..."
echo "Note: To connect, your EC2 instance must be running and its security group must allow SSH access."
echo

# Get EC2 public IP (check both env var and Replit Secret)
if [ -n "$EC2_PUBLIC_IP" ]; then
    EC2_IP="$EC2_PUBLIC_IP"
    echo "Using EC2_PUBLIC_IP environment variable: $EC2_IP"
else
    echo "Using default IP (51.20.250.135) - update with your actual IP if needed"
    EC2_IP="51.20.250.135"
fi

# Try to connect with verbose output
echo "Attempting to connect to $EC2_IP..."
ssh -v -i ~/.ssh/ec2_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_IP "echo 'Connection successful!'" 

RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "====================="
    echo "SUCCESS! The connection worked properly."
    echo "====================="
    
    # Create a better script to use for all future SSH connections
    cat > ec2-replit-connect.sh << 'INNEREOF'
#!/bin/bash
# Script to connect to EC2 using secret key

# Check for command parameter
if [ $# -eq 0 ]; then
    echo "Usage: $0 \"command to run on EC2\""
    echo "Example: $0 \"ls -la /home/ec2-user/aGENtrader\""
    exit 1
fi

# Set variables
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
KEY_PATH="$HOME/.ssh/ec2_key.pem"
EC2_DIR="/home/ec2-user/aGENtrader"

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
INNEREOF

    chmod +x ec2-replit-connect.sh
    echo "Created ec2-replit-connect.sh for future connections!"
    echo "Try running a backtest with: ./ec2-replit-connect.sh \"./ec2-multi-agent-backtest.sh --help\""
else
    echo "====================="
    echo "Connection FAILED with exit code $RESULT"
    echo "====================="
    echo "Possible issues:"
    echo "1. The EC2 instance might not be running"
    echo "2. Security group isn't configured to allow SSH access"
    echo "3. The IP address might be incorrect"
    echo "4. The key still has format issues"
fi

# Also update our main run script to use the secret key
cat > ec2-run-revised.sh << 'EOF2'
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
EOF2

chmod +x ec2-run-revised.sh
echo "Created revised ec2-run-revised.sh script for reliable connections"

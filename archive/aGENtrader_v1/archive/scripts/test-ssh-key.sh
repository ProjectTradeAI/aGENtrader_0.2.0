#!/bin/bash
# Test SSH connection and check deployment status

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verify secrets are available
if [ -z "$EC2_SSH_KEY" ] || [ -z "$EC2_PUBLIC_IP" ]; then
    print_error "EC2_SSH_KEY or EC2_PUBLIC_IP secret is not set."
    exit 1
fi

# Configuration
EC2_HOST="ec2-user@$EC2_PUBLIC_IP"
REMOTE_PATH="/home/ec2-user/aGENtrader"

# Format the SSH key properly
print_step "Reformatting SSH key..."
KEY_CONTENT=$(echo "$EC2_SSH_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY-----//' | sed 's/-----END RSA PRIVATE KEY-----//')
FORMATTED_KEY="-----BEGIN RSA PRIVATE KEY-----"

# Split the key into chunks of 64 characters
for ((i=0; i<${#KEY_CONTENT}; i+=64)); do
    FORMATTED_KEY="$FORMATTED_KEY
${KEY_CONTENT:$i:64}"
done

FORMATTED_KEY="$FORMATTED_KEY
-----END RSA PRIVATE KEY-----"

# Create a temporary SSH key file
SSH_KEY_PATH="/tmp/ec2_key.pem"
echo "$FORMATTED_KEY" > "$SSH_KEY_PATH"
chmod 600 "$SSH_KEY_PATH"

print_step "Testing SSH connection..."
if ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$EC2_HOST" "echo Connected successfully"; then
    print_step "SSH connection successful!"
    
    # Check if our deployment directory exists
    print_step "Checking deployment status..."
    if ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "if [ -d $REMOTE_PATH ]; then echo 'Deployment directory exists'; else echo 'Deployment directory does not exist'; fi"; then
        # Check if any Python files are present in the deployment directory
        if ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "find $REMOTE_PATH -name '*.py' | wc -l"; then
            print_step "Checking for key files..."
            # Check for specific key files
            ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "ls -la $REMOTE_PATH/ | grep -E 'run-backtest.sh|setup-ec2.sh'"
        fi
    fi
else
    print_error "Failed to connect to EC2 instance."
    exit 1
fi

# Clean up
rm -f "$SSH_KEY_PATH"
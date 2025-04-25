#!/bin/bash
# Modified EC2 Deployment Script with SSH key format fix for Replit

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
if [ -z "$EC2_SSH_KEY" ]; then
    print_error "EC2_SSH_KEY secret is not set. Please add it to your Replit secrets."
    exit 1
fi

if [ -z "$EC2_PUBLIC_IP" ]; then
    print_error "EC2_PUBLIC_IP secret is not set. Please add it to your Replit secrets."
    exit 1
fi

# Configuration
EC2_HOST="ec2-user@$EC2_PUBLIC_IP"
REMOTE_PATH="/home/ec2-user/aGENtrader"
LOCAL_PATH="$(pwd)"

# Extract key components and format properly with line breaks
print_step "Setting up SSH key with proper formatting..."
KEY_CONTENT=$(echo "$EC2_SSH_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY-----//' | sed 's/-----END RSA PRIVATE KEY-----//')
FORMATTED_KEY="-----BEGIN RSA PRIVATE KEY-----"

# Split the key into chunks of 64 characters as per standard PEM format
for ((i=0; i<${#KEY_CONTENT}; i+=64)); do
    FORMATTED_KEY="$FORMATTED_KEY
${KEY_CONTENT:$i:64}"
done

FORMATTED_KEY="$FORMATTED_KEY
-----END RSA PRIVATE KEY-----"

# Create a temporary SSH key file
mkdir -p ~/.ssh
SSH_KEY_PATH="/tmp/ec2_key.pem"

# Write the properly formatted key
echo "$FORMATTED_KEY" > "$SSH_KEY_PATH"

# Set correct permissions
chmod 600 "$SSH_KEY_PATH"

# Display key information for debugging
echo "Key file created at $SSH_KEY_PATH with proper line breaks"
head -n 2 "$SSH_KEY_PATH"
echo "..."
tail -n 2 "$SSH_KEY_PATH"
echo "Number of lines: $(wc -l < $SSH_KEY_PATH)"

# Test SSH connection
print_step "Testing SSH connection to your EC2 instance..."
if ! ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$EC2_HOST" "echo Connected successfully"; then
    print_error "Failed to connect to EC2 instance. The key format may still be incorrect."
    echo "Let's check if the key is in a valid format:"
    ssh-keygen -l -f "$SSH_KEY_PATH" || echo "Failed to read key"
    exit 1
fi

# Preparing AWS deployment package
print_step "Creating AWS deployment package..."
./create-aws-package.sh

# Upload package to EC2
print_step "Uploading deployment package to EC2..."
scp -i "$SSH_KEY_PATH" aws-deploy-package.tar.gz "$EC2_HOST:/tmp/"

# Extract and setup on EC2
print_step "Extracting and setting up on EC2..."
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "mkdir -p $REMOTE_PATH && tar -xzf /tmp/aws-deploy-package.tar.gz -C /tmp/ && cp -r /tmp/aws-deploy-package/* $REMOTE_PATH/ && rm -rf /tmp/aws-deploy-package.tar.gz /tmp/aws-deploy-package"

# Set up environment on EC2
print_step "Setting up environment on EC2..."
ssh -i "$SSH_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && cp ./setup-ec2.sh . && chmod +x ./setup-ec2.sh && ./setup-ec2.sh"

# Clean up
print_step "Cleaning up..."
rm -f "$SSH_KEY_PATH"

print_step "Deployment completed successfully!"
echo "You can now run backtests on your EC2 instance by SSHing into it and running ./run-backtest.sh"
echo
echo "To monitor the EC2 instance remotely, you can SSH with:"
echo "  ssh ec2-user@$EC2_PUBLIC_IP"
echo "Then run: cd $REMOTE_PATH && ./run-backtest.sh"
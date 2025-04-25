#!/bin/bash
# Script to test the new EC2 key

# Set variables
KEY_PATH="/tmp/new_ec2_key.pem"
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"

echo "===================================================="
echo "  Testing New EC2 SSH Key"
echo "===================================================="
echo "EC2 IP: $EC2_IP"
echo "SSH User: $SSH_USER"
echo

# Create key file from secret
echo "Creating key file from NEW_EC2_KEY secret..."
echo "$NEW_EC2_KEY" > "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Verify key format
echo "Verifying key format..."
head -n 1 "$KEY_PATH" | cat -A
tail -n 1 "$KEY_PATH" | cat -A
echo

# Check if OpenSSL can read the key
echo "Validating key with OpenSSL..."
openssl rsa -in "$KEY_PATH" -check -noout > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Key validation SUCCESS: OpenSSL confirms this is a valid RSA key"
else
    echo "❌ Key validation FAILED: OpenSSL cannot validate this as a valid RSA key"
    echo "Error message: $(openssl rsa -in "$KEY_PATH" -check -noout 2>&1 | head -n 1)"
fi
echo

# Test SSH connection
echo "Testing SSH connection to $EC2_IP..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$EC2_IP" "echo 'Connection successful!'"

if [ $? -eq 0 ]; then
    echo "✅ SSH connection SUCCESS!"
else
    echo "❌ SSH connection FAILED"
    echo "Detailed SSH debug information:"
    ssh -v -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$EC2_IP" "echo test" 2>&1 | grep -i "debug\|error\|denied\|refused"
fi

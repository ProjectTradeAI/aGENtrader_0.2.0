#!/bin/bash
# Script to install AutoGen on EC2

# Check if EC2_PUBLIC_IP and EC2_SSH_KEY are set
if [ -z "$EC2_PUBLIC_IP" ]; then
  echo "ERROR: EC2_PUBLIC_IP environment variable is not set"
  exit 1
fi

if [ -z "$EC2_SSH_KEY" ]; then
  echo "ERROR: EC2_SSH_KEY environment variable is not set"
  exit 1
fi

# Temporary file for SSH key with proper formatting
KEY_FILE=$(mktemp)
echo "Creating properly formatted SSH key..."
echo -e "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_FILE"
echo "$EC2_SSH_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY-----//g' | sed 's/-----END RSA PRIVATE KEY-----//g' | tr -d '\n' | fold -w 64 >> "$KEY_FILE"
echo -e "\n-----END RSA PRIVATE KEY-----" >> "$KEY_FILE"
chmod 600 "$KEY_FILE"

echo "Testing SSH connection..."
if ! ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "echo Connected successfully"; then
  echo "Error: Failed to connect to EC2 instance"
  rm "$KEY_FILE"
  exit 1
fi

echo "Connection successful!"
echo "Installing AutoGen on EC2..."

ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "pip install autogen-agentchat --user"
EXIT_CODE=$?

# Clean up the temporary key file
rm "$KEY_FILE"

if [ $EXIT_CODE -ne 0 ]; then
  echo "Error: Failed to install AutoGen with exit code $EXIT_CODE"
  exit $EXIT_CODE
fi

echo "AutoGen successfully installed on EC2!"
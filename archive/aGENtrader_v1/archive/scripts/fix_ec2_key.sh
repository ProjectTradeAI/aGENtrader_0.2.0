#!/bin/bash

KEY_PATH="/tmp/ec2_key.pem"
FIXED_KEY_PATH="/tmp/fixed_ec2_key.pem"
EC2_IP="51.20.250.135"

echo "==== EC2 SSH Key Fix Tool ===="

# Create a completely fresh key file with proper formatting
# We'll extract the key content and reformat it properly
echo "Creating properly formatted key..."

# Extract the key components while preserving the exact content
grep -v "BEGIN RSA PRIVATE KEY" $KEY_PATH | grep -v "END RSA PRIVATE KEY" > /tmp/key_content.txt

# Create a new key file with proper BEGIN/END markers and the extracted content
echo "-----BEGIN RSA PRIVATE KEY-----" > $FIXED_KEY_PATH
cat /tmp/key_content.txt >> $FIXED_KEY_PATH
echo "-----END RSA PRIVATE KEY-----" >> $FIXED_KEY_PATH

# Set proper permissions
chmod 600 $FIXED_KEY_PATH

echo "New key created at $FIXED_KEY_PATH"
echo

# Generate public key to verify the private key is valid
echo "Attempting to generate public key to verify private key..."
ssh-keygen -y -f $FIXED_KEY_PATH > /tmp/public_key.txt 2>/tmp/keygen_error.txt
if [ $? -eq 0 ]; then
    echo "Private key is valid! Public key generated:"
    head -1 /tmp/public_key.txt
else
    echo "Error generating public key. Key may be invalid or corrupted:"
    cat /tmp/keygen_error.txt
fi

echo
echo "Testing connection with the fixed key..."
ssh -i $FIXED_KEY_PATH -o StrictHostKeyChecking=no -o ConnectTimeout=5 ec2-user@$EC2_IP "echo Connection successful!" 2>/tmp/ssh_error.txt
if [ $? -eq 0 ]; then
    echo "Connection successful!"
else
    echo "Connection failed. Error message:"
    cat /tmp/ssh_error.txt
    echo
    echo "The key format may still be incorrect or there may be network/permission issues."
fi

echo 
echo "If connection still fails, you may need to:"
echo "1. Re-download your key from AWS console"
echo "2. Verify the EC2 security group allows SSH from your IP"
echo "3. Check that the EC2 instance is running"

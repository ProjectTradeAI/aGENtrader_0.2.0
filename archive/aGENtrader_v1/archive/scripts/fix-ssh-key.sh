#!/bin/bash
# Script to fix SSH key format issues

# Set the SSH key path
SSH_KEY_PATH="ec2_ssh_key.pem"

# Display original key file info
echo "Original key file info:"
echo "------------------------"
ls -la "$SSH_KEY_PATH"
file "$SSH_KEY_PATH"
echo

# Fix permissions
echo "Fixing permissions..."
chmod 600 "$SSH_KEY_PATH"
echo "New permissions applied: 600 (only owner can read/write)"

# Check if the key is in the correct format
echo
echo "Checking key format..."
if grep -q "OPENSSH PRIVATE KEY" "$SSH_KEY_PATH"; then
    echo "Key is in OpenSSH format."
elif grep -q "BEGIN RSA PRIVATE KEY" "$SSH_KEY_PATH"; then
    echo "Key is in RSA PEM format."
else
    echo "Key format not recognized. Attempting to fix..."
    
    # Create a backup
    cp "$SSH_KEY_PATH" "${SSH_KEY_PATH}.bak"
    echo "Created backup at ${SSH_KEY_PATH}.bak"
    
    # Try to normalize line endings (convert Windows CRLF to Unix LF)
    tr -d '\r' < "${SSH_KEY_PATH}.bak" > "$SSH_KEY_PATH"
    chmod 600 "$SSH_KEY_PATH"
    echo "Normalized line endings"
    
    # Check if the file contains base64 content without headers
    if ! grep -q "BEGIN" "$SSH_KEY_PATH" && ! grep -q "END" "$SSH_KEY_PATH"; then
        echo "Key appears to be missing headers. Adding PEM headers..."
        mv "$SSH_KEY_PATH" "${SSH_KEY_PATH}.raw"
        echo "-----BEGIN RSA PRIVATE KEY-----" > "$SSH_KEY_PATH"
        cat "${SSH_KEY_PATH}.raw" >> "$SSH_KEY_PATH"
        echo "-----END RSA PRIVATE KEY-----" >> "$SSH_KEY_PATH"
        rm "${SSH_KEY_PATH}.raw"
        chmod 600 "$SSH_KEY_PATH"
    fi
fi

# Show the final key file details
echo
echo "Final key file info:"
echo "------------------------"
ls -la "$SSH_KEY_PATH"
file "$SSH_KEY_PATH"
echo

# Test SSH connection
echo "Testing SSH connection..."
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 ec2-user@$EC2_PUBLIC_IP "echo 'SSH connection successful!'" 2>&1 || echo "SSH connection failed. Please check your EC2 instance details and network configuration."

echo
echo "Fix completed. If you still have issues, you may need to:"
echo "1. Verify that the EC2 instance is running"
echo "2. Verify that the security group allows SSH access"
echo "3. Verify that the EC2_PUBLIC_IP environment variable is correct"
echo "4. Consider re-downloading your key from AWS console"

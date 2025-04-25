#!/bin/bash
# Fix SSH key in the /tmp directory

SSH_KEY="/tmp/ec2_key.pem"
EC2_IP="51.20.250.135"

echo "========================================="
echo "  Fixing SSH key: $SSH_KEY"
echo "  For EC2 server: $EC2_IP"
echo "========================================="

# Check if key file exists
if [ ! -f "$SSH_KEY" ]; then
    echo "Error: Key file $SSH_KEY not found."
    exit 1
fi

# Display original file information
echo "Original key file info:"
echo "----------------------"
ls -la "$SSH_KEY"
file "$SSH_KEY"
head -n 1 "$SSH_KEY" | cat -A
echo 

# Fix permissions
echo "Fixing permissions..."
chmod 600 "$SSH_KEY"
echo "Permissions set to 600 (read/write for owner only)"
echo

# Create a backup
cp "$SSH_KEY" "${SSH_KEY}.bak"
echo "Backup created at ${SSH_KEY}.bak"
echo

# Fix line endings (convert Windows CRLF to Unix LF)
echo "Fixing line endings..."
tr -d '\r' < "${SSH_KEY}.bak" > "${SSH_KEY}.fixed"
mv "${SSH_KEY}.fixed" "$SSH_KEY"
chmod 600 "$SSH_KEY"
echo

# Check for common key format issues
echo "Checking key format..."
if grep -q "BEGIN OPENSSH PRIVATE KEY" "$SSH_KEY"; then
    echo "Key is in OpenSSH format."
    format="openssh"
elif grep -q "BEGIN RSA PRIVATE KEY" "$SSH_KEY"; then
    echo "Key is in RSA PEM format."
    format="pem"
elif grep -q "BEGIN PRIVATE KEY" "$SSH_KEY"; then
    echo "Key is in PKCS#8 format."
    format="pkcs8"
else
    echo "Key format not recognized."
    
    # Check if it's a base64 string without headers
    if grep -q -E '^[A-Za-z0-9+/=]+$' "$SSH_KEY"; then
        echo "Key appears to be a raw base64 string. Adding PEM headers..."
        
        # Save current content
        mv "$SSH_KEY" "${SSH_KEY}.raw"
        
        # Add PEM headers
        echo "-----BEGIN RSA PRIVATE KEY-----" > "$SSH_KEY"
        cat "${SSH_KEY}.raw" >> "$SSH_KEY"
        echo "-----END RSA PRIVATE KEY-----" >> "$SSH_KEY"
        
        chmod 600 "$SSH_KEY"
        format="fixed_pem"
    else
        format="unknown"
    fi
fi

# If OpenSSH format, try to convert to PEM
if [ "$format" == "openssh" ]; then
    echo "Converting OpenSSH format to PEM..."
    cp "$SSH_KEY" "${SSH_KEY}.openssh"
    ssh-keygen -p -m PEM -f "$SSH_KEY" -N ""
    chmod 600 "$SSH_KEY"
    echo "Conversion completed."
fi

# Display final key information
echo
echo "Fixed key file info:"
echo "------------------"
ls -la "$SSH_KEY"
file "$SSH_KEY"
head -n 1 "$SSH_KEY" | cat -A
echo

# Try connecting
echo "Testing SSH connection to $EC2_IP..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 ec2-user@$EC2_IP "echo Connection successful!" || echo "Connection failed."

echo
echo "If the connection still fails, try:"
echo "1. Check that the EC2 instance is running"
echo "2. Check that the security group allows SSH access from your IP"
echo "3. Verify you're using the correct username (ec2-user)"
echo "4. Verify you're using the correct IP address"
echo "5. Re-download the key from AWS console"

# Export EC2 variables for convenience
echo
echo "Setting environment variables for convenience:"
echo "export EC2_KEY=\"$SSH_KEY\""
echo "export EC2_IP=\"$EC2_IP\""
export EC2_KEY="$SSH_KEY"
export EC2_IP="$EC2_IP"
echo "Variables set. You can now use: ssh -i \$EC2_KEY ec2-user@\$EC2_IP"

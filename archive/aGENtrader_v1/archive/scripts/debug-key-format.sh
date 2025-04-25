#!/bin/bash
# Advanced SSH key debugging and fixing script

# Set the SSH key path
SSH_KEY_PATH="ec2_ssh_key.pem"

echo "=================================================="
echo "       SSH Key Format Debugging & Fixing Tool     "
echo "=================================================="
echo

if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "Error: SSH key file '$SSH_KEY_PATH' not found."
    exit 1
fi

# Function to check and report the key format
check_format() {
    local key_file="$1"
    
    echo "Key format details:"
    echo "------------------"
    
    # Check file type
    file_type=$(file "$key_file")
    echo "File command output: $file_type"
    
    # Check beginning of file
    head -n 1 "$key_file" | cat -A
    
    # Check for common formats
    if grep -q "BEGIN OPENSSH PRIVATE KEY" "$key_file"; then
        echo "Format detected: OpenSSH format (newer)"
        format="openssh"
    elif grep -q "BEGIN RSA PRIVATE KEY" "$key_file"; then
        echo "Format detected: PEM format (traditional)"
        format="pem"
    elif grep -q "BEGIN PRIVATE KEY" "$key_file"; then
        echo "Format detected: PKCS#8 format"
        format="pkcs8"
    elif grep -q "BEGIN DSA PRIVATE KEY" "$key_file"; then
        echo "Format detected: DSA format"
        format="dsa"
    elif grep -q "BEGIN EC PRIVATE KEY" "$key_file"; then
        echo "Format detected: EC format"
        format="ec"
    else
        echo "No standard key format detected."
        format="unknown"
    fi
    
    # Check for text vs binary
    if LC_ALL=C grep -q '[^[:print:][:space:]]' "$key_file"; then
        echo "File contains binary data."
        is_binary="yes"
    else
        echo "File appears to be text."
        is_binary="no"
    fi
    
    # Check line endings
    if grep -q $'\r\n' "$key_file"; then
        echo "Line endings: CRLF (Windows-style)"
        line_ending="crlf"
    else
        echo "Line endings: LF (Unix-style)"
        line_ending="lf"
    fi
    
    # Check permissions
    perms=$(stat -c '%a' "$key_file")
    echo "Current permissions: $perms"
    
    # Return results
    echo "$format;$is_binary;$line_ending;$perms"
}

# Backup the original key
cp "$SSH_KEY_PATH" "${SSH_KEY_PATH}.original"
echo "Original key backed up to ${SSH_KEY_PATH}.original"
echo

# Check initial format
echo "Analyzing original key..."
result=$(check_format "$SSH_KEY_PATH")
IFS=';' read -r format is_binary line_ending perms <<< "$result"
echo

# Fix permissions
if [ "$perms" != "600" ]; then
    echo "Fixing permissions to 600..."
    chmod 600 "$SSH_KEY_PATH"
    echo "Done."
    echo
fi

# Fix line endings if needed
if [ "$line_ending" == "crlf" ]; then
    echo "Converting CRLF to LF line endings..."
    tr -d '\r' < "$SSH_KEY_PATH" > "${SSH_KEY_PATH}.fixed"
    mv "${SSH_KEY_PATH}.fixed" "$SSH_KEY_PATH"
    chmod 600 "$SSH_KEY_PATH"
    echo "Done."
    echo
fi

# Fix format issues
if [ "$format" == "unknown" ]; then
    echo "Attempting to fix unknown format..."
    
    # Check if it might be base64 content without headers
    if grep -q -E '^[A-Za-z0-9+/=]+$' "$SSH_KEY_PATH"; then
        echo "Appears to be base64 encoded content without headers."
        echo "Adding RSA PEM headers..."
        
        mv "$SSH_KEY_PATH" "${SSH_KEY_PATH}.raw"
        echo "-----BEGIN RSA PRIVATE KEY-----" > "$SSH_KEY_PATH"
        # Format base64 content with proper line length
        fold -w 64 "${SSH_KEY_PATH}.raw" >> "$SSH_KEY_PATH"
        echo "-----END RSA PRIVATE KEY-----" >> "$SSH_KEY_PATH"
        rm "${SSH_KEY_PATH}.raw"
        chmod 600 "$SSH_KEY_PATH"
        echo "Done."
        echo
    else
        echo "Unable to automatically fix unknown format."
        echo "You may need to re-download your key from AWS console."
        echo
    fi
    
    # Recheck format after fix attempt
    echo "Rechecking format after fixes..."
    result=$(check_format "$SSH_KEY_PATH")
    IFS=';' read -r format is_binary line_ending perms <<< "$result"
    echo
fi

# Try to convert OpenSSH to PEM if needed
if [ "$format" == "openssh" ]; then
    echo "Converting OpenSSH format to PEM format..."
    if command -v ssh-keygen &> /dev/null; then
        cp "$SSH_KEY_PATH" "${SSH_KEY_PATH}.openssh"
        ssh-keygen -p -m PEM -f "$SSH_KEY_PATH" -N ""
        echo "Done."
    else
        echo "ssh-keygen not available. Cannot convert format."
    fi
    echo
fi

# Final check
echo "Final key status:"
echo "-----------------"
check_format "$SSH_KEY_PATH"
echo

# Test connection
echo "Testing SSH connection..."
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 ec2-user@$EC2_PUBLIC_IP "echo 'SSH connection successful!'" 2>&1 || echo "SSH connection failed. Please check your EC2 instance details and network configuration."

echo
echo "Fix attempts completed. If you still have issues:"
echo "1. Verify that the EC2 instance is running"
echo "2. Verify that the security group allows SSH access"
echo "3. Verify that the EC2_PUBLIC_IP environment variable is correct ($EC2_PUBLIC_IP)"
echo "4. Consider re-downloading your key from AWS console"
echo
echo "You can also try to use the original backup at ${SSH_KEY_PATH}.original if needed."

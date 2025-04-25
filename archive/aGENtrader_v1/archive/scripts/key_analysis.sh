#!/bin/bash

# Create a simple test file
echo "Analysis of key content"
echo "======================"

# Write the key to a file
KEY_FILE="/tmp/exact_key.pem"
echo "$NEW_EC2_KEY" > "$KEY_FILE"
chmod 600 "$KEY_FILE"

# Show file info
echo "File size in bytes: $(wc -c < "$KEY_FILE")"
echo "File in hexdump:"
hexdump -C "$KEY_FILE" | head -10
echo "..."

# Check if the key content is actually split into lines
if grep -q $'\n' "$KEY_FILE"; then
    echo "Key contains newlines"
else
    echo "Key does not contain newlines - this is a problem"
fi

echo
echo "====== RECOMMENDATION ======"
echo "Since we're having persistent issues with the SSH key format, please:"
echo
echo "1. Create a new EC2 key pair in the AWS console"
echo "2. Download the new .pem file to your local machine"
echo "3. Open the .pem file in a text editor (like Notepad++ or VS Code)"
echo "4. Copy the EXACT content, including all line breaks"
echo "5. Create a new Replit secret with this content"
echo
echo "In the meantime, use the AWS console browser-based access as described in use-aws-console.md"

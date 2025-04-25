#!/bin/bash

# Reuse the key formatting approach from direct-ssh-command.sh
echo "[STEP] Reformatting SSH key..."
# Convert any \n literals to actual newlines
PRIVATE_KEY=$(echo "$EC2_SSH_KEY" | sed 's/\\n/\n/g')
# Store the key in a temporary file
TMP_KEY_FILE=$(mktemp)
echo "$PRIVATE_KEY" > $TMP_KEY_FILE
chmod 600 $TMP_KEY_FILE

echo "[STEP] Connecting to EC2 instance..."
# Use the temporary key file for SCP
scp -o StrictHostKeyChecking=no -i $TMP_KEY_FILE run_simplified_test.py "ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/"

# Check if the transfer was successful
if [ $? -eq 0 ]; then
    echo "[STEP] File transferred successfully!"
else
    echo "[ERROR] File transfer failed!"
    # Output the first few lines of the key file to debug (be careful not to expose too much)
    echo "[DEBUG] First line of key file:"
    head -n 1 $TMP_KEY_FILE | cut -c 1-10
fi

# Clean up
rm $TMP_KEY_FILE

#!/bin/bash

# Format the private key
PRIVATE_KEY=$(echo "$EC2_SSH_KEY" | sed 's/\\n/\n/g')
TMP_KEY_FILE=$(mktemp)
echo "$PRIVATE_KEY" > $TMP_KEY_FILE
chmod 600 $TMP_KEY_FILE

# Transfer the file using scp
echo "[STEP] Transferring simplified test file to EC2..."
scp -o StrictHostKeyChecking=no -i $TMP_KEY_FILE run_simplified_test.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/

# Cleanup
rm $TMP_KEY_FILE
echo "[STEP] File transfer complete!"

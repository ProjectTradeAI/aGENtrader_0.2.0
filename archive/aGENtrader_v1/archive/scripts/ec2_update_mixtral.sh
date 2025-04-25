#!/bin/bash

# Set up EC2 connection info
EC2_USER="ec2-user"
SSH_KEY="ec2_ssh_key.pem"

# Command to execute on EC2
EC2_COMMAND="cd /home/ec2-user/aGENtrader && chmod +x download_mixtral.py && python3 download_mixtral.py"

# Create a temporary file with the command
TMP_CMD_FILE=$(mktemp)
echo "$EC2_COMMAND" > "$TMP_CMD_FILE"

# Execute the command on EC2
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$TMP_CMD_FILE" ${EC2_USER}@${EC2_PUBLIC_IP}:/tmp/ec2_command.sh
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_PUBLIC_IP} "chmod +x /tmp/ec2_command.sh && nohup /tmp/ec2_command.sh > /home/ec2-user/aGENtrader/mixtral_download.log 2>&1 &"

# Cleanup
rm "$TMP_CMD_FILE"

echo "The Mixtral model download has been started in the background on the EC2 instance."
echo "The log will be saved to /home/ec2-user/aGENtrader/mixtral_download.log"

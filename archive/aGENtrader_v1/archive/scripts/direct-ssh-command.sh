#!/bin/bash

# This script bypasses the key file and uses a string command approach

# SSH command options
EC2_IP="51.20.250.135"
SSH_USER="ec2-user"
COMMAND="echo Hello from EC2"

# Get the key content as a string
KEY_CONTENT=$(cat /tmp/ec2_key.pem)

# Create a temporary script that uses ssh command with the key content
TMP_SCRIPT=$(mktemp)
cat > $TMP_SCRIPT << INNEREOF
#!/bin/bash
# This is a generated script with embedded key
mkdir -p ~/.ssh
echo '$KEY_CONTENT' > ~/.ssh/temp_key
chmod 600 ~/.ssh/temp_key
ssh -i ~/.ssh/temp_key -o StrictHostKeyChecking=no $SSH_USER@$EC2_IP "$COMMAND"
rm ~/.ssh/temp_key
INNEREOF

chmod +x $TMP_SCRIPT
echo "Running SSH command via embedded key script..."
$TMP_SCRIPT
rm $TMP_SCRIPT

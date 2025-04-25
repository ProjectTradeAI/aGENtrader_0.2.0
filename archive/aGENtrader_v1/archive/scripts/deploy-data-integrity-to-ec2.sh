#!/bin/bash
# Deploy data integrity implementation to EC2

# Configuration
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
KEY_PATH="/tmp/ec2_key.pem"
EC2_DIR="/home/ec2-user/aGENtrader"
DEPLOYMENT_ARCHIVE="data_integrity_deployment.tar.gz"

# Create key file from secret
echo "Creating key file from EC2_KEY secret..."
echo "$EC2_KEY" > "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Test connection
echo "Testing connection to $EC2_IP with user $SSH_USER..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$EC2_IP" "echo Connection successful! && whoami && pwd"

if [ $? -ne 0 ]; then
  echo "❌ Connection failed."
  echo "Please check that:"
  echo "1. You've added the correct EC2_KEY to secrets"
  echo "2. The EC2 instance is running"
  echo "3. The security group allows SSH from your IP"
  exit 1
fi

echo "✅ Connection successful!"

# Copy the deployment archive to EC2
echo "Copying deployment archive to EC2..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$DEPLOYMENT_ARCHIVE" "$SSH_USER@$EC2_IP:~/"

if [ $? -ne 0 ]; then
  echo "❌ Failed to copy deployment archive to EC2."
  exit 1
fi

echo "✅ Deployment archive copied successfully."

# Extract and apply on EC2
echo "Extracting and applying data integrity implementation on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "
  cd $EC2_DIR &&
  mkdir -p data_integrity &&
  tar -xzf ~/$DEPLOYMENT_ARCHIVE -C data_integrity &&
  cd data_integrity &&
  chmod +x apply-data-integrity.sh &&
  ./apply-data-integrity.sh &&
  cd .. &&
  rm ~/$DEPLOYMENT_ARCHIVE
"

if [ $? -ne 0 ]; then
  echo "❌ Failed to apply data integrity implementation on EC2."
  exit 1
fi

echo "✅ Data integrity implementation applied successfully!"
echo
echo "Next steps:"
echo "1. Restart your trading system on EC2 to apply the changes."
echo "2. Verify that agents properly disclose when they don't have access to real data."
echo
echo "Your trading system now ensures data integrity with comprehensive validation!"

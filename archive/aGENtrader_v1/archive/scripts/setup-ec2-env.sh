#!/bin/bash
# Script to set up EC2 environment for backtesting

# Source the SSH key setup script if it exists
if [ -f "fix-ssh-key.sh" ]; then
    source fix-ssh-key.sh
fi

# Set variables
SSH_KEY_PATH="ec2_ssh_key.pem"
SSH_USER="ec2-user"
EC2_IP="${EC2_PUBLIC_IP}"

echo "Setting up EC2 instance for backtesting..."

# Create a remote script
cat > remote_setup.sh << 'REMOTE_SCRIPT'
#!/bin/bash
echo "Setting up environment for backtesting..."

# Check if psycopg2 is available
if python -c "import psycopg2" 2>/dev/null; then
  echo "psycopg2 is already available"
else
  echo "Adding psycopg2-binary to the environment..."
  pip install psycopg2-binary
fi

# Check if other dependencies are available
for pkg in "python-dotenv" "pandas" "numpy" "matplotlib"; do
  if python -c "import ${pkg//-/_}" 2>/dev/null; then
    echo "$pkg is already available"
  else
    echo "Adding $pkg to the environment..."
    pip install $pkg
  fi
done

# Try to check for autogen
if python -c "import autogen" 2>/dev/null; then
  echo "autogen is already available"
else
  echo "Adding pyautogen to the environment..."
  pip install pyautogen
fi

# Verify packages
echo "Verifying available packages:"
pip list | grep -E "psycopg2|dotenv|autogen|pandas|numpy|matplotlib"

echo "Environment setup completed!"
REMOTE_SCRIPT

# Transfer the script to EC2
echo "Transferring setup script to EC2..."
scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no remote_setup.sh "${SSH_USER}@${EC2_IP}:~/remote_setup.sh"

# Execute the script on EC2
echo "Executing setup script on EC2..."
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "${SSH_USER}@${EC2_IP}" "chmod +x ~/remote_setup.sh && ~/remote_setup.sh"

# Clean up the temporary script
rm remote_setup.sh

echo "EC2 environment setup completed."
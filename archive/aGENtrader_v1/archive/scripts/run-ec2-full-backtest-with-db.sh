#!/bin/bash
# Script to run full backtests on EC2 with complete database connectivity

# Source the SSH key setup script if it exists
if [ -f "fix-ssh-key.sh" ]; then
    source fix-ssh-key.sh
fi

# Set variables
SSH_KEY_PATH="ec2_ssh_key.pem"
SSH_USER="ec2-user"
EC2_IP="${EC2_PUBLIC_IP}"

echo "Preparing to run full backtest on EC2 with complete database connectivity..."

# Create a command script for EC2
cat > ec2_full_backtest.sh << 'REMOTE_CMD'
#!/bin/bash
echo "Setting up environment for full backtesting with database..."

# Create a setup script that will be executed on the EC2 instance
cat > /tmp/prepare_full_backtest.sh << 'SETUP_SCRIPT'
#!/bin/bash
# Ensure we have the necessary Python packages
echo "Checking and preparing Python environment for full backtest..."

# The command below runs Python to check for psycopg2 and installs it if missing
python3 -c '
import importlib.util
import subprocess
import sys

def check_install(package_name, pip_name=None):
    if pip_name is None:
        pip_name = package_name
    
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print(f"{package_name} not found, installing {pip_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        print(f"{pip_name} installed successfully")
    else:
        print(f"{package_name} is already installed")

# Check and install necessary packages
check_install("psycopg2", "psycopg2-binary")
check_install("dotenv", "python-dotenv")
check_install("autogen", "pyautogen")
check_install("pandas")
check_install("numpy")
check_install("matplotlib")
'

echo "Environment prepared for full database-connected backtest"
SETUP_SCRIPT

# Make the setup script executable and run it
chmod +x /tmp/prepare_full_backtest.sh
/tmp/prepare_full_backtest.sh

# Run the full backtest
echo "Running full backtest with complete database connectivity..."
cd ~/aGENtrader
python3 run_simplified_full_backtest.py --days 30 --symbol BTCUSDT --interval 1h

echo "Full backtest completed"
REMOTE_CMD

# Transfer the command script to EC2
echo "Transferring command script to EC2..."
scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no ec2_full_backtest.sh "${SSH_USER}@${EC2_IP}:~/ec2_full_backtest.sh"

# Execute the commands on EC2
echo "Executing command script on EC2..."
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "${SSH_USER}@${EC2_IP}" "chmod +x ~/ec2_full_backtest.sh && ~/ec2_full_backtest.sh"

# Clean up the temporary script
rm ec2_full_backtest.sh

echo "EC2 full backtest with complete database connectivity completed."

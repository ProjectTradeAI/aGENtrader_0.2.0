#!/bin/bash
echo "Setting up environment for backtesting with database..."

# Create a setup script that will be executed on the EC2 instance
cat > /tmp/prepare_environment.sh << 'SETUP_SCRIPT'
#!/bin/bash
# Ensure we have the necessary Python packages
echo "Checking and preparing Python environment..."

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

echo "Environment prepared for database connectivity"
SETUP_SCRIPT

# Make the setup script executable and run it
chmod +x /tmp/prepare_environment.sh
/tmp/prepare_environment.sh

# Run the backtest
echo "Running backtest with database connectivity..."
cd ~/aGENtrader
python run_collaborative_decision_test.py

echo "Backtest completed"

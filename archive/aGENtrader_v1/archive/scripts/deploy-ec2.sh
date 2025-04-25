#!/bin/bash
# EC2 Deployment Script for Trading Bot with Local LLM

# Configuration
# These will be set automatically by the deploy-from-replit.sh script
# when running from Replit, or can be set manually when running locally
EC2_HOST=${EC2_HOST:-"ec2-user@$EC2_PUBLIC_IP"}
EC2_KEY_PATH=${EC2_KEY_PATH:-"/tmp/ec2_key.pem"}
PROJECT_PATH=$(pwd)
REMOTE_PATH="/home/ec2-user/aGENtrader" # Using existing directory

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_connection() {
    print_step "Checking connection to EC2 instance..."
    if ssh -i "$EC2_KEY_PATH" -o ConnectTimeout=5 "$EC2_HOST" "echo Connected successfully"; then
        echo "Connection established!"
    else
        print_error "Failed to connect to EC2 instance!"
        echo "Please check your EC2_HOST and EC2_KEY_PATH variables."
        exit 1
    fi
}

prepare_remote_directory() {
    print_step "Preparing remote directory..."
    ssh -i "$EC2_KEY_PATH" "$EC2_HOST" "mkdir -p $REMOTE_PATH"
}

copy_project_files() {
    print_step "Copying project files to EC2 instance..."
    rsync -avz --progress -e "ssh -i $EC2_KEY_PATH" \
        --exclude ".git" \
        --exclude "node_modules" \
        --exclude "venv" \
        --exclude "__pycache__" \
        --exclude ".vscode" \
        --exclude "data/logs" \
        "$PROJECT_PATH/" "$EC2_HOST:$REMOTE_PATH/"
    
    echo "Project files copied successfully!"
}

setup_environment() {
    print_step "Setting up environment on EC2 instance..."
    ssh -i "$EC2_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && bash -s" << 'EOF'
    echo "Creating necessary directories..."
    mkdir -p data/logs data/backtest_results models/llm_models

    if [ ! -f .env ]; then
        echo "Creating .env file..."
        touch .env
        echo "Please update the .env file with your credentials!"
    fi

    echo "Checking for Python dependencies..."
    if ! command -v python3 &> /dev/null; then
        echo "Python not found! Installing Python..."
        sudo yum update -y
        sudo yum install -y python3 python3-pip python3-devel gcc
    fi

    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt

    # Check for and install additional LLM dependencies
    if ! pip3 list | grep -q "llama-cpp-python"; then
        echo "Installing LLM dependencies..."
        pip3 install llama-cpp-python huggingface_hub
    fi

    echo "Setting up configuration for AWS..."
    if [ ! -f utils/llm_integration/aws_config.py ]; then
        mkdir -p utils/llm_integration
        cat > utils/llm_integration/aws_config.py << 'PYEOF'
"""AWS-specific configuration for LLM integration"""

# AWS instance-specific settings
AWS_DEPLOYMENT = True

# Model configuration
DEFAULT_MODEL_PATH = "models/llm_models/llama-2-7b-chat.Q4_K_M.gguf"
DEFAULT_MODEL_REPO = "TheBloke/Llama-2-7B-Chat-GGUF"
DEFAULT_MODEL_FILE = "llama-2-7b-chat.Q4_K_M.gguf"

# Performance settings for EC2
import multiprocessing
DEFAULT_CONTEXT_LENGTH = 4096
NUM_THREADS = multiprocessing.cpu_count()  # Use all available CPU cores
N_GPU_LAYERS = 0  # Set to 0 if no GPU, or higher for GPU instances

# Timeout settings (in seconds)
DEFAULT_TIMEOUT = 60
ANALYST_TIMEOUT = 90
DECISION_TIMEOUT = 120
PYEOF
        echo "AWS configuration created!"
    fi

    echo "Environment setup complete!"
EOF
}

download_models() {
    print_step "Setting up LLM models on EC2 instance..."
    ssh -i "$EC2_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && bash -s" << 'EOF'
    echo "Checking if models need to be downloaded..."
    
    if [ ! -f models/llm_models/llama-2-7b-chat.Q4_K_M.gguf ]; then
        echo "Downloading the Llama-2-7B model (this may take a while)..."
        python3 -c "
from huggingface_hub import hf_hub_download
import os

os.makedirs('models/llm_models', exist_ok=True)
print('Downloading model from Hugging Face...')
hf_hub_download('TheBloke/Llama-2-7B-Chat-GGUF', 
                'llama-2-7b-chat.Q4_K_M.gguf', 
                local_dir='models/llm_models')
print('Model downloaded successfully!')
"
    else
        echo "Model already downloaded."
    fi
EOF
}

setup_pm2() {
    print_step "Setting up PM2 process manager..."
    ssh -i "$EC2_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && bash -s" << 'EOF'
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        echo "Node.js not found! Installing Node.js..."
        curl -fsSL https://rpm.nodesource.com/setup_16.x | sudo bash -
        sudo yum install -y nodejs
    fi

    # Install PM2 if not already installed
    if ! command -v pm2 &> /dev/null; then
        echo "Installing PM2..."
        sudo npm install -g pm2
    fi

    # Check if backtesting PM2 configuration exists
    if [ ! -f backtesting-ecosystem.config.cjs ]; then
        echo "Copying backtesting PM2 configuration..."
        cp /home/ec2-user/aGENtrader/backtesting-ecosystem.config.cjs .
    fi
    
    # Update psutil for the monitoring script
    echo "Installing psutil for LLM monitoring..."
    pip3 install --user psutil

    # Make sure logs directory exists
    mkdir -p logs
    
    # Create a starter script to easily run backtests
    cat > run-backtest.sh << 'SHEOF'
#!/bin/bash
# Script to easily run backtests with different parameters

# Default values
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-01"
END_DATE="2025-03-15"
TIMEOUT="120"
RISK="0.02"
BALANCE="10000"

# Usage function
usage() {
  echo "Usage: $0 [-s SYMBOL] [-i INTERVAL] [-f START_DATE] [-t END_DATE] [-o TIMEOUT] [-r RISK] [-b BALANCE]"
  echo "  -s SYMBOL      Trading symbol (default: BTCUSDT)"
  echo "  -i INTERVAL    Time interval (default: 1h)"
  echo "  -f START_DATE  Start date (default: 2025-03-01)"
  echo "  -t END_DATE    End date (default: 2025-03-15)"
  echo "  -o TIMEOUT     Analysis timeout in seconds (default: 120)"
  echo "  -r RISK        Risk per trade as decimal (default: 0.02)"
  echo "  -b BALANCE     Initial balance (default: 10000)"
  exit 1
}

# Parse command line arguments
while getopts "s:i:f:t:o:r:b:h" opt; do
  case $opt in
    s) SYMBOL=$OPTARG ;;
    i) INTERVAL=$OPTARG ;;
    f) START_DATE=$OPTARG ;;
    t) END_DATE=$OPTARG ;;
    o) TIMEOUT=$OPTARG ;;
    r) RISK=$OPTARG ;;
    b) BALANCE=$OPTARG ;;
    h) usage ;;
    \?) usage ;;
  esac
done

echo "Running backtest with:"
echo "Symbol: $SYMBOL"
echo "Interval: $INTERVAL"
echo "Start date: $START_DATE"
echo "End date: $END_DATE"
echo "Analysis timeout: $TIMEOUT"
echo "Risk per trade: $RISK"
echo "Initial balance: $BALANCE"
echo

# Update the PM2 configuration
sed -i "s|args: '.*'|args: 'run_backtest_with_local_llm.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --analysis_timeout $TIMEOUT --risk_per_trade $RISK --initial_balance $BALANCE'|" backtesting-ecosystem.config.cjs

# Run with PM2
echo "Starting backtest with PM2..."
pm2 start backtesting-ecosystem.config.cjs
pm2 logs trading-bot-backtesting
SHEOF

    chmod +x run-backtest.sh
    
    echo "Starting LLM monitoring..."
    pm2 start backtesting-ecosystem.config.cjs --only llm-monitoring
    pm2 save
    
    # Set PM2 to start on boot
    sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $(whoami) --hp $(echo $HOME)
    
    echo "PM2 setup complete. Use ./run-backtest.sh to start backtests."
EOF
}

test_backtest() {
    print_step "Running a test backtest..."
    ssh -i "$EC2_KEY_PATH" "$EC2_HOST" "cd $REMOTE_PATH && bash -s" << 'EOF'
    echo "Running a quick test backtest..."
    python3 run_backtest_with_local_llm.py \
      --symbol BTCUSDT \
      --interval 1h \
      --start_date 2025-03-01 \
      --end_date 2025-03-02 \
      --analysis_timeout 120 \
      --output_dir data/backtest_results
EOF
}

# Main script execution
echo "======== Trading Bot EC2 Deployment ========"
echo "This script will deploy your trading bot to an EC2 instance."
echo "Please ensure you have updated the configuration variables at the top of this script."
echo

read -p "Do you want to continue with deployment? (y/n): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Execute deployment steps
check_connection
prepare_remote_directory
copy_project_files
setup_environment

read -p "Do you want to download LLM models? This may take some time. (y/n): " download_confirm
if [[ $download_confirm == [yY] || $download_confirm == [yY][eE][sS] ]]; then
    download_models
else
    print_warning "Skipping model download. Make sure to download models manually!"
fi

read -p "Do you want to set up PM2 process manager? (y/n): " pm2_confirm
if [[ $pm2_confirm == [yY] || $pm2_confirm == [yY][eE][sS] ]]; then
    setup_pm2
else
    print_warning "Skipping PM2 setup. You'll need to manage processes manually."
fi

read -p "Do you want to run a test backtest? (y/n): " test_confirm
if [[ $test_confirm == [yY] || $test_confirm == [yY][eE][sS] ]]; then
    test_backtest
else
    print_warning "Skipping test backtest."
fi

print_step "Deployment completed successfully!"
echo "Next steps:"
echo "1. SSH into your EC2 instance: ssh -i $EC2_KEY_PATH $EC2_HOST"
echo "2. Navigate to the project directory: cd $REMOTE_PATH"
echo "3. Update the .env file with your API keys and credentials"
echo "4. If you didn't download models, run the download command manually"
echo "5. Run a backtest using the convenience script: ./run-backtest.sh"
echo "   Or customize parameters: ./run-backtest.sh -s BTCUSDT -i 1h -f 2025-03-01 -t 2025-03-15 -o 120"
echo
echo "Thank you for using the Trading Bot EC2 Deployment script!"
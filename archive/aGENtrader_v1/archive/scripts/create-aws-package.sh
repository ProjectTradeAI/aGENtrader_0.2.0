#!/bin/bash
# Create a package for AWS EC2 deployment

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

# Prepare package
print_step "Creating deployment package..."

# Create deployment directory
DEPLOY_DIR="aws-deploy-package"
mkdir -p "$DEPLOY_DIR"

# Copy necessary files
print_step "Copying files to package..."

# Main directories
for dir in agents config data models orchestration scripts server shared strategies utils; do
    if [ -d "$dir" ]; then
        mkdir -p "$DEPLOY_DIR/$dir"
        cp -r "$dir"/* "$DEPLOY_DIR/$dir"
    fi
done

# Create necessary subdirectories
mkdir -p "$DEPLOY_DIR/data/logs"
mkdir -p "$DEPLOY_DIR/data/backtest_results"
mkdir -p "$DEPLOY_DIR/models/llm_models"
mkdir -p "$DEPLOY_DIR/logs"
mkdir -p "$DEPLOY_DIR/docs"

# Copy main Python files
cp *.py "$DEPLOY_DIR"

# Copy shell scripts
cp *.sh "$DEPLOY_DIR"

# Copy configuration files
cp backtesting-ecosystem.config.cjs "$DEPLOY_DIR"
cp ecosystem.config.cjs "$DEPLOY_DIR"
cp ecosystem.config.js "$DEPLOY_DIR"
cp requirements.txt "$DEPLOY_DIR"

# Copy documentation
cp docs/EC2_DEPLOYMENT_FROM_REPLIT.md "$DEPLOY_DIR/docs"
cp *.md "$DEPLOY_DIR"

# Create .env file with placeholder for OpenAI key
cat > "$DEPLOY_DIR/.env" << 'EOF'
# OpenAI API Key - Required for trading agents
OPENAI_API_KEY=

# Database Configuration - Optional, configure if using external DB
DATABASE_URL=

# Deployment Configuration
DEPLOYMENT_ENV=ec2
EOF

# Create EC2 setup script
cat > "$DEPLOY_DIR/setup-ec2.sh" << 'EOF'
#!/bin/bash

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

# Check if running as root
if [ "$(id -u)" -eq 0 ]; then
    print_error "This script should not be run as root. Please run as the ec2-user."
    exit 1
fi

# Update system packages
print_step "Updating system packages..."
sudo yum update -y

# Install Python and development tools
print_step "Installing Python and development tools..."
sudo yum install -y python3 python3-pip python3-devel gcc gcc-c++ make

# Install Node.js and npm
print_step "Installing Node.js and npm..."
curl -fsSL https://rpm.nodesource.com/setup_16.x | sudo bash -
sudo yum install -y nodejs

# Install PM2 globally
print_step "Installing PM2 process manager..."
sudo npm install -g pm2

# Install Python dependencies
print_step "Installing Python dependencies..."
pip3 install --user -r requirements.txt
pip3 install --user llama-cpp-python huggingface_hub psutil

# Download LLM model
read -p "Do you want to download the Llama-2-7B model? This will take some time. (y/n): " download_model
if [[ $download_model == [yY] || $download_model == [yY][eE][sS] ]]; then
    print_step "Downloading the Llama-2-7B model from Hugging Face..."
    python3 -c "
from huggingface_hub import hf_hub_download
import os

os.makedirs('models/llm_models', exist_ok=True)
print('Downloading model from Hugging Face...')
try:
    hf_hub_download('TheBloke/Llama-2-7B-Chat-GGUF', 
                    'llama-2-7b-chat.Q4_K_M.gguf', 
                    local_dir='models/llm_models')
    print('Model downloaded successfully!')
except Exception as e:
    print(f'Error downloading model: {str(e)}')
    print('Please try downloading manually later.')
"
else
    print_warning "Skipping model download. You'll need to download it manually later."
fi

# Set up PM2 to start on boot
print_step "Setting up PM2 to start on boot..."
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $(whoami) --hp $(echo $HOME)

# Configure OpenAI API key
print_step "Setting up OpenAI API key..."
read -p "Please enter your OpenAI API key: " openai_key
if [ ! -z "$openai_key" ]; then
    sed -i "s/OPENAI_API_KEY=/OPENAI_API_KEY=$openai_key/" .env
    echo "OpenAI API key added to .env file"
else
    print_warning "No OpenAI API key provided. You'll need to add it manually to the .env file."
fi

# Make scripts executable
chmod +x run-backtest.sh
chmod +x *.sh

print_step "Setup complete!"
echo "You can now run a backtest using: ./run-backtest.sh"
echo "For more options, run: ./run-backtest.sh -h"
EOF

# Make the setup script executable
chmod +x "$DEPLOY_DIR/setup-ec2.sh"

# Create a simple README
cat > "$DEPLOY_DIR/README_AWS.md" << 'EOF'
# AWS EC2 Deployment Package

This package contains everything needed to run the trading bot with local LLM on an AWS EC2 instance.

## Quick Start

1. Upload this entire package to your EC2 instance:
   ```
   scp -r aws-deploy-package ec2-user@YOUR_EC2_IP:~/
   ```

2. SSH into your EC2 instance:
   ```
   ssh ec2-user@YOUR_EC2_IP
   ```

3. Navigate to the deployment package:
   ```
   cd aws-deploy-package
   ```

4. Run the setup script:
   ```
   ./setup-ec2.sh
   ```

5. Run a backtest:
   ```
   ./run-backtest.sh
   ```

## Configuration

- Edit the `.env` file to add your API keys and other configuration
- Customize backtest parameters in `run-backtest.sh`
- Monitor processes with PM2: `pm2 status`
- View logs with: `pm2 logs trading-bot-backtesting`

## Advanced Usage

For detailed information about deployment and usage, see `docs/EC2_DEPLOYMENT_FROM_REPLIT.md`.
EOF

# Create the archive
print_step "Creating deployment archive..."
tar -czf aws-deploy-package.tar.gz "$DEPLOY_DIR"

# Cleanup
print_step "Cleaning up..."
rm -rf "$DEPLOY_DIR"

print_step "Deployment package created: aws-deploy-package.tar.gz"
echo "To deploy:"
echo "1. Download this file from Replit"
echo "2. Upload to your EC2 instance: scp aws-deploy-package.tar.gz ec2-user@YOUR_EC2_IP:~/"
echo "3. SSH into your instance: ssh ec2-user@YOUR_EC2_IP"
echo "4. Extract the package: tar -xzf aws-deploy-package.tar.gz"
echo "5. Run the setup script: cd aws-deploy-package && ./setup-ec2.sh"
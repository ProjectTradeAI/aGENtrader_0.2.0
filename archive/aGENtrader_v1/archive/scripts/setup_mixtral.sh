#!/bin/bash

# This script will set up the Mixtral 8x7B model on the EC2 instance

# Connect to EC2 and run the setup
echo "Connecting to EC2 and setting up Mixtral 8x7B..."

# Create a setup script to run on EC2
cat > ec2_setup_mixtral.sh << 'EOF'
#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print step header
print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Change to home directory
cd $HOME/aGENtrader

# Install Python packages
print_step "Installing required Python packages..."
pip install --user huggingface_hub
pip install --user llama-cpp-python --verbose

# Check installation status
if pip list --user | grep -q "llama-cpp-python"; then
    echo "llama-cpp-python installed successfully"
else
    print_warning "llama-cpp-python installation may have failed"
    
    # Try alternative installation with specific build options
    print_step "Trying alternative installation..."
    pip install --user llama-cpp-python --verbose
fi

# Run the model download script
print_step "Running model download script..."
python3 download_mixtral.py

# Verify installation
print_step "Verifying installation..."
if [ -f "$HOME/aGENtrader/models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf" ]; then
    echo "Mixtral model found at: $HOME/aGENtrader/models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"
    echo "Size: $(ls -lh $HOME/aGENtrader/models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf | awk '{print $5}')"
    echo "Setup completed successfully!"
else
    print_warning "Mixtral model not found. Download may have failed."
    echo "Please check the logs for errors."
fi
EOF

# Make the script executable
chmod +x ec2_setup_mixtral.sh

# Upload the script to EC2
./direct-ssh-command.sh "mkdir -p /home/ec2-user/aGENtrader/utils/llm_integration" || {
    echo "Failed to create directories on EC2"
    exit 1
}

cat ec2_setup_mixtral.sh | ./direct-ssh-command.sh "cat > /home/ec2-user/aGENtrader/setup_mixtral.sh && chmod +x /home/ec2-user/aGENtrader/setup_mixtral.sh" || {
    echo "Failed to upload setup script to EC2"
    exit 1
}

# Run the setup script
echo "Running setup script on EC2..."
./direct-ssh-command.sh "cd /home/ec2-user/aGENtrader && ./setup_mixtral.sh" || {
    echo "Failed to run setup script on EC2"
    exit 1
}

# Clean up
rm -f ec2_setup_mixtral.sh

echo "Setup process complete!"
echo "The EC2 instance should now be configured to use Mixtral 8x7B."
echo "You can run backtests with the new model using the ec2-multi-agent-backtest.sh script."
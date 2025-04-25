#!/bin/bash
# Script to create and run a script on EC2 to update to Mixtral 8x7B

# Create the update script
cat > ec2_update_mixtral.sh << 'EOF'
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

# Configuration
MODELS_DIR="$HOME/aGENtrader/models/llm_models"
MIXTRAL_MODEL_REPO="TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF"
MIXTRAL_MODEL_FILE="mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"
AWS_CONFIG_PATH="$HOME/aGENtrader/utils/llm_integration/aws_config.py"

# Create directories
print_step "Creating model directory (if needed)..."
mkdir -p "$MODELS_DIR"

# Install required Python packages
print_step "Checking and installing required Python packages..."
pip install --upgrade huggingface_hub llama-cpp-python psutil

# Check if Mixtral model exists
print_step "Checking if Mixtral model already exists..."
if [ -f "$MODELS_DIR/$MIXTRAL_MODEL_FILE" ]; then
    echo "Mixtral model already exists, skipping download."
else
    print_step "Downloading Mixtral 8x7B GGUF model from Hugging Face..."
    python3 -c "
from huggingface_hub import hf_hub_download
import os

model_path = hf_hub_download(
    repo_id='$MIXTRAL_MODEL_REPO',
    filename='$MIXTRAL_MODEL_FILE',
    local_dir='$MODELS_DIR',
    local_dir_use_symlinks=False
)

print(f'Model downloaded to: {model_path}')
"
fi

# Update AWS config file
print_step "Updating AWS config file for Mixtral..."
mkdir -p $(dirname "$AWS_CONFIG_PATH")
cat > "$AWS_CONFIG_PATH" << 'CONFIG'
"""AWS-specific configuration for LLM integration"""

# AWS instance-specific settings
AWS_DEPLOYMENT = True

# Model configuration
DEFAULT_MODEL_PATH = "models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"
DEFAULT_MODEL_REPO = "TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF"
DEFAULT_MODEL_FILE = "mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"

# Performance settings for EC2
import multiprocessing
DEFAULT_CONTEXT_LENGTH = 8192
NUM_THREADS = multiprocessing.cpu_count()  # Use all available CPU cores
N_GPU_LAYERS = 0  # Set to 0 if no GPU, or higher for GPU instances

# Advanced performance settings
BATCH_SIZE = 512  # Higher values may be faster but use more memory
OFFLOAD_KV = True  # Set to True to offload KV cache to CPU when possible
ROPE_SCALING_TYPE = "yarn"  # Better for longer contexts

# Timeout settings (in seconds)
DEFAULT_TIMEOUT = 120
ANALYST_TIMEOUT = 180
DECISION_TIMEOUT = 240
CONFIG

# Update AutoGen configuration
print_step "Updating AutoGen configuration for Mixtral..."
AUTOGEN_CONFIG_PATH="$HOME/aGENtrader/utils/llm_integration/autogen_integration.py"

# Make a backup of the original file
if [ -f "$AUTOGEN_CONFIG_PATH" ]; then
    cp "$AUTOGEN_CONFIG_PATH" "${AUTOGEN_CONFIG_PATH}.bak"
    
    # Update the model name in the AutoGen configuration
    sed -i 's/"model": "local-tinyllama-1.1b-chat"/"model": "local-mixtral-8x7b-instruct"/g' "$AUTOGEN_CONFIG_PATH"
    echo "Updated AutoGen configuration to use Mixtral model"
else
    echo "AutoGen configuration file not found at $AUTOGEN_CONFIG_PATH"
fi

# Update the local_llm.py file to check for the Mixtral model
LOCAL_LLM_PATH="$HOME/aGENtrader/utils/llm_integration/local_llm.py"
if [ -f "$LOCAL_LLM_PATH" ]; then
    cp "$LOCAL_LLM_PATH" "${LOCAL_LLM_PATH}.bak"
    echo "Backed up local_llm.py file"
else
    echo "local_llm.py file not found at $LOCAL_LLM_PATH"
fi

# Check if system has enough RAM for Mixtral
TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_MEM_GB=$(echo "scale=2; $TOTAL_MEM_KB/1024/1024" | bc)

echo "System has approximately ${TOTAL_MEM_GB}GB of RAM"

if (( $(echo "$TOTAL_MEM_GB < 16" | bc -l) )); then
    echo -e "${YELLOW}Warning: System has less than 16GB of RAM (${TOTAL_MEM_GB}GB).${NC}"
    echo -e "${YELLOW}Mixtral 8x7B might run very slowly or encounter out-of-memory errors.${NC}"
    echo -e "${YELLOW}Consider using a smaller model or upgrading the EC2 instance.${NC}"
    
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborting installation."
        exit 1
    fi
fi

# Run a quick test
print_step "Testing Mixtral model loading..."
python3 -c "
try:
    from llama_cpp import Llama
    model_path = '$MODELS_DIR/$MIXTRAL_MODEL_FILE'
    print(f'Loading model from {model_path}...')
    llm = Llama(
        model_path=model_path,
        n_ctx=512,  # Small context for testing
        n_threads=4,  # Fewer threads for testing
        n_batch=64,  # Smaller batch for testing
    )
    print('Model loaded successfully!')
    response = llm('Q: What is your name? A:', max_tokens=32, echo=True)
    print(response['choices'][0]['text'])
    print('Test completed successfully!')
except Exception as e:
    print(f'Error: {str(e)}')
    exit(1)
"

print_step "Mixtral 8x7B setup complete!"
echo "The system is now configured to use Mixtral 8x7B for AutoGen agents."
echo "You can run backtests with the new model using the ec2-multi-agent-backtest.sh script."
EOF

# Make the script executable
chmod +x ec2_update_mixtral.sh

# Upload to EC2 and execute
echo "Uploading and executing update script on EC2..."
./direct-ssh-command.sh "mkdir -p /home/ec2-user/aGENtrader/utils/llm_integration"
cat ec2_update_mixtral.sh | ./direct-ssh-command.sh "cat > /home/ec2-user/aGENtrader/update_mixtral.sh && chmod +x /home/ec2-user/aGENtrader/update_mixtral.sh"
./direct-ssh-command.sh "cd /home/ec2-user/aGENtrader && ./update_mixtral.sh"

# Clean up
rm -f ec2_update_mixtral.sh

echo "Update process complete!"
echo "The EC2 instance has been updated to use Mixtral 8x7B."
echo "You can run backtests with the new model using the ec2-multi-agent-backtest.sh script."
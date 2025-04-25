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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
MODELS_DIR="$HOME/aGENtrader/models/llm_models"
MIXTRAL_MODEL_REPO="TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF"
MIXTRAL_MODEL_FILE="mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"
DOWNLOAD_URL="https://huggingface.co/$MIXTRAL_MODEL_REPO/resolve/main/$MIXTRAL_MODEL_FILE"
OUTPUT_PATH="$MODELS_DIR/$MIXTRAL_MODEL_FILE"
MIN_REQUIRED_SPACE_GB=8

# Create directories
print_step "Creating model directory (if needed)..."
mkdir -p "$MODELS_DIR"

# Check for available disk space
print_step "Checking available disk space..."
AVAILABLE_SPACE_KB=$(df / | awk 'NR==2 {print $4}')
AVAILABLE_SPACE_GB=$(echo "scale=2; $AVAILABLE_SPACE_KB / 1024 / 1024" | bc)

print_step "Available space: ${AVAILABLE_SPACE_GB}GB"

if (( $(echo "$AVAILABLE_SPACE_GB < $MIN_REQUIRED_SPACE_GB" | bc -l) )); then
    print_error "Not enough disk space available. Need at least ${MIN_REQUIRED_SPACE_GB}GB, but only have ${AVAILABLE_SPACE_GB}GB."
    exit 1
fi

# Remove incomplete file if it exists
if [ -f "$OUTPUT_PATH" ]; then
    print_warning "Removing existing file..."
    rm -f "$OUTPUT_PATH"
fi

# Also cleanup any incomplete downloads in the huggingface cache
print_step "Cleaning up any incomplete downloads..."
find "$MODELS_DIR/.cache" -name "*.incomplete" -type f -delete 2>/dev/null

# Download the model with wget
print_step "Downloading Mixtral model from $DOWNLOAD_URL"
print_step "This may take some time (several GB download)..."
wget --progress=dot:giga -c "$DOWNLOAD_URL" -O "$OUTPUT_PATH"

# Check if download was successful
if [ $? -eq 0 ] && [ -f "$OUTPUT_PATH" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_PATH" | cut -f1)
    print_step "Download complete! File size: $FILE_SIZE"
    
    # Update the AutoGen configuration
    AUTOGEN_CONFIG_PATH="$HOME/aGENtrader/utils/llm_integration/autogen_integration.py"
    if [ -f "$AUTOGEN_CONFIG_PATH" ]; then
        cp "$AUTOGEN_CONFIG_PATH" "${AUTOGEN_CONFIG_PATH}.bak"
        
        # Create a more robust sed command to update the model configuration
        sed -i 's/"model": "local-tinyllama-1.1b-chat"/"model": "local-mixtral-8x7b-instruct"/g' "$AUTOGEN_CONFIG_PATH"
        
        # Also update the model path if needed
        sed -i "s|tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf|$MIXTRAL_MODEL_FILE|g" "$AUTOGEN_CONFIG_PATH"
        
        print_step "Updated AutoGen configuration to use Mixtral"
    else
        print_warning "AutoGen configuration file not found at $AUTOGEN_CONFIG_PATH"
    fi
else
    print_error "Download failed!"
    exit 1
fi

print_step "Mixtral model setup complete!"

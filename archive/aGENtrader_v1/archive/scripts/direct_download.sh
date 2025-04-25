#!/bin/bash

# Download URL and output path
DOWNLOAD_URL="https://huggingface.co/TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF/resolve/main/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"
OUTPUT_PATH="/home/ec2-user/aGENtrader/models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"

# Remove incomplete file if it exists
rm -f "$OUTPUT_PATH"

# Download the model
echo "Starting download of Mixtral model..."
wget --progress=dot:giga "$DOWNLOAD_URL" -O "$OUTPUT_PATH"

# Check if download was successful
if [ $? -eq 0 ] && [ -f "$OUTPUT_PATH" ]; then
    echo "Download complete! File size: $(du -h "$OUTPUT_PATH" | cut -f1)"
    
    # Update AutoGen configuration
    CONFIG_PATH="/home/ec2-user/aGENtrader/utils/llm_integration/autogen_integration.py"
    if [ -f "$CONFIG_PATH" ]; then
        sed -i 's/"model": "local-tinyllama-1.1b-chat"/"model": "local-mixtral-8x7b-instruct"/g' "$CONFIG_PATH"
        echo "Updated AutoGen configuration to use Mixtral"
    fi
else
    echo "Download failed!"
    exit 1
fi

echo "Mixtral model setup complete!"

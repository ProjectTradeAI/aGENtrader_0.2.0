#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Checking Mixtral model status...${NC}"

# Check if the Mixtral model file exists
FILE_DETAILS=$(ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "ls -lah /home/ec2-user/aGENtrader/models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf 2>/dev/null || echo 'File not found'")

if [[ "$FILE_DETAILS" == *"File not found"* ]]; then
    echo -e "${RED}Mixtral model file not found. The download may not be complete.${NC}"
    
    # Check if download is still in progress
    WGET_PROCESS=$(ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "ps aux | grep 'wget.*mixtral' | grep -v grep")
    
    if [ -z "$WGET_PROCESS" ]; then
        echo -e "${RED}Download process is not running. The download may have failed.${NC}"
    else
        echo -e "${YELLOW}Download is still in progress. Please wait for it to complete.${NC}"
        echo -e "${YELLOW}You can check progress with:${NC} ./check_mixtral_progress.sh"
    fi
    
    exit 1
fi

echo -e "${GREEN}Mixtral model found:${NC}"
echo "$FILE_DETAILS"

# Check if AutoGen config already mentions Mixtral
CONFIG_UPDATED=$(ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "grep -q 'mixtral-8x7b-instruct' /home/ec2-user/aGENtrader/utils/llm_integration/autogen_integration.py && echo 'Already updated' || echo 'Not updated'")

if [[ "$CONFIG_UPDATED" == *"Already updated"* ]]; then
    echo -e "${GREEN}AutoGen configuration is already updated to use Mixtral.${NC}"
    exit 0
fi

echo -e "${GREEN}Updating AutoGen configuration to use Mixtral...${NC}"

# Create a Python script to update the configuration
cat > update_autogen_config.py << 'PYTHONSCRIPT'
"""
Script to update AutoGen configuration to use Mixtral
"""

import os
import sys
import re

# Path to the autogen_integration.py file
autogen_file_path = '/home/ec2-user/aGENtrader/utils/llm_integration/autogen_integration.py'

# Make sure the file exists
if not os.path.isfile(autogen_file_path):
    print(f"Error: Could not find {autogen_file_path}")
    sys.exit(1)

# Backup the original file
backup_path = f"{autogen_file_path}.bak"
try:
    with open(autogen_file_path, 'r') as f:
        original_content = f.read()
    
    with open(backup_path, 'w') as f:
        f.write(original_content)
    print(f"Created backup at {backup_path}")
except Exception as e:
    print(f"Error creating backup: {str(e)}")
    sys.exit(1)

# Define the mixtral model path
mixtral_model_path = "/home/ec2-user/aGENtrader/models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"

# Update the content with Mixtral configuration
updated_content = original_content

# First, look for create_local_llm_config function
local_llm_config_pattern = r'def create_local_llm_config\([^)]*\):'
if re.search(local_llm_config_pattern, original_content):
    # Find the function body and replace the model path
    function_body_pattern = r'def create_local_llm_config\([^)]*\):.*?return config'
    
    def replace_function(match):
        function_text = match.group(0)
        
        # Replace TinyLlama with Mixtral
        function_text = re.sub(
            r'"model": "TinyLlama.*?"', 
            '"model": "local-mixtral-8x7b-instruct"', 
            function_text
        )
        
        # Replace the model path
        function_text = re.sub(
            r'"model_path": ".*?"', 
            f'"model_path": "{mixtral_model_path}"', 
            function_text
        )
        
        # Set higher temperature and higher max tokens for Mixtral
        function_text = re.sub(
            r'"temperature": \d+\.\d+', 
            '"temperature": 0.7', 
            function_text
        )
        
        function_text = re.sub(
            r'"max_tokens": \d+', 
            '"max_tokens": 4096', 
            function_text
        )
        
        return function_text
    
    updated_content = re.sub(function_body_pattern, replace_function, original_content, flags=re.DOTALL)

# Also update any direct references to TinyLlama in the file
updated_content = re.sub(
    r'TinyLlama-1\.1B-Chat-v1\.0', 
    'mixtral-8x7b-instruct-v0.1.Q4_K_M', 
    updated_content
)

# Write the updated content
try:
    with open(autogen_file_path, 'w') as f:
        f.write(updated_content)
    print(f"Successfully updated {autogen_file_path} to use Mixtral")
except Exception as e:
    print(f"Error updating config: {str(e)}")
    # Try to restore from backup
    try:
        with open(backup_path, 'r') as f:
            backup_content = f.read()
        with open(autogen_file_path, 'w') as f:
            f.write(backup_content)
        print("Restored from backup due to error")
    except:
        print("Failed to restore from backup")
    sys.exit(1)

print("AutoGen configuration updated successfully!")
PYTHONSCRIPT

# Upload and run the script
scp -i ec2_ssh_key.pem -o StrictHostKeyChecking=no update_autogen_config.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/update_autogen_config.py

echo -e "${GREEN}Running update script on EC2...${NC}"
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python update_autogen_config.py"

echo -e "\n${GREEN}Verifying update...${NC}"
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "grep -A 5 'model.*mixtral' /home/ec2-user/aGENtrader/utils/llm_integration/autogen_integration.py || echo 'Update not found in config'"

echo -e "\n${GREEN}AutoGen configuration update completed!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Run ./test_mixtral_integration.sh to test the Mixtral integration"
echo -e "2. Run backtests to compare performance with the new model"

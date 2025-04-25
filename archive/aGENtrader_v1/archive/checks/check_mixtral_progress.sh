#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Checking Mixtral download progress...${NC}"

# Check if the process is still running
WGET_PROCESS=$(ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "ps aux | grep 'wget.*mixtral' | grep -v grep")

if [ -z "$WGET_PROCESS" ]; then
    echo -e "${YELLOW}Download process is not running.${NC}"
    
    # Check if the file exists and was fully downloaded
    FILE_DETAILS=$(ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "ls -lah /home/ec2-user/aGENtrader/models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf 2>/dev/null || echo 'File not found'")
    
    if [[ "$FILE_DETAILS" == *"File not found"* ]]; then
        echo -e "${RED}Mixtral model file not found. Download may have failed.${NC}"
        echo -e "${YELLOW}Check the log file for more details:${NC}"
        ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "tail -20 /home/ec2-user/aGENtrader/mixtral_download.log"
    else
        echo -e "${GREEN}Mixtral model has been downloaded:${NC}"
        echo "$FILE_DETAILS"
        
        # Check if AutoGen config was updated
        CONFIG_UPDATED=$(ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "grep 'local-mixtral-8x7b-instruct' /home/ec2-user/aGENtrader/utils/llm_integration/autogen_integration.py || echo 'Not updated'")
        
        if [[ "$CONFIG_UPDATED" == *"Not updated"* ]]; then
            echo -e "${YELLOW}AutoGen configuration has not been updated to use Mixtral.${NC}"
        else
            echo -e "${GREEN}AutoGen configuration has been updated to use Mixtral.${NC}"
        fi
    fi
else
    echo -e "${GREEN}Download is in progress...${NC}"
    
    # Get the latest log entries
    echo -e "\n${GREEN}Recent download progress:${NC}"
    ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "tail -15 /home/ec2-user/aGENtrader/mixtral_download.log"
    
    # Get disk space
    echo -e "\n${GREEN}Disk space:${NC}"
    ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "df -h /"
fi

#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Checking disk space on EC2 instance...${NC}"

# Check current disk space
DISK_SPACE=$(ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "df -h /")
echo -e "Current disk space:"
echo "$DISK_SPACE"

echo -e "${YELLOW}Disk space is critically low. Attempting to free up space...${NC}"

# Find large files that may be safe to remove
echo -e "\n${GREEN}Finding large files that may be safe to remove...${NC}"
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "find /home/ec2-user/aGENtrader -type f -not -path '*/models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf' -size +100M -exec ls -lh {} \; | sort -k5hr | head -10"

# Clean Python bytecode files
echo -e "\n${GREEN}Removing Python bytecode files...${NC}"
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "find /home/ec2-user/aGENtrader -name '*.pyc' -o -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true"

# Find and remove log files
echo -e "\n${GREEN}Finding large log files to remove...${NC}"
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "find /home/ec2-user/aGENtrader -name '*.log' -size +50M -exec ls -lh {} \;"

echo -e "${YELLOW}Do you want to remove these log files? (type 'yes' to confirm)${NC}"
read -p "Confirm: " confirm

if [[ "$confirm" == "yes" ]]; then
    ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "find /home/ec2-user/aGENtrader -name '*.log' -size +50M -exec rm {} \; 2>/dev/null || true"
    echo -e "${GREEN}Log files removed.${NC}"
else
    echo -e "${YELLOW}Log files not removed.${NC}"
fi

# Check disk space again after cleanup
echo -e "\n${GREEN}Disk space after cleanup:${NC}"
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "df -h /"

echo -e "\n${GREEN}Done!${NC}"

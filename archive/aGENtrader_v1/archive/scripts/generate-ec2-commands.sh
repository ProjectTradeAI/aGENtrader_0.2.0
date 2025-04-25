#!/bin/bash
# Generate EC2 deployment commands using the stored secrets

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for secrets
if [ -z "$EC2_PUBLIC_IP" ]; then
    echo -e "${RED}Error: EC2_PUBLIC_IP secret is not set.${NC}"
    echo "Please add it to your Replit secrets or run this script with the environment variable set."
    exit 1
fi

echo -e "${GREEN}=== AWS EC2 Deployment Guide ===${NC}"
echo
echo -e "This guide gives you commands to deploy to your EC2 instance at ${BLUE}$EC2_PUBLIC_IP${NC}"
echo
echo -e "${GREEN}Step 1: Download the deployment package${NC}"
echo -e "Click the ${YELLOW}aws-deploy-package.tar.gz${NC} file in the file explorer and then click the download button"
echo
echo -e "${GREEN}Step 2: Upload the package to your EC2 instance${NC}"
echo -e "Run this command from your local terminal (where you downloaded the file):"
echo -e "${BLUE}scp -i /path/to/your/ec2-key.pem aws-deploy-package.tar.gz ec2-user@$EC2_PUBLIC_IP:~/${NC}"
echo -e "(Replace /path/to/your/ec2-key.pem with the path to your EC2 SSH key)"
echo
echo -e "${GREEN}Step 3: SSH into your EC2 instance${NC}"
echo -e "Run this command from your local terminal:"
echo -e "${BLUE}ssh -i /path/to/your/ec2-key.pem ec2-user@$EC2_PUBLIC_IP${NC}"
echo
echo -e "${GREEN}Step 4: Extract and set up the package${NC}"
echo -e "Run these commands on your EC2 instance:"
echo -e "${BLUE}tar -xzf aws-deploy-package.tar.gz${NC}"
echo -e "${BLUE}cd aws-deploy-package${NC}"
echo -e "${BLUE}./setup-ec2.sh${NC}"
echo
echo -e "${GREEN}Step 5: Run your first backtest${NC}"
echo -e "Run this command on your EC2 instance:"
echo -e "${BLUE}./run-backtest.sh -f 2025-03-01 -t 2025-03-10${NC}"
echo
echo -e "${YELLOW}Note: You'll need to provide your OpenAI API key during setup${NC}"
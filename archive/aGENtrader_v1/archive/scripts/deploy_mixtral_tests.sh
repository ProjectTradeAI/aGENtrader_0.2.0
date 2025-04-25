#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define files to transfer
FILES=(
  "improved_mixtral_test.py"
  "update_mixtral_config.py"
  "mixtral_db_integration_test.py"
)

echo -e "${GREEN}Deploying Mixtral integration test files to EC2...${NC}"

# Transfer files to EC2
for file in "${FILES[@]}"; do
  echo -e "${YELLOW}Transferring $file...${NC}"
  scp -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$file" ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully transferred $file${NC}"
  else
    echo -e "${RED}Failed to transfer $file${NC}"
    exit 1
  fi
done

echo -e "\n${GREEN}All files transferred. Running update script...${NC}"

# Run the update script to ensure config is set for Mixtral
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=60 ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 update_mixtral_config.py"

echo -e "\n${GREEN}Config updated. Installing llama-cpp-python package...${NC}"

# Install llama-cpp-python package
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=60 ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && pip install llama-cpp-python"

echo -e "\n${GREEN}Running basic Mixtral test...${NC}"

# Run the improved Mixtral test
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=120 ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 improved_mixtral_test.py | tee mixtral_test_output.log"

echo -e "\n${GREEN}Running database integration test...${NC}"

# Run the database integration test
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=120 ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 mixtral_db_integration_test.py | tee mixtral_db_test_output.log"

echo -e "\n${GREEN}Tests completed. Getting results...${NC}"

# Get the results
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && tail -50 mixtral_test_output.log"
echo -e "\n${YELLOW}--------- Database Integration Test Results ---------${NC}"
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && tail -50 mixtral_db_test_output.log"

echo -e "\n${GREEN}Deployment and testing completed!${NC}"
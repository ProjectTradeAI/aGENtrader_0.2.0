#!/bin/bash

# Deploy files to EC2 and run tests without installing packages
echo "Deploying Mixtral integration test files to EC2..."

# Transfer files to EC2
scp -i ec2_ssh_key.pem -o StrictHostKeyChecking=no improved_mixtral_test.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/
scp -i ec2_ssh_key.pem -o StrictHostKeyChecking=no update_mixtral_config.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/
scp -i ec2_ssh_key.pem -o StrictHostKeyChecking=no mixtral_db_integration_test.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/

echo "All files transferred. Running update script..."

# Run the update script to ensure config is set for Mixtral
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 update_mixtral_config.py"

echo "Running basic Mixtral test..."

# Run the improved Mixtral test
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 improved_mixtral_test.py"

echo "Tests completed."

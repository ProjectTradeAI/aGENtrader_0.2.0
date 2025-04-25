#!/bin/bash
# Script to update the aGENtrader v2 deployment with the fixed technical_analyst_agent.py

# Check if EC2_PUBLIC_IP environment variable is set
if [ -z "$EC2_PUBLIC_IP" ]; then
    echo "Error: EC2_PUBLIC_IP environment variable is not set."
    exit 1
fi

echo "Updating aGENtrader v2 technical_analyst_agent.py..."

# Copy the fixed file directly to EC2
echo "Copying fixed technical_analyst_agent.py to EC2..."
scp -i aGENtrader.pem technical_analyst_agent.py ec2-user@$EC2_PUBLIC_IP:~/aGENtrader-test/aGENtrader_v2/agents/

# SSH into EC2 and restart the Docker container
echo "Restarting the Docker container..."
ssh -i aGENtrader.pem ec2-user@$EC2_PUBLIC_IP << 'EOF'
    cd ~/aGENtrader-test
    
    # Stop the current container
    sudo docker-compose down
    
    # Restart the container
    sudo docker-compose up -d
    
    # Update the log file
    echo "Container restarted with fixed technical_analyst_agent.py at $(date)" >> logs/test_updates.log
    
    # Show running containers
    sudo docker ps
EOF

echo "Update completed and test restarted."
echo "Use ./check_24hr_test_status.sh to check the status."
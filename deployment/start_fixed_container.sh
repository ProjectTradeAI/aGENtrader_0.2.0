#!/bin/bash
# Script to manually start the container for aGENtrader v2 24-hour testing

# Check if EC2_PUBLIC_IP environment variable is set
if [ -z "$EC2_PUBLIC_IP" ]; then
    echo "Error: EC2_PUBLIC_IP environment variable is not set."
    exit 1
fi

# Check if COINAPI_KEY environment variable is set
if [ -z "$COINAPI_KEY" ]; then
    echo "Error: COINAPI_KEY environment variable is not set."
    exit 1
fi

echo "Starting aGENtrader v2 container on EC2..."
echo "==========================================="

# SSH into EC2 and start the container
ssh -i aGENtrader.pem ec2-user@$EC2_PUBLIC_IP << EOF
    echo "Checking Docker image status..."
    sudo docker images | grep agentrader
    
    # Make sure logs directory exists
    mkdir -p ~/aGENtrader-test-fixed/logs
    chmod -R 777 ~/aGENtrader-test-fixed/logs
    
    # Update the .env file with the latest API key
    echo "COINAPI_KEY=$COINAPI_KEY" > ~/aGENtrader-test-fixed/.env
    
    echo "Starting the container directly using Docker command..."
    cd ~/aGENtrader-test-fixed
    
    # Stop any existing containers with the same name
    sudo docker rm -f agentrader_v2 || true
    
    # Run the container directly from the image
    sudo docker run -d \
        --name agentrader_v2 \
        -v $(pwd)/logs:/app/logs \
        -e COINAPI_KEY=$COINAPI_KEY \
        agentrader-test-agentrader_v2:latest
    
    echo "Checking container status..."
    sudo docker ps
    
    echo "Initial container logs:"
    sleep 3
    sudo docker logs agentrader_v2
EOF

echo ""
echo "Container start attempted. Checking status..."
sleep 5
./check_fixed_test_status.sh
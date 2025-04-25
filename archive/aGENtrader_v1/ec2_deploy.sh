#!/bin/bash
# EC2 Deployment Script
# This script deploys the trading system API solution to the EC2 instance

set -e  # Exit on any error
echo "Preparing to deploy trading system API to EC2 instance..."

# Check if EC2 public IP is available
if [ -z "$EC2_PUBLIC_IP" ]; then
    if [ -f ".env" ]; then
        source .env
    fi
    
    if [ -z "$EC2_PUBLIC_IP" ]; then
        echo "Error: EC2_PUBLIC_IP environment variable not set. Please provide the EC2 public IP."
        exit 1
    fi
fi

# Check if EC2 private key is available
if [ -z "$EC2_PRIVATE_KEY" ] && [ ! -f "./ec2_key.pem" ]; then
    if [ -f ".env" ]; then
        source .env
    fi
    
    if [ -z "$EC2_PRIVATE_KEY" ]; then
        echo "Error: EC2_PRIVATE_KEY environment variable not set and no ec2_key.pem file found."
        exit 1
    else
        # Extract the key to a file
        echo "$EC2_PRIVATE_KEY" > ./ec2_key.pem
        chmod 600 ./ec2_key.pem
    fi
fi

# Try trading-bot-deployer.pem first, then fall back to other options
if [ -f "./trading-bot-deployer.pem" ]; then
    KEY_FILE="./trading-bot-deployer.pem"
elif [ -f "./ec2_key.pem" ]; then
    KEY_FILE="./ec2_key.pem"
elif [ ! -z "$EC2_SSH_KEY" ]; then
    KEY_FILE="$EC2_SSH_KEY"
else
    echo "Error: No SSH key file found. Please provide trading-bot-deployer.pem or ec2_key.pem."
    exit 1
fi

# Confirm details
echo "Deploying to EC2 instance at: $EC2_PUBLIC_IP"
echo "Using SSH key: $KEY_FILE"

# Function to copy files to EC2
deploy_to_ec2() {
    echo "Creating deployment package..."
    
    # Create a deployment directory
    mkdir -p deploy_package
    
    # Copy essential files
    cp test_simple_api.js deploy_package/
    cp start_test_server.sh deploy_package/
    cp stop_test_server.sh deploy_package/
    cp API_DOCUMENTATION.md deploy_package/
    cp -r api deploy_package/ 2>/dev/null || echo "No api directory found"
    cp -r orchestration deploy_package/ 2>/dev/null || echo "No orchestration directory found"
    cp -r agents deploy_package/ 2>/dev/null || echo "No agents directory found"
    cp -r utils deploy_package/ 2>/dev/null || echo "No utils directory found"
    cp -r scripts deploy_package/ 2>/dev/null || echo "No scripts directory found"
    cp run_python_sync.js deploy_package/ 2>/dev/null || echo "No run_python_sync.js found"
    
    # Copy EC2 cleanup script
    cp ec2_cleanup.sh deploy_package/
    
    # Create a README for EC2
    cat > deploy_package/README.md << 'EOF'
# Trading System API for EC2

This package contains the Trading System API for deployment on EC2.

## Getting Started

1. Run the cleanup script to organize the environment (if needed):
   ```
   ./ec2_cleanup.sh
   ```

2. Install dependencies:
   ```
   npm install express cors
   ```

3. Start the API server:
   ```
   ./start_test_server.sh
   ```

4. Access the API at:
   http://localhost:5050/

5. Stop the server when done:
   ```
   ./stop_test_server.sh
   ```

See API_DOCUMENTATION.md for API details.
EOF
    
    echo "Deployment package created."
    
    # Copy files to EC2
    echo "Copying files to EC2..."
    scp -i "$KEY_FILE" -r deploy_package/* ec2-user@$EC2_PUBLIC_IP:~/aGENtrader/
    
    # Cleanup
    rm -rf deploy_package
    
    echo "Deployment completed successfully!"
    echo "Connect to your EC2 instance and run the following commands:"
    echo "  cd ~/aGENtrader"
    echo "  npm install express cors"
    echo "  ./start_test_server.sh"
}

# Execute the deployment
deploy_to_ec2
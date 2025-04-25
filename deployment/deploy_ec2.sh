#!/bin/bash
# aGENtrader v2.2 - EC2 Deployment Script
# This script deploys aGENtrader v2.2 to an EC2 instance

set -e

# Configuration
EC2_USER="ec2-user"
EC2_HOST=""
PEM_FILE="aGENtrader.pem"
DEPLOY_DIR="/home/ec2-user/aGENtrader"
GITHUB_REPO="https://github.com/yourusername/aGENtrader.git"
BRANCH="v2.2-main"

# Display header
echo "======================================================================"
echo "              aGENtrader v2.2 - EC2 Deployment Script"
echo "======================================================================"
echo

# Check for EC2 host parameter
if [ "$1" != "" ]; then
    EC2_HOST="$1"
fi

# If EC2_HOST is still empty, prompt for it
if [ "$EC2_HOST" == "" ]; then
    read -p "Enter EC2 hostname or IP address: " EC2_HOST
    
    if [ "$EC2_HOST" == "" ]; then
        echo "Error: EC2 hostname or IP address is required"
        exit 1
    fi
fi

# Check if PEM file exists
if [ ! -f "$PEM_FILE" ]; then
    echo "Error: PEM file not found at $PEM_FILE"
    exit 1
fi

# Ensure PEM file has correct permissions
chmod 400 "$PEM_FILE"

echo "Deploying to EC2 instance: $EC2_USER@$EC2_HOST"
echo "Using PEM file: $PEM_FILE"
echo

# SSH into the instance and execute deployment
echo "Connecting to EC2 instance..."
ssh -i "$PEM_FILE" "$EC2_USER@$EC2_HOST" << EOF
    echo "Connected to EC2 instance"
    
    # Ensure deployment directory exists
    echo "Creating deployment directory: $DEPLOY_DIR"
    mkdir -p "$DEPLOY_DIR"
    
    # Check if Git is installed
    if ! command -v git &> /dev/null; then
        echo "Installing Git..."
        sudo yum install -y git
    fi
    
    # Clone or update the repository
    if [ -d "$DEPLOY_DIR/.git" ]; then
        echo "Updating existing repository..."
        cd "$DEPLOY_DIR"
        git fetch
        git checkout "$BRANCH"
        git pull
    else
        echo "Cloning repository..."
        git clone -b "$BRANCH" "$GITHUB_REPO" "$DEPLOY_DIR"
        cd "$DEPLOY_DIR"
    fi
    
    # Install dependencies
    echo "Installing dependencies..."
    if [ -f "$DEPLOY_DIR/deployment/install_prerequisites.sh" ]; then
        cd "$DEPLOY_DIR"
        bash deployment/install_prerequisites.sh
    else
        echo "Warning: prerequisites installation script not found"
    fi
    
    # Build Docker image
    echo "Building Docker image..."
    if [ -f "$DEPLOY_DIR/deployment/build_image.sh" ]; then
        cd "$DEPLOY_DIR"
        bash deployment/build_image.sh
    else
        echo "Warning: Docker build script not found"
    fi
    
    # Start the application
    echo "Starting aGENtrader..."
    if [ -f "$DEPLOY_DIR/deployment/start.sh" ]; then
        cd "$DEPLOY_DIR"
        bash deployment/start.sh
    else
        echo "Warning: start script not found"
    fi
    
    echo "Deployment completed"
EOF

# Check if SSH command was successful
if [ $? -eq 0 ]; then
    echo
    echo "Deployment successful!"
    echo "aGENtrader v2.2 has been deployed to $EC2_USER@$EC2_HOST"
    echo
    echo "To monitor the application:"
    echo "  ssh -i $PEM_FILE $EC2_USER@$EC2_HOST"
    echo "  cd $DEPLOY_DIR && bash deployment/monitor_agentrader.sh"
    echo
else
    echo
    echo "Deployment failed."
    exit 1
fi

exit 0
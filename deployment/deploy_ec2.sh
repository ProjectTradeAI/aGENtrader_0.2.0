#!/bin/bash
# aGENtrader v2.2 - EC2 Deployment Script
# This script deploys aGENtrader v2.2 to an EC2 instance

set -e

# Configuration
EC2_USER="ubuntu"  # Changed to ubuntu as common EC2 default
EC2_HOST=""
PEM_FILE="aGENtrader.pem"
DEPLOY_DIR="/home/ubuntu/aGENtrader" # Adjusted for ubuntu user
GITHUB_REPO="git@github.com:ProjectTradeAI/aGENtrader_0.2.0.git"
BRANCH="main"
VERSION=$(git describe --tags --always || echo "v0.2.0")

# Display header
echo "======================================================================"
echo "              aGENtrader v2.2 - EC2 Deployment Script"
echo "======================================================================"
echo "Deployment version: $VERSION"
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
echo "Repository: $GITHUB_REPO"
echo "Branch: $BRANCH"
echo "Version: $VERSION"
echo

# Make sure known_hosts has GitHub entry first
ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts 2>/dev/null

# SSH into the instance and execute deployment
echo "Connecting to EC2 instance..."
ssh -i "$PEM_FILE" -o StrictHostKeyChecking=accept-new "$EC2_USER@$EC2_HOST" << EOF
    echo "Connected to EC2 instance"
    
    # Ensure deployment directory exists
    echo "Creating deployment directory: $DEPLOY_DIR"
    mkdir -p "$DEPLOY_DIR"
    
    # Check if Git is installed
    if ! command -v git &> /dev/null; then
        echo "Installing Git..."
        sudo apt-get update && sudo apt-get install -y git
    fi
    
    # Make sure GitHub is in known_hosts
    ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts 2>/dev/null
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        sudo apt-get update
        sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable"
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io
        sudo usermod -aG docker \$USER
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        echo "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    # Clone or update the repository
    if [ -d "$DEPLOY_DIR/.git" ]; then
        echo "Updating existing repository..."
        cd "$DEPLOY_DIR"
        git fetch --all
        git checkout "$BRANCH"
        git reset --hard origin/"$BRANCH"
        git pull
    else
        echo "Cloning repository..."
        git clone -b "$BRANCH" "$GITHUB_REPO" "$DEPLOY_DIR"
        cd "$DEPLOY_DIR"
    fi
    
    # Copy environment variables if needed
    if [ -f ".env.example" ] && [ ! -f ".env" ]; then
        echo "Creating .env file from example..."
        cp .env.example .env
        # Note: You'll need to manually edit the .env file with appropriate values
        echo "Please edit $DEPLOY_DIR/.env with appropriate values"
    fi
    
    # Build and deploy using Docker Compose
    echo "Building and deploying with Docker Compose..."
    cd "$DEPLOY_DIR"
    
    # Stop existing containers if running
    if [ -f "docker/docker-compose.yml" ]; then
        echo "Stopping existing containers..."
        cd docker
        docker-compose down
        
        # Build with version tag
        echo "Building new Docker image with version $VERSION..."
        VERSION=$VERSION docker-compose build --no-cache
        
        # Start services
        echo "Starting services..."
        VERSION=$VERSION docker-compose up -d
        
        # Show running containers
        echo "Running containers:"
        docker-compose ps
        cd ..
    else
        echo "Error: docker-compose.yml not found in docker directory"
        exit 1
    fi
    
    # Execute validation if available
    if [ -f "deployment/validate_deployment.py" ]; then
        echo "Validating deployment..."
        python deployment/validate_deployment.py
    else
        echo "Warning: deployment validation script not found"
        echo "Checking logs for basic validation..."
        sleep 5
        docker logs \$(docker ps -q -f "name=aGENtrader") --tail 20
    fi
    
    echo "Deployment completed"
EOF

# Check if SSH command was successful
if [ $? -eq 0 ]; then
    echo
    echo "Deployment successful!"
    echo "aGENtrader v2.2 has been deployed to $EC2_USER@$EC2_HOST"
    echo "Version: $VERSION"
    echo
    echo "To monitor the application:"
    echo "  ssh -i $PEM_FILE $EC2_USER@$EC2_HOST"
    echo "  cd $DEPLOY_DIR/docker && docker-compose logs -f"
    echo
else
    echo
    echo "Deployment failed."
    exit 1
fi

exit 0
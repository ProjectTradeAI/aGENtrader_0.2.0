#!/bin/bash
# aGENtrader v2.2 - EC2 Rollback Script
# This script rolls back the aGENtrader deployment to a previous version

set -e

# Configuration
EC2_USER="ubuntu"
EC2_HOST=""
PEM_FILE="aGENtrader.pem"
DEPLOY_DIR="/home/ubuntu/aGENtrader"

# Display header
echo "======================================================================"
echo "              aGENtrader v2.2 - Deployment Rollback Script"
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

# Get available versions (Git tags)
echo "Fetching available versions..."
git fetch --tags

# List available tags and recent commits
echo
echo "Available versions (Git tags):"
git tag -l --sort=-v:refname | head -10 | nl

echo
echo "Recent commits:"
git log --oneline -n 5

# Ask for version to rollback to
echo
read -p "Enter version to rollback to (Git tag, branch, or commit hash): " ROLLBACK_VERSION

if [ -z "$ROLLBACK_VERSION" ]; then
    echo "Error: No rollback version specified"
    exit 1
fi

# Confirm rollback
echo
echo "You are about to roll back to: $ROLLBACK_VERSION"
read -p "Are you sure you want to proceed? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Rollback canceled."
    exit 0
fi

echo
echo "Rolling back to $ROLLBACK_VERSION on $EC2_USER@$EC2_HOST..."
echo

# SSH into the instance and execute rollback
echo "Connecting to EC2 instance..."
ssh -i "$PEM_FILE" -o StrictHostKeyChecking=accept-new "$EC2_USER@$EC2_HOST" << EOF
    echo "Connected to EC2 instance"
    
    # Change to deployment directory
    cd "$DEPLOY_DIR"
    
    # Stash any local changes
    echo "Saving any local changes..."
    git stash
    
    # Fetch all tags and branches
    echo "Updating repository..."
    git fetch --all --tags
    
    # Checkout the specified version
    echo "Rolling back to $ROLLBACK_VERSION..."
    git checkout $ROLLBACK_VERSION
    
    # Get actual version for Docker tagging
    VERSION=\$(git describe --tags --always)
    echo "Resolved version: \$VERSION"
    
    # Stop existing containers
    echo "Stopping current containers..."
    cd docker
    docker-compose down
    
    # Check if there are any dangling volumes to clean up
    DANGLING_VOLUMES=\$(docker volume ls -qf dangling=true)
    if [ ! -z "\$DANGLING_VOLUMES" ]; then
        echo "Cleaning up dangling volumes..."
        docker volume rm \$DANGLING_VOLUMES
    fi
    
    # Build and start with the rollback version
    echo "Building Docker image for version \$VERSION..."
    VERSION=\$VERSION docker-compose build --no-cache
    
    echo "Starting rolled-back version..."
    VERSION=\$VERSION docker-compose up -d
    
    # Show running containers
    echo "Running containers:"
    docker-compose ps
    
    # Wait for system to start up
    echo "Waiting for system to initialize (30 seconds)..."
    sleep 30
    
    # Validate deployment
    if [ -f "../deployment/validate_deployment.py" ]; then
        echo "Validating rollback deployment..."
        cd ..
        python deployment/validate_deployment.py
    else
        echo "Warning: validation script not found, checking logs manually"
        docker logs \$(docker ps -q -f "name=aGENtrader") --tail 20
    fi
    
    echo "Rollback completed to version: \$VERSION"
EOF

# Check if SSH command was successful
if [ $? -eq 0 ]; then
    echo
    echo "Rollback successful!"
    echo "aGENtrader has been rolled back to $ROLLBACK_VERSION on $EC2_USER@$EC2_HOST"
    echo
    echo "To monitor the application:"
    echo "  ssh -i $PEM_FILE $EC2_USER@$EC2_HOST"
    echo "  cd $DEPLOY_DIR/docker && docker-compose logs -f"
    echo
    
    # Create a local tag for this rollback if it doesn't exist already
    if ! git show-ref --quiet --tags "rollback-$(date +%Y%m%d-%H%M%S)"; then
        ROLLBACK_TAG="rollback-$(date +%Y%m%d-%H%M%S)"
        git tag -a "$ROLLBACK_TAG" -m "Rollback to $ROLLBACK_VERSION on $(date)"
        echo "Created local rollback tag: $ROLLBACK_TAG"
        echo "Push this tag to remote with: git push origin $ROLLBACK_TAG"
    fi
else
    echo
    echo "Rollback failed."
    exit 1
fi

exit 0
#!/bin/bash
# aGENtrader v2.2 - Clean EC2 Deployment Script
# This script performs a full cleanup and fresh deployment of aGENtrader v2.2 to an EC2 instance

set -e

# Configuration
EC2_USER="ubuntu"
EC2_HOST=""
PEM_FILE="aGENtrader.pem"
DEPLOY_DIR="/home/ubuntu/aGENtrader"
GITHUB_REPO="git@github.com:ProjectTradeAI/aGENtrader_0.2.0.git"
BRANCH="main"
VERSION=$(git describe --tags --always || echo "v0.2.0")
FORCE_CONFIRM=false
ENV_FILE=""  # Path to .env file to upload (optional)

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Display header
echo -e "${BLUE}======================================================================"
echo -e "          aGENtrader v2.2 - Clean EC2 Deployment Script"
echo -e "======================================================================${NC}"
echo -e "Deployment version: ${GREEN}$VERSION${NC}"
echo

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage:${NC} $0 [options]"
    echo ""
    echo -e "Options:"
    echo -e "  -h, --host HOST     EC2 hostname or IP address"
    echo -e "  -k, --key FILE      Path to PEM key file (default: aGENtrader.pem)"
    echo -e "  -e, --env FILE      Path to .env file to upload to EC2 (optional)"
    echo -e "  -y, --yes           Skip confirmation prompt"
    echo -e "  --help              Show this help message"
    echo ""
    echo -e "Examples:"
    echo -e "  Basic deployment:"
    echo -e "    $0 --host ec2-12-34-56-78.compute-1.amazonaws.com --key ~/.ssh/my-key.pem"
    echo ""
    echo -e "  Deployment with .env file (recommended):"
    echo -e "    $0 --host ec2-12-34-56-78.compute-1.amazonaws.com --key ~/.ssh/my-key.pem --env ./.env.production"
    echo ""
    echo -e "  Non-interactive deployment (for automation):"
    echo -e "    $0 --host ec2-12-34-56-78.compute-1.amazonaws.com --key ~/.ssh/my-key.pem --env ./.env.production --yes"
    echo ""
}

# Parse command line options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -h|--host) EC2_HOST="$2"; shift ;;
        -k|--key) PEM_FILE="$2"; shift ;;
        -e|--env) ENV_FILE="$2"; shift ;;
        -y|--yes) FORCE_CONFIRM=true ;;
        --help) show_usage; exit 0 ;;
        *) echo -e "${RED}Unknown parameter: $1${NC}"; show_usage; exit 1 ;;
    esac
    shift
done

# Check for EC2 host parameter
if [ "$EC2_HOST" == "" ]; then
    read -p "Enter EC2 hostname or IP address: " EC2_HOST
    
    if [ "$EC2_HOST" == "" ]; then
        echo -e "${RED}Error: EC2 hostname or IP address is required${NC}"
        exit 1
    fi
fi

# Check if PEM file exists
if [ ! -f "$PEM_FILE" ]; then
    echo -e "${RED}Error: PEM file not found at $PEM_FILE${NC}"
    exit 1
fi

# Ensure PEM file has correct permissions
chmod 400 "$PEM_FILE"

# Check if ENV_FILE exists when provided
if [ ! -z "$ENV_FILE" ] && [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: ENV file not found at $ENV_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}Deployment Target:${NC}"
echo -e "  EC2 Instance: ${GREEN}$EC2_USER@$EC2_HOST${NC}"
echo -e "  PEM File: ${GREEN}$PEM_FILE${NC}"
echo -e "  Repository: ${GREEN}$GITHUB_REPO${NC}"
echo -e "  Branch: ${GREEN}$BRANCH${NC}"
echo -e "  Version: ${GREEN}$VERSION${NC}"
if [ ! -z "$ENV_FILE" ]; then
    echo -e "  ENV File: ${GREEN}$ENV_FILE${NC} (will be uploaded)"
fi
echo

# Check environment before proceeding
echo -e "${BLUE}Checking environment configuration...${NC}"
if [ -f "deployment/check_env.py" ]; then
    python deployment/check_env.py
    CHECK_ENV_EXIT=$?
    
    if [ $CHECK_ENV_EXIT -ne 0 ]; then
        echo -e "${YELLOW}Environment check failed. You can continue but the deployment may not work correctly.${NC}"
        if [ "$FORCE_CONFIRM" != "true" ]; then
            read -p "Continue anyway? (y/N): " CONTINUE_ANYWAY
            if [[ ! "$CONTINUE_ANYWAY" =~ ^[Yy]$ ]]; then
                echo -e "${RED}Operation canceled.${NC}"
                exit 1
            fi
        fi
    else
        echo -e "${GREEN}Environment check passed.${NC}"
    fi
else
    echo -e "${YELLOW}Environment check script not found. Continuing without verification.${NC}"
fi

# Confirmation prompt
if [ "$FORCE_CONFIRM" != "true" ]; then
    echo -e "${YELLOW}WARNING: This script will perform a complete cleanup of the EC2 instance:${NC}"
    echo -e "  1. Remove all Docker containers, images, volumes, and networks"
    echo -e "  2. Delete the existing aGENtrader repository folder"
    echo -e "  3. Clone a fresh copy of the repository"
    echo -e "  4. Build new Docker images and start containers"
    echo
    read -p "Do you want to continue? (y/N): " CONFIRM
    
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Operation canceled.${NC}"
        exit 0
    fi
fi

# Make sure known_hosts has GitHub entry first
ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts 2>/dev/null || true

# Upload env file if provided
if [ ! -z "$ENV_FILE" ]; then
    echo -e "${BLUE}Uploading .env file to EC2 instance...${NC}"
    # Get current timestamp for unique directory name
    TIMESTAMP=$(date +%s)
    TEMP_ENV_DIR="/tmp/agentrader_env_${TIMESTAMP}"
    
    # First create a temporary directory on the remote server
    ssh -i "$PEM_FILE" -o StrictHostKeyChecking=accept-new "$EC2_USER@$EC2_HOST" "mkdir -p $TEMP_ENV_DIR"
    
    # Upload the .env file
    scp -i "$PEM_FILE" "$ENV_FILE" "$EC2_USER@$EC2_HOST:$TEMP_ENV_DIR/.env"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to upload .env file. Continuing without it.${NC}"
    else
        echo -e "${GREEN}Successfully uploaded .env file to temporary location.${NC}"
        # Pass the timestamp to the SSH session via environment variable
        export TIMESTAMP
    fi
fi

# SSH into the instance and execute cleanup and deployment
echo -e "${BLUE}Connecting to EC2 instance...${NC}"
ssh -i "$PEM_FILE" -o StrictHostKeyChecking=accept-new "$EC2_USER@$EC2_HOST" << EOF
    # Get TIMESTAMP environment variable from parent if set
    TIMESTAMP="${TIMESTAMP:-""}"
    echo -e "${GREEN}Connected to EC2 instance${NC}"
    
    # 1. Full Docker Cleanup
    echo -e "\n${BLUE}STEP 1: Full Docker System Cleanup${NC}"
    
    # Stop all running containers first
    echo "Stopping all running containers..."
    docker stop \$(docker ps -q) 2>/dev/null || echo "No running containers to stop."
    
    # Perform complete system cleanup
    echo "Removing all Docker containers, images, volumes, and networks..."
    docker system prune -a --volumes -f
    
    # 2. Remove Old Repository Folder
    echo -e "\n${BLUE}STEP 2: Removing Old Repository Folder${NC}"
    if [ -d "$DEPLOY_DIR" ]; then
        echo "Deleting $DEPLOY_DIR..."
        rm -rf "$DEPLOY_DIR"
    else
        echo "No existing repository folder found."
    fi
    
    # 3. Ensure prerequisites are installed
    echo -e "\n${BLUE}STEP 3: Checking Prerequisites${NC}"
    
    # Check if Git is installed
    if ! command -v git &> /dev/null; then
        echo "Installing Git..."
        sudo apt-get update && sudo apt-get install -y git
    else
        echo "Git is already installed."
    fi
    
    # Make sure GitHub is in known_hosts
    ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts 2>/dev/null || true
    
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
        echo "You may need to reconnect to the SSH session for Docker permissions to take effect."
    else
        echo "Docker is already installed."
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        echo "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    else
        echo "Docker Compose is already installed."
    fi
    
    # 4. Fresh Repository Clone
    echo -e "\n${BLUE}STEP 4: Fresh Repository Clone${NC}"
    echo "Creating deployment directory: $DEPLOY_DIR"
    mkdir -p "$DEPLOY_DIR"
    
    echo "Cloning repository from $GITHUB_REPO..."
    git clone -b "$BRANCH" "$GITHUB_REPO" "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
    
    # 5. Setup Environment Variables
    echo -e "\n${BLUE}STEP 5: Setting Up Environment Variables${NC}"
    
    # Check if we have an uploaded .env file
    if [ ! -z "$TIMESTAMP" ]; then
        TEMP_ENV_DIR="/tmp/agentrader_env_${TIMESTAMP}"
        if [ -f "$TEMP_ENV_DIR/.env" ]; then
            echo "Using uploaded .env file..."
            cp "$TEMP_ENV_DIR/.env" .env
            echo "Removing temporary env directory..."
            rm -rf "$TEMP_ENV_DIR"
        fi
    elif [ -f ".env.example" ] && [ ! -f ".env" ]; then
        echo "Creating .env file from example..."
        cp .env.example .env
        echo "Note: You'll need to manually edit the .env file with appropriate API keys."
    elif [ -f ".env" ]; then
        echo ".env file already exists, keeping it."
    else
        echo "Creating empty .env file (you'll need to configure it)..."
        touch .env
    fi
    
    # 6. Build and Deploy
    echo -e "\n${BLUE}STEP 6: Building and Deploying${NC}"
    cd "$DEPLOY_DIR"
    
    if [ -f "build_image.sh" ]; then
        echo "Building Docker image using build_image.sh..."
        bash build_image.sh
    else
        echo "Warning: build_image.sh not found. Using docker-compose instead."
    fi
    
    if [ -f "docker/docker-compose.yml" ]; then
        echo "Deploying with Docker Compose..."
        cd docker
        
        # Build with version tag
        echo "Building Docker image with version $VERSION..."
        VERSION=$VERSION docker-compose build
        
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
    
    # 7. Validate Deployment
    echo -e "\n${BLUE}STEP 7: Validating Deployment${NC}"
    if [ -f "deployment/validate_deployment.py" ]; then
        echo "Running deployment validation..."
        python3 deployment/validate_deployment.py
        VALIDATION_EXIT=\$?
        
        if [ \$VALIDATION_EXIT -eq 0 ]; then
            echo -e "${GREEN}Validation PASSED: Deployment is working correctly.${NC}"
        else
            echo -e "${RED}Validation FAILED: Deployment may have issues.${NC}"
        fi
    else
        echo "Warning: Validation script not found. Checking logs instead..."
        echo "Container logs:"
        docker logs \$(docker ps -q -f "name=agentrader" -f "name=aGENtrader") --tail 20
    fi
    
    # 8. Final System Check
    echo -e "\n${BLUE}STEP 8: Final System Check${NC}"
    echo "Disk space usage:"
    df -h | grep -E 'Filesystem|/$'
    
    echo "Docker container status:"
    docker ps -a
    
    echo "Docker image list:"
    docker images
    
    echo -e "\n${GREEN}Deployment completed!${NC}"
    echo "aGENtrader v2.2 has been freshly deployed with version: $VERSION"
EOF

# Check if SSH command was successful
if [ $? -eq 0 ]; then
    echo
    echo -e "${GREEN}Clean deployment successful!${NC}"
    echo -e "aGENtrader v2.2 has been freshly deployed to ${BLUE}$EC2_USER@$EC2_HOST${NC}"
    echo -e "Version: ${BLUE}$VERSION${NC}"
    echo
    echo -e "${YELLOW}Important Next Steps:${NC}"
    
    if [ ! -z "$ENV_FILE" ]; then
        echo -e "1. Your .env file has been uploaded. Monitor the application:"
        echo -e "   ssh -i $PEM_FILE $EC2_USER@$EC2_HOST"
        echo -e "   cd $DEPLOY_DIR/docker && docker-compose logs -f"
        echo
        echo -e "2. After testing, consider tagging this deployment as a new version:"
        echo -e "   git tag -a v0.2.1-alpha -m \"Clean deployment on $(date)\""
        echo -e "   git push origin v0.2.1-alpha"
    else
        echo -e "1. Configure API keys in the .env file:"
        echo -e "   ssh -i $PEM_FILE $EC2_USER@$EC2_HOST"
        echo -e "   nano $DEPLOY_DIR/.env"
        echo
        echo -e "2. Monitor the application:"
        echo -e "   ssh -i $PEM_FILE $EC2_USER@$EC2_HOST"
        echo -e "   cd $DEPLOY_DIR/docker && docker-compose logs -f"
        echo
        echo -e "3. After testing, consider tagging this deployment as a new version:"
        echo -e "   git tag -a v0.2.1-alpha -m \"Clean deployment on $(date)\""
        echo -e "   git push origin v0.2.1-alpha"
    fi
    echo
else
    echo
    echo -e "${RED}Deployment failed.${NC}"
    exit 1
fi

exit 0
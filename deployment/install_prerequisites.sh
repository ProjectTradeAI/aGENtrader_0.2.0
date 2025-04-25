#!/bin/bash
# Install prerequisites for aGENtrader v2 on EC2 instance

# Colors for console output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================================${NC}"
echo -e "${GREEN}aGENtrader v2 Prerequisites Installation${NC}"
echo -e "${BLUE}=======================================================${NC}"

# Detect OS and distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
    echo -e "${YELLOW}Detected OS: $OS $VER${NC}"
else
    echo -e "${RED}Cannot detect OS. Manual installation required.${NC}"
    exit 1
fi

# Function to install Docker on Amazon Linux 2023
install_docker_amazon_linux() {
    echo -e "${YELLOW}Installing Docker on Amazon Linux...${NC}"
    
    # Update packages
    sudo dnf update -y
    
    # Install docker
    sudo dnf install -y docker
    
    # Start and enable Docker service
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}Docker installed successfully!${NC}"
    echo -e "${YELLOW}NOTE: You may need to log out and log back in for group changes to take effect.${NC}"
}

# Function to install Docker on Ubuntu
install_docker_ubuntu() {
    echo -e "${YELLOW}Installing Docker on Ubuntu...${NC}"
    
    # Update package index and install prerequisites
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    
    # Set up the stable repository
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    
    # Update the package index again and install Docker CE
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Start and enable Docker service
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}Docker installed successfully!${NC}"
    echo -e "${YELLOW}NOTE: You may need to log out and log back in for group changes to take effect.${NC}"
}

# Function to install Docker Compose
install_docker_compose() {
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    
    # Get latest Docker Compose release
    LATEST_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep "tag_name" | cut -d '"' -f 4)
    
    if [ -z "$LATEST_COMPOSE_VERSION" ]; then
        echo -e "${RED}Failed to get latest Docker Compose version. Using v2.18.1 as fallback.${NC}"
        LATEST_COMPOSE_VERSION="v2.18.1"
    fi
    
    # Download and install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/${LATEST_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Create a symbolic link if /usr/bin/docker-compose doesn't exist
    if [ ! -f /usr/bin/docker-compose ]; then
        sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
    fi
    
    echo -e "${GREEN}Docker Compose installed successfully!${NC}"
}

# Function to install screen
install_screen() {
    echo -e "${YELLOW}Installing screen...${NC}"
    
    if [[ "$OS" == *"Amazon Linux"* ]]; then
        sudo dnf install -y screen
    elif [[ "$OS" == *"Ubuntu"* ]]; then
        sudo apt-get install -y screen
    else
        echo -e "${RED}Unsupported OS for automatic screen installation. Please install manually.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Screen installed successfully!${NC}"
}

# Function to install Python and required packages
install_python_packages() {
    echo -e "${YELLOW}Installing Python packages...${NC}"
    
    if [[ "$OS" == *"Amazon Linux"* ]]; then
        sudo dnf install -y python3 python3-pip python3-devel gcc
    elif [[ "$OS" == *"Ubuntu"* ]]; then
        sudo apt-get install -y python3 python3-pip python3-dev build-essential
    else
        echo -e "${RED}Unsupported OS for automatic Python installation. Please install manually.${NC}"
        return 1
    fi
    
    # Install required Python packages
    pip3 install --user pandas numpy python-dotenv openai
    
    echo -e "${GREEN}Python packages installed successfully!${NC}"
}

# Install Docker based on OS
if [[ "$OS" == *"Amazon Linux"* ]]; then
    install_docker_amazon_linux
elif [[ "$OS" == *"Ubuntu"* ]]; then
    install_docker_ubuntu
else
    echo -e "${RED}Unsupported OS for automatic Docker installation. Please install Docker manually.${NC}"
    exit 1
fi

# Install Docker Compose
install_docker_compose

# Install screen
install_screen

# Install Python packages
install_python_packages

# Verify installations
echo -e "${YELLOW}Verifying installations...${NC}"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker installed: $DOCKER_VERSION${NC}"
else
    echo -e "${RED}✗ Docker not installed or not in PATH${NC}"
    echo -e "${YELLOW}You may need to log out and log back in for group changes to take effect.${NC}"
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓ Docker Compose installed: $COMPOSE_VERSION${NC}"
else
    echo -e "${RED}✗ Docker Compose not installed or not in PATH${NC}"
fi

# Check screen
if command -v screen &> /dev/null; then
    SCREEN_VERSION=$(screen --version)
    echo -e "${GREEN}✓ Screen installed: $SCREEN_VERSION${NC}"
else
    echo -e "${RED}✗ Screen not installed or not in PATH${NC}"
fi

# Check Python and packages
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python installed: $PYTHON_VERSION${NC}"
    
    echo -e "${YELLOW}Checking Python packages...${NC}"
    for package in pandas numpy python-dotenv openai; do
        if python3 -c "import $package" 2>/dev/null; then
            echo -e "${GREEN}✓ $package installed${NC}"
        else
            echo -e "${RED}✗ $package not installed${NC}"
        fi
    done
else
    echo -e "${RED}✗ Python 3 not installed or not in PATH${NC}"
fi

echo -e "${BLUE}=======================================================${NC}"
echo -e "${GREEN}Prerequisites installation complete!${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo -e "${YELLOW}IMPORTANT: You may need to log out and log back in for Docker group changes to take effect.${NC}"
echo -e "${YELLOW}After logging back in, run the following command to verify Docker works without sudo:${NC}"
echo -e "${GREEN}docker run hello-world${NC}"
echo -e "${BLUE}=======================================================${NC}"
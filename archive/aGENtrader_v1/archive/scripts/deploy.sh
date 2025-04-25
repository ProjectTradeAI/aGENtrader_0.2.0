#!/bin/bash
set -e

# Configuration
APP_NAME="trading-bot"
CONTAINER_PORT=8080
HOST_PORT=8080

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting deployment for $APP_NAME...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please create a .env file with required environment variables:"
    echo "SESSION_SECRET=your_secret_here"
    exit 1
fi

# Build the Docker image with no cache
echo -e "${GREEN}Building Docker image...${NC}"
docker build --no-cache -t $APP_NAME .

# Stop and remove existing container if it exists
if docker ps -a | grep -q $APP_NAME; then
    echo -e "${GREEN}Stopping existing container...${NC}"
    docker stop $APP_NAME || true
    docker rm $APP_NAME || true
fi

# Run the new container
echo -e "${GREEN}Starting new container...${NC}"
docker run -d \
    --name $APP_NAME \
    --restart unless-stopped \
    -p $HOST_PORT:$CONTAINER_PORT \
    --env-file .env \
    $APP_NAME

# Health check
echo -e "${GREEN}Performing health check...${NC}"
sleep 5
if curl -s http://localhost:$HOST_PORT/health > /dev/null; then
    echo -e "${GREEN}Deployment successful! Application is running on port $HOST_PORT${NC}"
else
    echo -e "${RED}Health check failed. Please check container logs:${NC}"
    docker logs $APP_NAME
    exit 1
fi

# Show container status
docker ps | grep $APP_NAME

echo -e "${GREEN}Deployment completed successfully!${NC}"
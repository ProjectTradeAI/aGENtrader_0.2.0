#!/bin/bash
# aGENtrader v2.2 - Local Deployment Script
# This script deploys aGENtrader v2.2 locally using Docker

set -e

# Configuration
CONTAINER_NAME="agentrader"
IMAGE_NAME="agentrader"
TAG="v2.2"
PORT="8000"
ENV_FILE=".env"

# Display header
echo "======================================================================"
echo "             aGENtrader v2.2 - Local Deployment Script"
echo "======================================================================"
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Warning: Environment file $ENV_FILE not found."
    echo "Creating minimal .env file..."
    cat > "$ENV_FILE" << EOL
# aGENtrader v2.2 Environment Variables
MODE=test
DEFAULT_SYMBOL=BTC/USDT
DEFAULT_INTERVAL=1h
LOG_LEVEL=INFO
PYTHONPATH=.:$PYTHONPATH
EOL
    echo "Created minimal $ENV_FILE file."
fi

# Build the Docker image if it doesn't exist
if ! docker image inspect "$IMAGE_NAME:$TAG" &> /dev/null; then
    echo "Building Docker image..."
    
    if [ -f "deployment/build_image.sh" ]; then
        bash deployment/build_image.sh
    else
        echo "Error: Docker build script not found at deployment/build_image.sh"
        exit 1
    fi
fi

# Stop and remove existing container if it exists
if docker ps -a | grep -q "$CONTAINER_NAME"; then
    echo "Stopping and removing existing container: $CONTAINER_NAME"
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
fi

# Run the container
echo "Starting aGENtrader container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:$PORT" \
    --env-file "$ENV_FILE" \
    -e "IN_DOCKER=true" \
    -e "MODE=test" \
    -e "TEST_DURATION=24h" \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/reports:/app/reports" \
    -v "$(pwd)/trades:/app/trades" \
    -v "$(pwd)/config:/app/config" \
    -v "$(pwd)/data:/app/data" \
    "$IMAGE_NAME:$TAG"

# Check if container started successfully
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo
    echo "Deployment successful!"
    echo "aGENtrader v2.2 is running at: http://localhost:$PORT"
    echo
    echo "To view logs:"
    echo "  docker logs -f $CONTAINER_NAME"
    echo
    echo "To stop the container:"
    echo "  docker stop $CONTAINER_NAME"
    echo
else
    echo
    echo "Deployment failed. Container is not running."
    echo "Check logs with: docker logs $CONTAINER_NAME"
    exit 1
fi

# Print container status
echo "Container status:"
docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo

exit 0
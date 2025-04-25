#!/bin/bash
# aGENtrader v2.2 - Docker Image Build Script
# This script builds the Docker image for aGENtrader v2.2

set -e

# Configuration
IMAGE_NAME="agentrader"
TAG="v2.2"
DOCKERFILE_PATH="docker/Dockerfile"

# Display header
echo "======================================================================"
echo "               aGENtrader v2.2 - Docker Image Builder"
echo "======================================================================"
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo "Error: Dockerfile not found at $DOCKERFILE_PATH"
    exit 1
fi

# Build the image
echo "Building Docker image: $IMAGE_NAME:$TAG"
echo "Using Dockerfile: $DOCKERFILE_PATH"
echo

docker build -t "$IMAGE_NAME:$TAG" -f "$DOCKERFILE_PATH" .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo
    echo "Build successful!"
    echo "Image created: $IMAGE_NAME:$TAG"
    
    # Tag as latest
    docker tag "$IMAGE_NAME:$TAG" "$IMAGE_NAME:latest"
    echo "Also tagged as: $IMAGE_NAME:latest"
    
    echo
    echo "To run the container:"
    echo "  docker run -p 8000:8000 --name agentrader -d $IMAGE_NAME:$TAG"
    echo
else
    echo
    echo "Build failed."
    exit 1
fi

exit 0
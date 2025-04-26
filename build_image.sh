#!/bin/bash
# aGENtrader v2.2 - Docker Image Build Script
# This script builds the Docker image for aGENtrader v2.2

set -e

# Configuration
IMAGE_NAME="aGENtrader"

# Get version from Git (use tag if available, otherwise use commit hash)
if [ -n "$VERSION" ]; then
    # Use version passed as environment variable
    TAG=$VERSION
else
    # Try to get version from Git
    TAG=$(git describe --tags --always 2>/dev/null || echo "v0.2.0")
fi

DOCKERFILE_PATH="docker/Dockerfile"

# Display header
echo "======================================================================"
echo "               aGENtrader v2.2 - Docker Image Builder"
echo "======================================================================"
echo "Building version: $TAG"
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

# Pass build args for version
docker build \
    --build-arg VERSION=$TAG \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    -t "$IMAGE_NAME:$TAG" \
    -f "$DOCKERFILE_PATH" .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo
    echo "Build successful!"
    echo "Image created: $IMAGE_NAME:$TAG"
    
    # Tag as latest
    docker tag "$IMAGE_NAME:$TAG" "$IMAGE_NAME:latest"
    echo "Also tagged as: $IMAGE_NAME:latest"
    
    # Print image details
    docker images "$IMAGE_NAME:$TAG" --format "Image Size: {{.Size}}"
    
    echo
    echo "To run the container:"
    echo "  docker run -p 8000:8000 --name agentrader -d $IMAGE_NAME:$TAG"
    echo
    echo "Or use docker-compose:"
    echo "  cd docker && VERSION=$TAG docker-compose up -d"
    echo
else
    echo
    echo "Build failed."
    exit 1
fi

exit 0
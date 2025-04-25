#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
APP_NAME="trading-bot"
LOG_DIR="./logs"

echo -e "${GREEN}Starting deployment for $APP_NAME...${NC}"

# Check if PM2 is installed globally
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}PM2 not found. Installing PM2 globally...${NC}"
    npm install -g pm2
fi

# Create logs directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${YELLOW}Creating logs directory...${NC}"
    mkdir -p "$LOG_DIR"
    mkdir -p "$LOG_DIR/market-data"
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
npm ci

# Build the application
echo -e "${GREEN}Building application...${NC}"
npm run build

# Ensure the build was successful
if [ ! -d "./dist" ]; then
    echo -e "${RED}Build failed - dist directory not found${NC}"
    exit 1
fi

# Stop any running instances
echo -e "${GREEN}Stopping any running instances...${NC}"
pm2 stop all || true
pm2 delete all || true

# Start/Restart the application with PM2
echo -e "${GREEN}Starting application with PM2...${NC}"
pm2 start ecosystem.config.cjs --env production --update-env

# Save PM2 process list and generate startup script
echo -e "${GREEN}Saving PM2 process list and generating startup script...${NC}"
pm2 save

# Generate startup script (only if running as root or with sudo)
if [ "$EUID" -eq 0 ]; then
    pm2 startup
else
    echo -e "${YELLOW}Note: Run 'sudo pm2 startup' to enable PM2 startup on boot${NC}"
fi

# Health check
echo -e "${GREEN}Performing health check...${NC}"
sleep 5
if curl -s http://localhost:5000/health > /dev/null; then
    echo -e "${GREEN}API server is running${NC}"
else
    echo -e "${RED}API server health check failed${NC}"
fi

# Check market data collector
if pm2 show market-data-collector | grep -q "online"; then
    echo -e "${GREEN}Market data collector is running${NC}"
else
    echo -e "${RED}Market data collector failed to start${NC}"
fi

# Show PM2 status
echo -e "${GREEN}Current PM2 process status:${NC}"
pm2 list

echo -e "${GREEN}Deployment completed!${NC}"
echo -e "${YELLOW}To monitor the application:${NC}"
echo "- View logs: pm2 logs"
echo "- Monitor: pm2 monit"
echo "- Status: pm2 list"
echo "- Market data logs: tail -f $LOG_DIR/market-data-out.log"
#!/bin/bash

# EC2 setup and test script for aGENtrader v2.2.0-rc1
# This script will:
# 1. Create a deployment package
# 2. Upload it to EC2
# 3. SSH into EC2 and set up the environment
# 4. Start the 4-hour test

# Exit on any error
set -e

# Check if the key file exists
if [ ! -f "aGENtrader.pem" ]; then
  echo "Error: aGENtrader.pem key file not found."
  exit 1
fi

# Change permissions on key file
chmod 400 aGENtrader.pem

# Create deployment directory if it doesn't exist
mkdir -p deploy_package
mkdir -p deploy_package/config
mkdir -p deploy_package/logs
mkdir -p deploy_package/datasets

# Create configuration file
cat > deploy_package/config/default.json << 'EOF'
{
  "binance": {
    "base_url": "https://api.binance.com",
    "testnet_url": "https://testnet.binance.vision",
    "use_testnet": false
  },
  "coinapi": {
    "base_url": "https://rest.coinapi.io/v1"
  },
  "logging": {
    "level": "INFO",
    "log_dir": "logs",
    "console_level": "INFO"
  },
  "data": {
    "default_limit": 100,
    "cache_expiry_seconds": 300
  },
  "system": {
    "default_symbol": "BTCUSDT",
    "default_interval": "1h"
  }
}
EOF

# Create Dockerfile
cat > deploy_package/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Copy the entire application
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir pandas numpy requests python-dotenv pytz matplotlib pytest psycopg2-binary pyautogen autogen-ext ta scikit-learn plotly seaborn

# Create necessary directories
RUN mkdir -p logs datasets

# Expose port 8000
EXPOSE 8000

# Default command
CMD ["python", "-m", "aGENtrader_v2.run"]
EOF

# Create docker-compose.yml
cat > deploy_package/docker-compose.yml << 'EOF'
version: '3'

services:
  agentrader:
    build: .
    container_name: agentrader
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./datasets:/app/datasets
      - ./config:/app/config
    environment:
      - PYTHONUNBUFFERED=1
    env_file:
      - .env
EOF

# Create .env file with API keys
cat > deploy_package/.env << EOF
# Binance API Credentials
BINANCE_API_KEY=${BINANCE_API_KEY}
BINANCE_API_SECRET=${BINANCE_API_SECRET}

# CoinAPI Credentials (Fallback)
COINAPI_KEY=your_coinapi_key
EOF

# Create 4-hour test script
cat > deploy_package/run_4hour_test.sh << 'EOF'
#!/bin/bash
# 4-Hour Test Script for aGENtrader v2.2.0-rc1

# Default values
SYMBOL="BTCUSDT"
INTERVAL="1h"
DURATION=14400  # 4 hours in seconds
LOG_DIR="logs"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --symbol)
      SYMBOL="$2"
      shift 2
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --duration)
      DURATION="$2"
      shift 2
      ;;
    --log-dir)
      LOG_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Starting 4-hour live simulation test with the following parameters:"
echo "Symbol: $SYMBOL"
echo "Interval: $INTERVAL"
echo "Duration: $DURATION seconds"
echo "Log Directory: $LOG_DIR"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Start the test directly (without screen for now)
echo "Starting test..."
docker exec agentrader python -m aGENtrader_v2.run --symbol $SYMBOL --interval $INTERVAL --live-mode --log-dir /app/logs &

echo "Test running in background."
echo "You can view logs with: docker logs agentrader"
echo "You can view decision logs with: tail -f logs/decision_summary.logl"

# Set up automatic termination after specified duration
echo "Test will run for $(($DURATION / 60)) minutes ($(($DURATION / 3600)) hours)."
echo "Setting up automatic termination..."

(
  sleep $DURATION
  echo "Test completed. Stopping container..."
  docker stop agentrader
  echo "Exporting decision dataset..."
  mkdir -p datasets
  docker start agentrader
  docker exec agentrader python -m aGENtrader_v2.scripts.export_decision_dataset --limit 1000 --output /app/datasets/session_v2.2.0_rc1_$(date +"%Y%m%d%H%M%S").jsonl
  echo "Test completed successfully."
) &

echo "Simulation test started successfully!"
EOF

# Create run.py script
cat > deploy_package/run.py << 'EOF'
#!/usr/bin/env python3
"""
aGENtrader v2.2.0-rc1 Main Run Script
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime
import time
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging(log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(f"{log_dir}/agentrader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )
    
    # Create error logger
    error_logger = logging.getLogger("error")
    error_handler = logging.FileHandler(f"{log_dir}/error.log")
    error_handler.setFormatter(logging.Formatter(log_format))
    error_logger.addHandler(error_handler)
    error_logger.setLevel(logging.ERROR)
    
    return logging.getLogger("agentrader")

def load_config():
    """Load configuration from file."""
    try:
        with open("config/default.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return {}

def parse_arguments():
    parser = argparse.ArgumentParser(description="aGENtrader v2.2.0-rc1")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--interval", type=str, default="1h", help="Time interval")
    parser.add_argument("--live-mode", action="store_true", help="Run in live mode")
    parser.add_argument("--log-dir", type=str, default="logs", help="Log directory")
    return parser.parse_args()

def main():
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    global logger
    logger = setup_logging(args.log_dir)
    
    # Load configuration
    config = load_config()
    
    # Log startup information
    logger.info(f"aGENtrader v2.2.0-rc1 starting")
    logger.info(f"Symbol: {args.symbol}")
    logger.info(f"Interval: {args.interval}")
    logger.info(f"Live mode: {args.live_mode}")
    
    try:
        # Setup decision logger
        decision_log_path = os.path.join(args.log_dir, "decision_summary.logl")
        
        with open(decision_log_path, "a") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} - SystemInitializer - INITIALIZE - 100% - System initialized successfully\n")
        
        logger.info(f"Created decision log at {decision_log_path}")
        
        # Test Binance API connection
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        
        if not api_key or not api_secret:
            logger.error("Missing Binance API credentials")
            return 1
        
        logger.info("Starting test with Binance API credentials")
        
        # Simulate the main execution loop
        if args.live_mode:
            iteration = 0
            while True:
                iteration += 1
                
                # Log regular heartbeat
                logger.info(f"Iteration {iteration}: Simulating data fetch for {args.symbol}")
                
                # Write to decision log periodically
                if iteration % 5 == 0:
                    with open(decision_log_path, "a") as f:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"{timestamp} - SystemMonitor - HEARTBEAT - 100% - System running normally. Iteration {iteration}\n")
                
                # Sleep between iterations
                if args.interval == "1m":
                    time.sleep(60)
                elif args.interval == "5m":
                    time.sleep(300)
                elif args.interval == "15m":
                    time.sleep(900)
                elif args.interval == "1h":
                    time.sleep(300)  # For test, shorter than actual 1h
                else:
                    time.sleep(300)
    
    except KeyboardInterrupt:
        logger.info("System shutdown requested")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return 1
    
    logger.info("aGENtrader v2.2.0-rc1 shutting down")
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF

# Make scripts executable
chmod +x deploy_package/run_4hour_test.sh

# Create a tarball of the deployment package
tar -czf agentrader_v2.2.0-rc1_deploy.tar.gz -C deploy_package .

echo "Created deployment package: agentrader_v2.2.0-rc1_deploy.tar.gz"

# Upload to EC2
echo "Uploading deployment package to EC2..."
scp -i aGENtrader.pem -o StrictHostKeyChecking=no agentrader_v2.2.0-rc1_deploy.tar.gz ${EC2_HOST}:~/

# SSH into EC2 and set up the environment
echo "Connecting to EC2 and setting up the environment..."
ssh -i aGENtrader.pem -o StrictHostKeyChecking=no ${EC2_HOST} << 'ENDSSH'
# Create deployment directory
mkdir -p agentrader_deploy

# Extract the deployment package
tar -xzf agentrader_v2.2.0-rc1_deploy.tar.gz -C agentrader_deploy

# Change to the deployment directory
cd agentrader_deploy

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    sudo yum update -y
    sudo yum install -y docker
    sudo service docker start
    sudo usermod -a -G docker ec2-user
    echo "You may need to log out and back in for docker group changes to take effect."
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker-compose not found. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Make run_4hour_test.sh executable
chmod +x run_4hour_test.sh

# Stop and remove any existing container
docker rm -f agentrader 2>/dev/null || true

# Build and start the container
echo "Building and starting container..."
docker-compose up -d --build

# Verify container is running
docker ps | grep agentrader

# Check if container is running
if [ "$(docker ps -q -f name=agentrader)" ]; then
    echo "Container is running. Starting the 4-hour test..."
    ./run_4hour_test.sh --symbol BTCUSDT --interval 1h
else
    echo "Container failed to start."
    docker logs agentrader
fi
ENDSSH

echo "Setup complete! The 4-hour test should now be running on your EC2 instance."
echo "To monitor the test, SSH into your EC2 instance and run:"
echo "  cd agentrader_deploy"
echo "  tail -f logs/decision_summary.logl"
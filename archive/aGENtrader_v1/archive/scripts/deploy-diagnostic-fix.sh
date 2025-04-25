#!/bin/bash
# Deploy diagnostic and fix scripts to EC2 and run them

# Set parameters
EC2_IP="51.20.250.135"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Get environment variables
DB_URL=$(node -e "console.log(process.env.DATABASE_URL || '')")
ALPACA_API_KEY=$(node -e "console.log(process.env.ALPACA_API_KEY || '')")
ALPACA_API_SECRET=$(node -e "console.log(process.env.ALPACA_API_SECRET || '')")
OPENAI_API_KEY=$(node -e "console.log(process.env.OPENAI_API_KEY || '')")

# Upload the files to EC2
echo "Uploading diagnostic scripts to EC2..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no agent_framework_diagnostic.py "$SSH_USER@$EC2_IP:$EC2_DIR/"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/agent_framework_diagnostic.py"

# Run the diagnostic
echo "Running diagnostic and fix on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' python3 agent_framework_diagnostic.py"

# Download any generated files
echo "Downloading generated files from EC2..."
mkdir -p ./results/diagnostic
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/enhanced_agent_logging.py" ./results/diagnostic/ 2>/dev/null
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/test_agent_framework.py" ./results/diagnostic/ 2>/dev/null
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/updated_full_agent_backtest.py" ./results/diagnostic/ 2>/dev/null
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/run-updated-backtest.sh" ./results/diagnostic/ 2>/dev/null
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/agent_framework_diagnostic_*.log" ./results/diagnostic/ 2>/dev/null

# Run the test script
echo "Running test agent framework on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' python3 test_agent_framework.py"

# Run the updated backtest with appropriate parameters
echo "Running updated backtest on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' bash run-updated-backtest.sh BTCUSDT 1h 2025-04-10 2025-04-12 10000"

# Download the log files
echo "Downloading log files from EC2..."
mkdir -p ./results/logs
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/data/logs/enhanced_agent_comms_*.log" ./results/logs/ 2>/dev/null
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/test_agent_framework_*.log" ./results/logs/ 2>/dev/null
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/updated_agent_backtest_*.log" ./results/logs/ 2>/dev/null

# Download result files
echo "Downloading result files from EC2..."
mkdir -p ./results
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/results/updated_agent_backtest_*.json" ./results/ 2>/dev/null
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/results/summary_*.json" ./results/ 2>/dev/null

echo "Diagnostic and fix process complete."
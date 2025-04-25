
#!/bin/bash
# EC2 Setup Script for Trading Bot
# This script sets up an EC2 instance for running the trading bot

# Exit on any error
set -e

echo "=== Setting up EC2 instance for Trading Bot ==="

# Update system
echo "Updating system packages..."
sudo yum update -y

# Install Node.js
echo "Installing Node.js..."
curl -sL https://rpm.nodesource.com/setup_16.x | sudo bash -
sudo yum install -y nodejs

# Install Python and related packages
echo "Installing Python and dependencies..."
sudo yum install -y python3 python3-pip python3-devel gcc git

# Install PM2 globally
echo "Installing PM2 for process management..."
sudo npm install -g pm2

# Create application directory
echo "Setting up application directory..."
mkdir -p ~/trading-bot
cd ~/trading-bot

# Clone repository (if using git)
# echo "Cloning repository..."
# git clone YOUR_REPOSITORY_URL .

# Create log directory
mkdir -p logs

# Copy ecosystem.config.js if it doesn't exist
if [ ! -f ecosystem.config.js ]; then
  echo "Creating PM2 ecosystem config..."
  cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'trading-bot',
    script: './main.py',
    interpreter: 'python3',
    env: {
      NODE_ENV: 'production'
    },
    instances: 1,
    exec_mode: 'fork',
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    error_file: './logs/error.log',
    out_file: './logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true
  }]
}
EOF
fi

# Install Python dependencies
echo "Installing Python requirements..."
pip3 install --user numpy pandas requests schedule

# Set up environment variables
echo "Setting up environment variables..."
if [ ! -f .env ]; then
  cat > .env << EOF
# Trading Bot Configuration
LOG_LEVEL=info
EOF
fi

echo "Setting up cron job for monitoring..."
# Add cron job to check if bot is running
(crontab -l 2>/dev/null; echo "*/10 * * * * cd ~/trading-bot && ./scripts/health_check.sh >> logs/health_check.log 2>&1") | crontab -

# Health check script
mkdir -p scripts
cat > scripts/health_check.sh << EOF
#!/bin/bash
echo "[$(date)] Running health check"
if ! pm2 list | grep -q "trading-bot"; then
  echo "[$(date)] Trading bot not running, restarting..."
  cd ~/trading-bot
  pm2 start ecosystem.config.js
  pm2 save
else
  echo "[$(date)] Trading bot is running"
fi
EOF
chmod +x scripts/health_check.sh

echo "=== EC2 setup completed ==="
echo "You can now deploy your application code to this server"
echo "Once code is deployed, start the application with:"
echo "pm2 start ecosystem.config.js && pm2 save"

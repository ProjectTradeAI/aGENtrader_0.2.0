#!/bin/bash
# Deploy Authentic Backtesting Framework to EC2 (Fixed Version)
# This script handles key format issues and properly deploys the backtesting framework

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
  echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

log_info() {
  echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Check if EC2 environment variables are set
if [ -z "$EC2_PUBLIC_IP" ]; then
  log_error "EC2_PUBLIC_IP environment variable is not set."
  log_error "Please set it by running: export EC2_PUBLIC_IP=<your-ec2-ip>"
  exit 1
fi

# Create a more deterministic key file
create_key_file() {
  KEY_PATH="$1"
  
  # Check if EC2_KEY is set
  if [ -z "$EC2_KEY" ]; then
    log_error "EC2_KEY environment variable is not set."
    return 1
  fi
  
  # Clean the key content to handle various formats
  # This extracts just the key data, removing headers and extra newlines
  log_info "Creating a clean key file..."
  
  # If key already has BEGIN/END markers, write it cleanly with proper newlines
  if [[ "$EC2_KEY" == *"BEGIN RSA PRIVATE KEY"* ]]; then
    # The key may have markers with incorrect formatting, so let's clean it up
    CLEANED_KEY=$(echo "$EC2_KEY" | grep -v "BEGIN\|END\|PRIVATE\|KEY" | tr -d '\n\r ')
    
    # Write with proper BEGIN/END markers and formatting
    echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
    echo "$CLEANED_KEY" | fold -w 64 >> "$KEY_PATH"
    echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
  else
    # The key is likely just the base64 data without markers
    echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
    echo "$EC2_KEY" | fold -w 64 >> "$KEY_PATH"
    echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
  fi
  
  # Set proper permissions
  chmod 600 "$KEY_PATH"
  
  # Verify the key format (this won't verify if the key is correct for the server)
  if ssh-keygen -l -f "$KEY_PATH" > /dev/null 2>&1; then
    log_info "✅ Successfully created a valid key file"
    return 0
  else
    log_error "❌ Failed to create a valid key file"
    return 1
  fi
}

# Create a temporary directory for staging files
TMP_DIR=$(mktemp -d)
KEY_PATH="$TMP_DIR/ec2_key.pem"

# Create the key file
if ! create_key_file "$KEY_PATH"; then
  log_error "Failed to create a valid key file. Cannot continue."
  rm -rf "$TMP_DIR"
  exit 1
fi

# Test SSH connection
log "Testing SSH connection to EC2..."
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 ec2-user@$EC2_PUBLIC_IP "echo 'Connection successful'" > /dev/null 2>&1; then
  log_error "Failed to connect to EC2 instance. Check your EC2_KEY and EC2_PUBLIC_IP."
  cat "$KEY_PATH" | head -1
  cat "$KEY_PATH" | tail -1
  rm -rf "$TMP_DIR"
  exit 1
fi

log "✅ Successfully connected to EC2 instance"

# Create directories on EC2
log "Creating directories on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "mkdir -p /home/ec2-user/aGENtrader/backtesting/core /home/ec2-user/aGENtrader/backtesting/utils /home/ec2-user/aGENtrader/backtesting/analysis /home/ec2-user/aGENtrader/backtesting/scripts /home/ec2-user/aGENtrader/data/analysis"

# Package and deploy backtesting framework
log "Deploying authentic backtesting framework to EC2..."

# Create subdirectories in temporary directory
mkdir -p "$TMP_DIR/backtesting/core"
mkdir -p "$TMP_DIR/backtesting/utils"
mkdir -p "$TMP_DIR/backtesting/analysis"
mkdir -p "$TMP_DIR/backtesting/scripts"

# Copy files to temp directory
cp ./backtesting/core/authentic_backtest.py "$TMP_DIR/backtesting/core/"
cp ./backtesting/utils/data_integrity_checker.py "$TMP_DIR/backtesting/utils/"
cp ./backtesting/utils/market_data.py "$TMP_DIR/backtesting/utils/"
cp ./backtesting/analysis/visualize_backtest.py "$TMP_DIR/backtesting/analysis/"
cp ./backtesting/scripts/run_authentic_backtest.sh "$TMP_DIR/backtesting/scripts/"
chmod +x "$TMP_DIR/backtesting/scripts/run_authentic_backtest.sh"

# Create a tar archive
TAR_FILE="$TMP_DIR/authentic-backtest.tar.gz"
(cd "$TMP_DIR" && tar -czf "authentic-backtest.tar.gz" ./backtesting)

# Upload the tar file to EC2
log "Uploading package to EC2..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$TAR_FILE" ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/

# Extract on EC2
log "Extracting package on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user && tar -xzf authentic-backtest.tar.gz && cp -r backtesting/* aGENtrader/backtesting/ && chmod +x aGENtrader/backtesting/scripts/run_authentic_backtest.sh"

# Test database connection on EC2
log "Testing the deployed backtesting framework..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 -c 'import sys; sys.path.append(\"/home/ec2-user/aGENtrader\"); from backtesting.utils.data_integrity_checker import check_database_access; print(\"Database connection test:\"); print(check_database_access())'"

# Copy the fixed key for future use
cp "$KEY_PATH" /tmp/ec2_key_fixed.pem
chmod 600 /tmp/ec2_key_fixed.pem

# Clean up
log "Cleaning up..."
rm -rf "$TMP_DIR"

log "✅ Authentic backtesting framework deployed successfully to EC2!"
log_info "Your fixed key file has been saved to /tmp/ec2_key_fixed.pem for future use"
log_info "You can now run backtests on EC2 with:"
log_info "  EC2_KEY_PATH=/tmp/ec2_key_fixed.pem ./run-authentic-backtest-fixed.sh --symbol BTCUSDT --interval 1h --start 2025-04-01 --end 2025-04-10"
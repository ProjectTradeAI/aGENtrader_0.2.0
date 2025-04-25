#!/bin/bash
# Debug EC2 Key format

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

# Check if EC2_KEY is set
if [ -z "$EC2_KEY" ]; then
  log_error "EC2_KEY environment variable is not set."
  exit 1
fi

# Create a temporary file for the key
KEY_PATH="/tmp/debug_ec2_key.pem"

# Output key stats
log "Analyzing EC2_KEY environment variable..."
log_info "EC2_KEY variable length: ${#EC2_KEY}"
log_info "First 20 characters: ${EC2_KEY:0:20}..."
log_info "Last 20 characters: ...${EC2_KEY: -20}"

# Check if key looks like it contains BEGIN/END markers
if [[ $EC2_KEY == *"BEGIN"* && $EC2_KEY == *"END"* ]]; then
  log_info "The key appears to contain BEGIN/END markers"
else
  log_info "The key does not appear to contain BEGIN/END markers"
fi

# Check if key is base64 encoded
if [[ $EC2_KEY =~ ^[A-Za-z0-9+/=]+$ ]]; then
  log_info "The key appears to be base64 encoded"
else
  log_info "The key does not appear to be solely base64 encoded"
fi

# Try to fix common issues
log "Attempting to create a properly formatted key file..."

# Method 1: Just write the key as is
echo "$EC2_KEY" > "${KEY_PATH}_1"
chmod 600 "${KEY_PATH}_1"
log_info "Method 1: Direct write complete"

# Method 2: Write with BEGIN/END markers if not present
if [[ $EC2_KEY != *"BEGIN"* ]]; then
  echo "-----BEGIN RSA PRIVATE KEY-----" > "${KEY_PATH}_2"
  echo "$EC2_KEY" | fold -w 64 >> "${KEY_PATH}_2"
  echo "-----END RSA PRIVATE KEY-----" >> "${KEY_PATH}_2"
else
  echo "$EC2_KEY" > "${KEY_PATH}_2"
fi
chmod 600 "${KEY_PATH}_2"
log_info "Method 2: Write with markers complete"

# Method 3: Clean up and normalize
CLEANED_KEY=$(echo "$EC2_KEY" | grep -v "BEGIN\|END\|PRIVATE\|KEY" | tr -d '\n\r')
echo "-----BEGIN RSA PRIVATE KEY-----" > "${KEY_PATH}_3"
echo "$CLEANED_KEY" | fold -w 64 >> "${KEY_PATH}_3"
echo "-----END RSA PRIVATE KEY-----" >> "${KEY_PATH}_3"
chmod 600 "${KEY_PATH}_3"
log_info "Method 3: Cleaned format complete"

# Check each key file format
for i in 1 2 3; do
  curr_path="${KEY_PATH}_${i}"
  log_info "Testing key file method $i:"
  
  # Display key file format (first and last line only)
  echo "  First line: $(head -n 1 $curr_path)"
  echo "  Last line: $(tail -n 1 $curr_path)"
  
  # Try to use ssh-keygen to test the key
  if ssh-keygen -l -f "$curr_path" > /dev/null 2>&1; then
    log "✅ Method $i key is valid!"
    echo "  Fingerprint: $(ssh-keygen -l -f $curr_path)"
    
    # Try a simple SSH command with timeout to avoid hanging
    log_info "Attempting SSH connection with method $i key..."
    timeout 5 ssh -i "$curr_path" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 ec2-user@$EC2_PUBLIC_IP "echo 'Connection successful'" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
      log "✅ Method $i key successfully connected to EC2!"
      cp "$curr_path" "$KEY_PATH"
      log_info "Copied method $i key to $KEY_PATH for future use"
      break
    else
      log_warning "Method $i key failed to connect to EC2"
    fi
  else
    log_error "❌ Method $i key is not valid. ssh-keygen failed."
  fi
done

log "EC2 key debugging completed. Check the output above for details."
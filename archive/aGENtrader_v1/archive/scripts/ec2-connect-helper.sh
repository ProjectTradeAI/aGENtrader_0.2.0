#!/bin/bash
# EC2 Connection Helper
# This script provides a reliable way to connect to EC2

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

# Check if EC2_PUBLIC_IP is set
if [ -z "$EC2_PUBLIC_IP" ]; then
  log_error "EC2_PUBLIC_IP environment variable is not set."
  log_error "Please set it by running: export EC2_PUBLIC_IP=<your-ec2-ip>"
  exit 1
fi

# Function to check if a file is a valid private key
check_key_file() {
  KEY_FILE="$1"
  if ssh-keygen -l -f "$KEY_FILE" &>/dev/null; then
    return 0
  else
    return 1
  fi
}

# Function to test SSH connection
test_ssh_connection() {
  KEY_FILE="$1"
  timeout 5 ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=3 ec2-user@$EC2_PUBLIC_IP "echo 'Connected'" &>/dev/null
  return $?
}

# Try to use the EC2_KEY environment variable
if [ -n "$EC2_KEY" ]; then
  log_info "Using EC2_KEY environment variable"
  KEY_FILE="/tmp/ec2_key_temp.pem"

  # Method 1: Direct write
  echo "$EC2_KEY" > "$KEY_FILE"
  chmod 600 "$KEY_FILE"
  
  if check_key_file "$KEY_FILE"; then
    log_info "Method 1: Direct write succeeded"
    if test_ssh_connection "$KEY_FILE"; then
      log_info "Successfully connected to EC2 using Method 1"
      EC2_KEY_PATH="$KEY_FILE"
    else
      log_warning "Method 1: Key validated but connection failed"
    fi
  else
    log_warning "Method 1: Direct write failed"
    
    # Method 2: Try with BEGIN/END markers
    log_info "Trying Method 2: With markers"
    echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_FILE"
    echo "$EC2_KEY" | grep -v "BEGIN\|END\|PRIVATE\|KEY" | tr -d '\n\r' | fold -w 64 >> "$KEY_FILE"
    echo "-----END RSA PRIVATE KEY-----" >> "$KEY_FILE"
    chmod 600 "$KEY_FILE"
    
    if check_key_file "$KEY_FILE"; then
      log_info "Method 2: With markers succeeded"
      if test_ssh_connection "$KEY_FILE"; then
        log_info "Successfully connected to EC2 using Method 2"
        EC2_KEY_PATH="$KEY_FILE"
      else
        log_warning "Method 2: Key validated but connection failed"
      fi
    else
      log_warning "Method 2: With markers failed"
      
      # Method 3: Advanced format
      log_info "Trying Method 3: Advanced format"
      echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_FILE"
      echo "$EC2_KEY" | sed 's/-*BEGIN [A-Z]* PRIVATE KEY-*//g' | sed 's/-*END [A-Z]* PRIVATE KEY-*//g' | tr -d '\n\r\t ' | fold -w 64 >> "$KEY_FILE"
      echo "-----END RSA PRIVATE KEY-----" >> "$KEY_FILE"
      chmod 600 "$KEY_FILE"
      
      if check_key_file "$KEY_FILE"; then
        log_info "Method 3: Advanced format succeeded"
        if test_ssh_connection "$KEY_FILE"; then
          log_info "Successfully connected to EC2 using Method 3"
          EC2_KEY_PATH="$KEY_FILE"
        else
          log_warning "Method 3: Key validated but connection failed"
        fi
      else
        log_warning "Method 3: Advanced format failed"
      fi
    fi
  fi
elif [ -n "$EC2_PRIVATE_KEY" ]; then
  log_info "Using EC2_PRIVATE_KEY environment variable"
  KEY_FILE="/tmp/ec2_private_key_temp.pem"
  echo "$EC2_PRIVATE_KEY" > "$KEY_FILE"
  chmod 600 "$KEY_FILE"
  
  if check_key_file "$KEY_FILE"; then
    log_info "EC2_PRIVATE_KEY is valid"
    if test_ssh_connection "$KEY_FILE"; then
      log_info "Successfully connected to EC2 using EC2_PRIVATE_KEY"
      EC2_KEY_PATH="$KEY_FILE"
    else
      log_warning "EC2_PRIVATE_KEY validated but connection failed"
    fi
  else
    log_error "EC2_PRIVATE_KEY is not valid"
  fi
elif [ -f "$EC2_KEY_PATH" ]; then
  log_info "Using key file at EC2_KEY_PATH: $EC2_KEY_PATH"
  
  if check_key_file "$EC2_KEY_PATH"; then
    log_info "EC2_KEY_PATH is valid"
    if test_ssh_connection "$EC2_KEY_PATH"; then
      log_info "Successfully connected to EC2 using EC2_KEY_PATH"
    else
      log_warning "EC2_KEY_PATH validated but connection failed"
    fi
  else
    log_error "EC2_KEY_PATH is not valid"
  fi
else
  log_error "No SSH key available. Please set EC2_KEY or EC2_PRIVATE_KEY environment variable."
  exit 1
fi

# Here we need to have a valid key
if [ -z "$EC2_KEY_PATH" ]; then
  log_error "Failed to create a valid key file. Cannot continue."
  exit 1
fi

log_info "Using key file: $EC2_KEY_PATH"

# Check if we were passed a command
if [ $# -gt 0 ]; then
  log_info "Running command on EC2: $@"
  ssh -i "$EC2_KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "$@"
  exit $?
else
  log_info "No command specified. Use this script to run commands on EC2."
  log_info "Example: $0 'ls -la /home/ec2-user'"
  exit 0
fi
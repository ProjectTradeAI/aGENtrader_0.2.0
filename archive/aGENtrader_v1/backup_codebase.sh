#!/bin/bash
# Backup Codebase Script
# This script creates a backup of the current codebase before cleaning up

# Set variables
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="./backups"
BACKUP_FILE="codebase_backup_${TIMESTAMP}.tar.gz"
EC2_BACKUP_FILE="ec2_codebase_backup_${TIMESTAMP}.tar.gz"
EC2_IP="51.20.250.135"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Function to create backup
create_backup() {
  echo "===== CREATING LOCAL BACKUP ====="
  
  # Create backup directory if it doesn't exist
  mkdir -p "$BACKUP_DIR"
  
  # Define files/directories to exclude
  EXCLUDE_PATTERNS=(
    "./node_modules"
    "./.git"
    "./backups"
    "./__pycache__"
    "./.venv"
    "./*.pyc"
    "./*.pyo"
    "./*.log"
  )
  
  # Build exclude arguments
  EXCLUDE_ARGS=""
  for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=$pattern"
  done
  
  # Create the backup
  echo "Creating backup archive at: $BACKUP_DIR/$BACKUP_FILE"
  tar $EXCLUDE_ARGS -czf "$BACKUP_DIR/$BACKUP_FILE" .
  
  # Check if backup was successful
  if [ $? -eq 0 ]; then
    echo "✅ Backup completed successfully"
    echo "Backup location: $BACKUP_DIR/$BACKUP_FILE"
    echo "Backup size: $(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)"
  else
    echo "❌ Backup failed"
    exit 1
  fi
}

# Function to create backup on EC2
create_ec2_backup() {
  echo -e "\n===== CREATING EC2 BACKUP ====="
  
  # Create EC2 key file if needed
  if [ ! -f "$KEY_PATH" ]; then
    echo "Creating EC2 key file..."
    cat > "$KEY_PATH" << 'KEYEOF'
-----BEGIN RSA PRIVATE KEY-----
MIIEoQIBAAKCAQEAyxNT6X+1frDllJPAbCAjOjNV6+IYbJTBJF+NNUESxrYsMK8J
1Dt4OBuXKSMV7nttmb6/jy6tItkztExoPyqr1QuKwHUInkbkKTm15Cl90o6yzXba
UfntOfpwZHwmEOJRVniLRJPzkOldOplyTiIxaf8mZKLeaXDlleaHZlNyrBWs9wNN
gJJbCBve2Z1TJsZeRig3u0Tg0+xo1BPxSm8dROalr8/30UrXpCkDQVL5S3oA2kSd
6hvwQhUZclGNheGgLOGTMtZ/FxGAI/mVsD29ErWnEoysLGCpbLfXpw7o3yEDCND+
cpqtV+ckbTeX2gqbugyZmBVrxcnbafwW1ykoaQIDAQABAoIBAE53gmXn1c5FNgBp
8uEUrefwLBQAAeX6uIKAdUSNh17Gx15sVATwkaxEZO0dRH0orhnJDaWaqIWdnY/e
Mi2uJEUmt49T6WeXBtQzG2g07Awu3UHs2cDxLEvJzCHXorHFcR5TZ6Sw8l0c/swE
vJkaNzO4xjH+iKf/WobIU6sjNVzuNjJF7TNUJ/kZmfZHOjOKCSBF/ahY+weeVBFp
lqaSKrNINPYoYn4nrAgWVxMiPqItWhm3Y9G3c3z9ePNJKRkNKnRB+pCfGS3EZTq0
deI3rcurPsBe34B/SxZF7G1hLVhEtom18YUbZvSBxgCJmI7D239e/Qz6bgqB7FAo
rFJ/S3ECgYEA+oCEP5NjBilqOHSdLLPhI/Ak6pNIK017xMBdiBTjnRh93D8Xzvfh
glkHRisZo8gmIZsgW3izlEeUv4CaVf7OzlOUiu2KmmrLxGHPoT+QPLf/Ak3GZE14
XY9vtaQQSwxM+i5sNtAD/3/KcjH6wT1B+8R4xqtHUYXw7VoEQWRSs/UCgYEAz4hW
j7+ooYlyHzkfuiEMJG0CtKR/fYsd9Zygn+Y6gGQvCiL+skAmx/ymG/qU6D8ZejkN
Azzv7JGQ+1z8OtTNStgDPE7IT74pA0BC60jHySDYzyGAaoMJDhHxA2CPm60EwPDU
5pRVy+FN5LmCCT8oDgcpsPpgjALOqR2TUkcOziUCgYAFXdN3eTTZ4PFBnF3xozjj
iDWCQP1+z/4izOw0Ch6GMwwfN8rOyEiwfi/FtQ6rj5Ihji03SHKwboglQiAMT5Um
nmvEPiqF/Fu5LU9BaRcx9c8kwX3KkE5P0s7V2VnwAad0hKIU2of7ZUV1BNUWZrWP
KzpbJzgz6uaqbw9AR2HuMQJ/YuaWWer8cf8OY9LVS95z6ugIYg4Cs9GYdXQvGASf
3I/h2vLSbiAkWyoL/0lrrUJk4dpOWTyxGgxFC4VErsS7EO/gmtzwmRAGe4YkXfxR
OYhtykgs6pWHuyzRrspVpdrOaSRcUYZfXMoCVP4S+lUewZCoTa8EU7UCx5VQn+U9
KQKBgQDsjVRcsfC/szL7KgeheEN/2zRADix5bqrg0rAB1y+sw+yzkCCh3jcRn2O2
wNIMroggGNy+vcR8Xo/V1wLCsEn45cxB6W7onqxFRM6IkGxkBgdatEL/aBnETSAI
x4C5J+IqaT2T53O2n3DR+GsVoeNUbz8j/lPONNQnV0ZqHRVWpA==
-----END RSA PRIVATE KEY-----
KEYEOF
    chmod 600 "$KEY_PATH"
  fi
  
  # Test EC2 connection
  echo "Testing EC2 connection..."
  if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'" > /dev/null 2>&1; then
    echo "❌ Failed to connect to EC2. Skipping EC2 backup."
    return 1
  fi
  echo "✅ EC2 connection successful"
  
  # Create backup on EC2
  echo "Creating backup on EC2..."
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && mkdir -p backups && tar --exclude='./backups' --exclude='./node_modules' --exclude='./__pycache__' -czf backups/$EC2_BACKUP_FILE ."
  
  # Check if EC2 backup was successful
  if [ $? -eq 0 ]; then
    echo "✅ EC2 backup completed successfully"
    # Get backup size
    EC2_BACKUP_SIZE=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "du -h $EC2_DIR/backups/$EC2_BACKUP_FILE | cut -f1")
    echo "EC2 backup location: $EC2_DIR/backups/$EC2_BACKUP_FILE"
    echo "EC2 backup size: $EC2_BACKUP_SIZE"
    return 0
  else
    echo "❌ EC2 backup failed"
    return 1
  fi
}

# Main function
main() {
  echo "========================================"
  echo "CODEBASE BACKUP SCRIPT"
  echo "========================================"
  echo "This script will create backups of the codebase"
  echo "both locally and on the EC2 instance."
  echo "========================================"
  
  # Create local backup
  create_backup
  
  # Create EC2 backup
  create_ec2_backup
  
  echo -e "\n========================================"
  echo "BACKUP SUMMARY"
  echo "========================================"
  echo "Local backup: $BACKUP_DIR/$BACKUP_FILE"
  echo "EC2 backup: $EC2_DIR/backups/$EC2_BACKUP_FILE"
  echo "========================================\n"
  
  echo "It is now safe to proceed with the cleanup process."
}

# Run the main function
main
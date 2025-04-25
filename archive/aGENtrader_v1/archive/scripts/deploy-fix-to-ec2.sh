#!/bin/bash
# Simple script to deploy fix script to EC2 using alternate methods

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Log function
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
  echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Ensure EC2 public IP is set
if [ -z "$EC2_PUBLIC_IP" ]; then
  log_error "EC2_PUBLIC_IP environment variable is not set."
  log "Please set it by running: export EC2_PUBLIC_IP=<your-ec2-ip>"
  exit 1
fi

# Check for SSH key
SSH_KEY="ec2_ssh_key.pem"
if [ ! -f "$SSH_KEY" ]; then
  log_error "SSH key file not found: $SSH_KEY"
  exit 1
fi

# Set proper permissions for SSH key
chmod 400 "$SSH_KEY"

# Create a package with all necessary files
log "Creating deployment package..."
tar -czf autogen-fix.tar.gz fix_autogen_group_chat.py AUTOGEN_EC2_FIX_INSTRUCTIONS.md

# Try to upload using SCP
log "Attempting to transfer to EC2 using SCP..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 autogen-fix.tar.gz ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/

# Check if SCP was successful
if [ $? -eq 0 ]; then
  log "Successfully transferred files to EC2."
  
  # Extract and run the fix
  log "Connecting to EC2 to extract and run the fix..."
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "
    cd /home/ec2-user && 
    tar -xzf autogen-fix.tar.gz && 
    mv fix_autogen_group_chat.py aGENtrader/ && 
    mv AUTOGEN_EC2_FIX_INSTRUCTIONS.md aGENtrader/ && 
    cd aGENtrader && 
    python3 fix_autogen_group_chat.py --all && 
    echo 'Fix applied successfully!'
  "
  
  if [ $? -eq 0 ]; then
    log "Fix has been applied successfully on EC2!"
  else
    log_error "Failed to apply the fix on EC2."
  fi
else
  log_error "Failed to transfer files to EC2 using SCP."
  log_warning "EC2 instance may be unreachable or there might be connectivity issues."
  log "You can manually apply the fix by following the instructions in AUTOGEN_EC2_FIX_INSTRUCTIONS.md"
fi

# Create a simple README file with manual instructions
log "Creating additional manual instructions file..."
cat > MANUAL_EC2_FIX.txt << EOF
# Manual EC2 Fix Instructions

If the automated script failed to connect to EC2, you can manually apply the fix:

1. SSH into your EC2 instance:
   ssh -i ec2_ssh_key.pem ec2-user@$EC2_PUBLIC_IP

2. Open the file that needs fixing (collaborative_trading_framework.py):
   cd /home/ec2-user/aGENtrader
   nano agents/collaborative_trading_framework.py

3. Look for this code:
   manager = GroupChatManager(
       groupchat=self.group_chat,
       llm_config=self.llm_config,
       is_termination_msg=lambda msg: "TRADING SESSION COMPLETE" in msg.get("content", "")
   )

4. Update it to:
   manager = GroupChatManager(
       groupchat=self.group_chat,
       llm_config=self.llm_config,
       is_termination_msg=lambda msg: "TRADING SESSION COMPLETE" in msg.get("content", ""),
       select_speaker_auto_llm_config=self.llm_config  # Add this line
   )

5. Save the file (Ctrl+O, Enter, Ctrl+X in nano)

6. Test the fix:
   python3 test_structured_decision_making.py --test_type extractor

For more detailed instructions, see AUTOGEN_EC2_FIX_INSTRUCTIONS.md
EOF

log "Manual instructions written to MANUAL_EC2_FIX.txt"
log "Deployment process completed."
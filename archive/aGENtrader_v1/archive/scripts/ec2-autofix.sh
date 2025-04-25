#!/bin/bash
# EC2 AutoFix Script - Comprehensive AutoGen GroupChatManager Fix

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

# Print banner
echo -e "
${GREEN}╔══════════════════════════════════════════════════════════╗
║   EC2 AutoGen GroupChatManager Comprehensive Fix Tool      ║
╚══════════════════════════════════════════════════════════╝${NC}
"

# Check for EC2 IP
if [ -z "$EC2_PUBLIC_IP" ]; then
  log_warning "EC2_PUBLIC_IP environment variable is not set."
  read -p "Enter EC2 Public IP: " EC2_PUBLIC_IP
  if [ -z "$EC2_PUBLIC_IP" ]; then
    log_error "No EC2 IP provided. Exiting."
    exit 1
  fi
fi

# Check for SSH key
SSH_KEY="ec2_ssh_key.pem"
if [ ! -f "$SSH_KEY" ]; then
  log_error "SSH key file '$SSH_KEY' not found. Please ensure it exists in the current directory."
  exit 1
fi

# Set proper permissions on SSH key
chmod 400 "$SSH_KEY"

# Print current status
log "EC2 Target IP: $EC2_PUBLIC_IP"
log "SSH Key: $SSH_KEY"
log "Starting comprehensive AutoGen fix..."

# Function to run a simple SSH test command to verify connectivity
test_ssh_connection() {
  log "Testing SSH connection to EC2..."
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes ec2-user@$EC2_PUBLIC_IP "echo 'Connection successful'"
  return $?
}

# Function to copy files to EC2
copy_fix_to_ec2() {
  log "Preparing to copy files to EC2..."
  
  # Create a package with all necessary files
  tar -czf autogen-fix-package.tar.gz fix_ec2_autogen_group_chat.py fix_autogen_group_chat.py AUTOGEN_EC2_FIX_INSTRUCTIONS.md
  
  log "Transferring fix package to EC2..."
  scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 autogen-fix-package.tar.gz ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/
  
  if [ $? -eq 0 ]; then
    log "Successfully transferred files to EC2."
    return 0
  else
    log_error "Failed to transfer files to EC2."
    return 1
  fi
}

# Function to execute fix on EC2
execute_fix_on_ec2() {
  log "Executing fix on EC2..."
  
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "
    cd /home/ec2-user && 
    tar -xzf autogen-fix-package.tar.gz && 
    cp fix_ec2_autogen_group_chat.py aGENtrader/ || cp fix_autogen_group_chat.py aGENtrader/ && 
    cp AUTOGEN_EC2_FIX_INSTRUCTIONS.md aGENtrader/ && 
    cd aGENtrader && 
    python3 fix_ec2_autogen_group_chat.py --all || python3 fix_autogen_group_chat.py --all || echo 'Error: Could not run any fix script'
  "
  
  return $?
}

# Function to run test on EC2
test_fix_on_ec2() {
  log "Testing fix on EC2..."
  
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "
    cd /home/ec2-user/aGENtrader && 
    python3 test_structured_decision_making.py --test_type extractor
  "
  
  return $?
}

# Function for inline fix via SSH if file transfer fails
execute_inline_fix_on_ec2() {
  log "Attempting inline fix via SSH..."
  
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "
    cd /home/ec2-user/aGENtrader && 
    
    # Create inline fix script
    cat > inline_fix.py << 'EOF'
#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
import sys

def fix_file(file_path):
    print(f\"Checking {file_path}...\")
    if not os.path.exists(file_path):
        print(f\"File not found: {file_path}\")
        return False
        
    # Create backup
    backup_path = f\"{file_path}.bak\"
    shutil.copyfile(file_path, backup_path)
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Skip if already fixed
    if 'select_speaker_auto_llm_config' in content:
        print(f\"File already fixed: {file_path}\")
        return False
    
    # Look for GroupChatManager initializations
    pattern = r'(manager\s*=\s*GroupChatManager\s*\(.*?\))'
    
    match = re.search(pattern, content, re.DOTALL)
    if match:
        match_text = match.group(1)
        if match_text.strip().endswith(')'):
            # Add the new parameter before the closing parenthesis
            last_paren = match_text.rstrip().rfind(')')
            fixed_text = match_text[:last_paren] + ',\n        select_speaker_auto_llm_config=self.llm_config  # Added to fix speaker selection error\n    )' + match_text[last_paren+1:]
            new_content = content.replace(match_text, fixed_text)
            
            # Write the updated content
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            print(f\"Fixed: {file_path}\")
            return True
    
    print(f\"No match found or couldn't fix: {file_path}\")
    return False

def find_and_fix_files():
    # Main file to fix
    main_file = 'agents/collaborative_trading_framework.py'
    fixed_files = []
    
    if os.path.exists(main_file):
        if fix_file(main_file):
            fixed_files.append(main_file)
    else:
        print(f\"Main file not found: {main_file}\")
    
    # Check for other files that might use GroupChatManager
    try:
        result = subprocess.run(['grep', '-l', 'GroupChatManager', '--include=*.py', '-r', '.'], capture_output=True, text=True)
        files = result.stdout.splitlines()
        for file in files:
            if file != main_file:  # Skip the main file that we already tried to fix
                if fix_file(file):
                    fixed_files.append(file)
    except Exception as e:
        print(f\"Error searching for additional files: {e}\")
    
    return fixed_files

if __name__ == \"__main__\":
    print(\"Starting inline AutoGen GroupChatManager fix\")
    fixed_files = find_and_fix_files()
    print(f\"Fixed {len(fixed_files)} files: {fixed_files}\")
    print(\"Fix completed!\")
    sys.exit(0 if fixed_files else 1)
EOF
    
    # Make executable and run
    chmod +x inline_fix.py
    python3 inline_fix.py
    
    # Clean up
    rm inline_fix.py
  "
  
  return $?
}

# Main execution flow
if test_ssh_connection; then
  log "SSH connection successful."
  
  if copy_fix_to_ec2; then
    if execute_fix_on_ec2; then
      log "Fix scripts executed successfully."
      
      if test_fix_on_ec2; then
        log "Test completed successfully! Fix appears to be working properly."
        exit 0
      else
        log_warning "Test encountered issues. Fix may not be complete."
        # Fall back to inline fix
        execute_inline_fix_on_ec2
        test_fix_on_ec2
      fi
    else
      log_warning "Fix script execution failed. Trying inline fix..."
      execute_inline_fix_on_ec2
      test_fix_on_ec2
    fi
  else
    log_warning "Failed to copy files to EC2. Trying inline fix..."
    execute_inline_fix_on_ec2
    test_fix_on_ec2
  fi
else
  log_error "Cannot establish SSH connection to EC2. Please check connectivity."
  log "Please consider following the manual instructions in MANUAL_EC2_FIX.txt"
  exit 1
fi

log "EC2 AutoFix process completed."
log "If you still encounter issues, please follow the manual instructions in MANUAL_EC2_FIX.txt"
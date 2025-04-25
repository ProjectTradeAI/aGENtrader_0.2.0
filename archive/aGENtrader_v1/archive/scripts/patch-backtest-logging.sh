#!/bin/bash
# Script to patch an existing backtest script for better agent communications visibility

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Setup SSH key
KEY_PATH="/tmp/patch_backtest_key.pem"
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
PROJECT_DIR="/home/ec2-user/aGENtrader"

echo -e "${BLUE}Setting up SSH key...${NC}"
echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Function to run SSH commands
run_cmd() {
  local cmd="$1"
  local silent="${2:-false}"
  
  if [ "$silent" = "false" ]; then
    echo -e "${BLUE}Running command:${NC} $cmd"
    echo -e "${BLUE}---------------------------------------------------${NC}"
  fi
  
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "$cmd"
  local result=$?
  
  if [ "$silent" = "false" ]; then
    echo -e "${BLUE}---------------------------------------------------${NC}"
    if [ $result -eq 0 ]; then
      echo -e "${GREEN}✓ Command completed successfully${NC}"
    else
      echo -e "${RED}✗ Command failed with code $result${NC}"
    fi
  fi
  
  return $result
}

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  BACKTEST LOGGING ENHANCEMENT PATCH   ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check for available backtest scripts
echo -e "${BLUE}Checking for available backtest scripts...${NC}"
run_cmd "find $PROJECT_DIR -maxdepth 1 -name '*backtest*.py' | sort"

# Ask which script to patch
echo
echo -e "${YELLOW}Which script would you like to patch? (Default: run_enhanced_backtest.py)${NC}"
read -p "Enter script name: " script_name
script_name=${script_name:-run_enhanced_backtest.py}

# First, check if the script exists
script_exists=$(run_cmd "test -f $PROJECT_DIR/$script_name && echo 'yes' || echo 'no'" true)
if [ "$script_exists" != "yes" ]; then
  echo -e "${RED}Error: Script $script_name not found${NC}"
  exit 1
fi

# Create a backup of the script
echo -e "${BLUE}Creating backup of $script_name...${NC}"
run_cmd "cp $PROJECT_DIR/$script_name $PROJECT_DIR/${script_name}.bak"

# Now patch the script to enhance logging
echo -e "${BLUE}Patching $script_name to enhance agent communications logging...${NC}"

# Create a temporary patch file
cat > /tmp/backtest_logging_patch.py << 'PYTHONPATCH'
#!/usr/bin/env python3
"""
Enhanced logging patch for backtest scripts
"""
import os
import sys
import json
import logging
from datetime import datetime

# Configure enhanced logging
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_dir = os.path.join('data', 'logs')
os.makedirs(log_dir, exist_ok=True)

# Create a special logger for agent communications
agent_log_file = os.path.join(log_dir, f'agent_communications_{timestamp}.log')
agent_handler = logging.FileHandler(agent_log_file)
agent_handler.setLevel(logging.INFO)
agent_handler.setFormatter(logging.Formatter('%(asctime)s - AGENT - %(message)s'))

# Get the root logger and add our handler
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(agent_handler)

# Create a dedicated logger for agent communications
agent_logger = logging.getLogger('agent_comms')
agent_logger.setLevel(logging.INFO)
agent_logger.addHandler(agent_handler)

# Log the start of the patched run
agent_logger.info('=== BACKTEST WITH ENHANCED AGENT LOGGING STARTED ===')
agent_logger.info(f'Agent communications will be logged to: {agent_log_file}')

# Original imports and code would be here...

# Function to log agent communications
def log_agent_communication(agent_name, message):
    """Log agent communications to the dedicated log file"""
    agent_logger.info(f'{agent_name}: {message}')

# Monkey patch key classes to add logging
try:
    # Try to import and patch agent classes
    sys.path.append('.')
    
    # Attempt to import and monkey patch the collaborative agent class
    try:
        from agents.collaborative_decision_agent import CollaborativeDecisionFramework
        
        # Store the original method
        if hasattr(CollaborativeDecisionFramework, 'run_decision_session'):
            original_run_decision = CollaborativeDecisionFramework.run_decision_session
            
            # Create a patched version with logging
            def patched_run_decision(self, symbol, prompt=None):
                agent_logger.info(f'=== STARTING COLLABORATIVE DECISION SESSION FOR {symbol} ===')
                result = original_run_decision(self, symbol, prompt)
                agent_logger.info(f'=== COMPLETED COLLABORATIVE DECISION SESSION ===')
                if isinstance(result, dict):
                    decision = result.get('decision', 'Unknown')
                    confidence = result.get('confidence', 'Unknown')
                    agent_logger.info(f'Decision: {decision}, Confidence: {confidence}')
                return result
            
            # Replace the original method with our patched version
            CollaborativeDecisionFramework.run_decision_session = patched_run_decision
            agent_logger.info('Successfully patched CollaborativeDecisionFramework.run_decision_session')
    except (ImportError, AttributeError) as e:
        agent_logger.warning(f'Could not patch CollaborativeDecisionFramework: {e}')
    
    # Attempt to import and monkey patch the decision session class
    try:
        from orchestration.decision_session import DecisionSession
        
        # Store the original method
        if hasattr(DecisionSession, 'initiate_chat'):
            original_initiate_chat = DecisionSession.initiate_chat
            
            # Create a patched version with logging
            def patched_initiate_chat(self, *args, **kwargs):
                agent_logger.info('=== INITIATING GROUP CHAT ===')
                result = original_initiate_chat(self, *args, **kwargs)
                agent_logger.info('=== GROUP CHAT INITIATED ===')
                return result
            
            # Replace the original method with our patched version
            DecisionSession.initiate_chat = patched_initiate_chat
            agent_logger.info('Successfully patched DecisionSession.initiate_chat')
    except (ImportError, AttributeError) as e:
        agent_logger.warning(f'Could not patch DecisionSession: {e}')
        
    # Also try to patch any group chat or autogen components
    try:
        from orchestration.autogen_manager import AutoGenManager
        agent_logger.info('Successfully imported AutoGenManager')
        
        # Try to find and patch relevant methods
        for attr_name in dir(AutoGenManager):
            if attr_name.startswith('__'):
                continue
            if 'chat' in attr_name.lower() or 'agent' in attr_name.lower() or 'group' in attr_name.lower():
                try:
                    original_method = getattr(AutoGenManager, attr_name)
                    if callable(original_method):
                        agent_logger.info(f'Found potential method to patch: {attr_name}')
                except:
                    pass
    except ImportError as e:
        agent_logger.warning(f'Could not import AutoGenManager: {e}')
    
except Exception as e:
    agent_logger.error(f'Error patching classes: {e}')

# At the end of any backtest run, log completion
import atexit
def log_completion():
    agent_logger.info('=== BACKTEST WITH ENHANCED AGENT LOGGING COMPLETED ===')
    print(f'\nAgent communications have been logged to: {agent_log_file}')
atexit.register(log_completion)

print(f'Enhanced agent logging patch applied, communications will be logged to: {agent_log_file}')
PYTHONPATCH

# Upload the patch file to EC2
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no /tmp/backtest_logging_patch.py "$SSH_USER@$EC2_IP:$PROJECT_DIR/backtest_logging_patch.py"

# Now modify the backtest script to use our patch
run_cmd "cat > $PROJECT_DIR/run_patched_backtest.py << EOF
#!/usr/bin/env python3
\"\"\"
Patched backtest script with enhanced agent communications logging
\"\"\"
# First import our logging patch
import backtest_logging_patch

# Then import the original script
with open('$script_name', 'r') as f:
    exec(f.read())
EOF"

# Make the patched script executable
run_cmd "chmod +x $PROJECT_DIR/run_patched_backtest.py"

# Create a shell script wrapper on EC2 to run the patched backtest
run_cmd "cat > $PROJECT_DIR/run_patched_backtest.sh << 'SHELLSCRIPT'
#!/bin/bash
# Run a backtest with enhanced agent communications logging

# Default parameters
SYMBOL='BTCUSDT'
INTERVAL='1h'
START_DATE='2025-03-01'
END_DATE='2025-03-02'
INITIAL_BALANCE=10000
RISK_PER_TRADE=0.02
USE_LOCAL_LLM=true

# Parse command line arguments
while [[ \$# -gt 0 ]]; do
    case \$1 in
        --symbol) SYMBOL=\"\$2\"; shift ;;
        --interval) INTERVAL=\"\$2\"; shift ;;
        --start_date) START_DATE=\"\$2\"; shift ;;
        --end_date) END_DATE=\"\$2\"; shift ;;
        --initial_balance) INITIAL_BALANCE=\"\$2\"; shift ;;
        --risk_per_trade) RISK_PER_TRADE=\"\$2\"; shift ;;
        --use_local_llm) USE_LOCAL_LLM=true ;;
        --use_openai) USE_LOCAL_LLM=false ;;
        *) echo \"Unknown parameter: \$1\"; exit 1 ;;
    esac
    shift
done

# Construct the command based on the script
SCRIPT_NAME=\"run_patched_backtest.py\"

# Build the parameter string based on the original script
PARAMS=\"--symbol \$SYMBOL --interval \$INTERVAL --start_date \$START_DATE --end_date \$END_DATE\"

# Add other parameters
PARAMS=\"\$PARAMS --initial_balance \$INITIAL_BALANCE --risk_per_trade \$RISK_PER_TRADE\"

# Add local LLM option if enabled
if [ \"\$USE_LOCAL_LLM\" = true ]; then
    PARAMS=\"\$PARAMS --use_local_llm\"
fi

# Print the command
echo \"Running: python3 \$SCRIPT_NAME \$PARAMS\"
echo \"=====================================================\"

# Run the command
PYTHONPATH=. python3 \$SCRIPT_NAME \$PARAMS

# Get the latest agent communications log
LATEST_LOG=\$(find data/logs -name 'agent_communications_*.log' | sort -r | head -n 1)

if [ -n \"\$LATEST_LOG\" ]; then
    echo \"=====================================================\"
    echo \"Agent communications log: \$LATEST_LOG\"
    echo \"Log content:\"
    echo \"=====================================================\"
    cat \"\$LATEST_LOG\"
fi
SHELLSCRIPT"

# Make the script executable
run_cmd "chmod +x $PROJECT_DIR/run_patched_backtest.sh"

echo
echo -e "${GREEN}Successfully created patched backtest script${NC}"
echo
echo -e "${YELLOW}To run the patched backtest on EC2, you can use:${NC}"
echo -e "${BLUE}./ec2-backtest.sh run \"cd $PROJECT_DIR && ./run_patched_backtest.sh\"${NC}"

# Create a helper script locally to run the patched backtest
cat > run-patched-backtest.sh << EOF
#!/bin/bash
# Run a patched backtest with enhanced agent communications logging

# Setup
KEY_PATH="/tmp/run_patched_key.pem"
echo "Setting up SSH key..."
echo "-----BEGIN RSA PRIVATE KEY-----" > "\$KEY_PATH"
echo "\$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "\$KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "\$KEY_PATH"
chmod 600 "\$KEY_PATH"

echo "Running patched backtest with enhanced agent communications logging..."
echo "This will run a short backtest (1 day) to minimize execution time."

ssh -i "\$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@\$EC2_PUBLIC_IP "cd $PROJECT_DIR && ./run_patched_backtest.sh --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-02 --use_local_llm"

#!/bin/bash
# Script to verify the multi-agent framework functionality in the codebase

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Setup SSH key
KEY_PATH="/tmp/check_framework_key.pem"
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
echo -e "${YELLOW}  MULTI-AGENT FRAMEWORK VERIFICATION   ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check for the agent classes
echo -e "${BLUE}Checking for agent classes in the codebase...${NC}"
run_cmd "find $PROJECT_DIR/agents -name '*.py' | grep -i 'collab\|multi\|structured\|trading\|decision' | sort"

# Examine the collaborative agent implementation
echo
echo -e "${BLUE}Examining collaborative agent implementation...${NC}"
collab_agent=$(run_cmd "find $PROJECT_DIR/agents -name '*collab*.py' | head -n 1" true)

if [ -n "$collab_agent" ]; then
  echo -e "${GREEN}Found collaborative agent: $collab_agent${NC}"
  
  # Check the class definition
  echo -e "${BLUE}Checking the class definition...${NC}"
  run_cmd "grep -A 10 'class Collaborative' $collab_agent"
  
  # Check for multi-agent interaction methods
  echo -e "${BLUE}Checking for multi-agent interaction methods...${NC}"
  run_cmd "grep -A 5 -B 2 'def .*session\|def .*interact\|def .*communicate\|def .*collaborate' $collab_agent"
fi

# Check for orchestration code
echo
echo -e "${BLUE}Checking for orchestration code...${NC}"
run_cmd "find $PROJECT_DIR/orchestration -name '*.py' | grep -i 'decision\|session\|autogen\|manager' | sort"

# Examine the decision session implementation
echo
echo -e "${BLUE}Examining decision session implementation...${NC}"
decision_session=$(run_cmd "find $PROJECT_DIR/orchestration -name '*decision*session*.py' | head -n 1" true)

if [ -n "$decision_session" ]; then
  echo -e "${GREEN}Found decision session: $decision_session${NC}"
  
  # Check the class definition
  echo -e "${BLUE}Checking the class definition...${NC}"
  run_cmd "grep -A 10 'class Decision' $decision_session"
  
  # Check for agent initialization
  echo -e "${BLUE}Checking for agent initialization...${NC}"
  run_cmd "grep -A 15 -B 5 'def init.*agent\|def create.*agent\|def setup.*agent' $decision_session"
  
  # Check for group chat setup
  echo -e "${BLUE}Checking for group chat setup...${NC}"
  run_cmd "grep -A 10 -B 5 'GroupChat\|group_chat\|initiate_chat' $decision_session"
fi

# Check for AutoGen integration
echo
echo -e "${BLUE}Checking for AutoGen integration...${NC}"
autogen_manager=$(run_cmd "find $PROJECT_DIR/orchestration -name '*autogen*.py' | head -n 1" true)

if [ -n "$autogen_manager" ]; then
  echo -e "${GREEN}Found AutoGen manager: $autogen_manager${NC}"
  
  # Check the imports
  echo -e "${BLUE}Checking imports...${NC}"
  run_cmd "grep -A 10 'import' $autogen_manager | grep -i 'autogen'"
  
  # Check for group chat creation
  echo -e "${BLUE}Checking for group chat creation...${NC}"
  run_cmd "grep -A 15 -B 5 'GroupChat\|group_chat\|create_group_chat' $autogen_manager"
  
  # Check for agent creation
  echo -e "${BLUE}Checking for agent creation...${NC}"
  run_cmd "grep -A 10 -B 2 'UserProxyAgent\|AssistantAgent\|create_agent' $autogen_manager"
  
  # Check for speaker selection fix
  echo -e "${BLUE}Checking for speaker selection fix...${NC}"
  run_cmd "grep -A 2 -B 2 'select_speaker\|auto_select\|speaker_selection' $autogen_manager"
fi

# Check for actual multi-agent backtest calls
echo
echo -e "${BLUE}Checking backtest scripts for multi-agent calls...${NC}"
run_cmd "find $PROJECT_DIR -maxdepth 1 -name '*backtest*.py' | sort"

echo
echo -e "${BLUE}Checking how backtests initialize agents...${NC}"
backtest_script=$(run_cmd "find $PROJECT_DIR -maxdepth 1 -name '*enhanced*backtest*.py' | head -n 1" true)

if [ -n "$backtest_script" ]; then
  echo -e "${GREEN}Found backtest script: $backtest_script${NC}"
  
  # Check for agent initialization
  echo -e "${BLUE}Checking for agent initialization in backtest...${NC}"
  run_cmd "grep -n -A 10 -B 5 'agent\|session\|collaborative\|decision' $backtest_script | head -n 30"
fi

# Summary of findings
echo
echo -e "${YELLOW}Summary of Multi-Agent Framework Verification:${NC}"

# Check if key files exist
has_collab_agent=$(run_cmd "find $PROJECT_DIR/agents -name '*collab*.py' | wc -l" true)
has_decision_session=$(run_cmd "find $PROJECT_DIR/orchestration -name '*decision*session*.py' | wc -l" true)
has_autogen_manager=$(run_cmd "find $PROJECT_DIR/orchestration -name '*autogen*.py' | wc -l" true)
has_groupchat=$(run_cmd "grep -r 'GroupChat' $PROJECT_DIR | wc -l" true)
has_speaker_selection_fix=$(run_cmd "grep -r 'select_speaker_auto_llm_config' $PROJECT_DIR | wc -l" true)

if [ "$has_collab_agent" -gt 0 ]; then
  echo -e "${GREEN}✓ Found collaborative agent implementation${NC}"
else
  echo -e "${RED}✗ No collaborative agent implementation found${NC}"
fi

if [ "$has_decision_session" -gt 0 ]; then
  echo -e "${GREEN}✓ Found decision session implementation${NC}"
else
  echo -e "${RED}✗ No decision session implementation found${NC}"
fi

if [ "$has_autogen_manager" -gt 0 ]; then
  echo -e "${GREEN}✓ Found AutoGen manager implementation${NC}"
else
  echo -e "${RED}✗ No AutoGen manager implementation found${NC}"
fi

if [ "$has_groupchat" -gt 0 ]; then
  echo -e "${GREEN}✓ Found GroupChat implementation (${has_groupchat} references)${NC}"
else
  echo -e "${RED}✗ No GroupChat implementation found${NC}"
fi

if [ "$has_speaker_selection_fix" -gt 0 ]; then
  echo -e "${GREEN}✓ Found speaker selection fix (${has_speaker_selection_fix} references)${NC}"
else
  echo -e "${RED}✗ No speaker selection fix found${NC}"
fi

# Overall assessment
echo
echo -e "${YELLOW}Overall Assessment:${NC}"
if [ "$has_collab_agent" -gt 0 ] && [ "$has_decision_session" -gt 0 ] && [ "$has_autogen_manager" -gt 0 ] && [ "$has_groupchat" -gt 0 ]; then
  echo -e "${GREEN}✓ The multi-agent framework appears to be fully implemented${NC}"
  
  if [ "$has_speaker_selection_fix" -gt 0 ]; then
    echo -e "${GREEN}✓ The speaker selection fix is in place${NC}"
  else
    echo -e "${YELLOW}⚠ The speaker selection fix may be missing, which could affect agent communications${NC}"
  fi
  
  echo
  echo -e "${YELLOW}Next Steps:${NC}"
  echo -e "1. The framework code exists, but the logging might be insufficient to show agent communications."
  echo -e "2. Try running a backtest with enhanced logging to see agent interactions."
  echo -e "3. Consider adding more verbose logging to the agent communication methods."
else
  echo -e "${RED}✗ The multi-agent framework may be partially implemented or not properly integrated${NC}"
  
  echo
  echo -e "${YELLOW}Next Steps:${NC}"
  echo -e "1. Check if there are separate implementations not discovered by this script."
  echo -e "2. Ensure that the backtest scripts are actually using the multi-agent framework."
  echo -e "3. Add proper logging to make agent communications visible during backtests."
fi

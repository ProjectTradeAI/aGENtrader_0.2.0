#!/bin/bash
# Script to verify multi-agent functionality

# Configuration
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
KEY_PATH="/tmp/ec2_verify_key.pem"
PROJECT_DIR="/home/ec2-user/aGENtrader"

# Color output
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Setup SSH key
setup_key() {
  echo -e "${BLUE}Setting up SSH key...${NC}"
  # Create properly formatted key file
  echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
  echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
  echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
  chmod 600 "$KEY_PATH"
}

# Run SSH command
run_ssh_cmd() {
  local cmd="$1"
  local silent="${2:-false}"
  
  if [ "$silent" = "false" ]; then
    echo -e "${BLUE}Running command on EC2:${NC} $cmd"
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

# Check if the multi-agent framework is properly set up
check_multi_agent_setup() {
  echo -e "${BLUE}Checking multi-agent framework setup...${NC}"
  
  # Check for agent modules
  run_ssh_cmd "test -d $PROJECT_DIR/agents" true
  if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Agent directory not found${NC}"
    return 1
  fi
  
  # Check for key agent files
  run_ssh_cmd "ls -la $PROJECT_DIR/agents/ | grep -E '(collaborative|structured|trading)'"
  
  # Check for orchestration files
  run_ssh_cmd "test -d $PROJECT_DIR/orchestration" true
  if [ $? -eq 0 ]; then
    run_ssh_cmd "ls -la $PROJECT_DIR/orchestration/ | grep -E '(decision|session|autogen)'"
  fi
  
  # Check for group chat configuration fixes
  echo -e "${BLUE}Checking for group chat configuration fixes...${NC}"
  run_ssh_cmd "grep -r 'select_speaker_auto_llm_config' $PROJECT_DIR/orchestration/ | head -n 5"
  
  return 0
}

# Check the content of a recent log file for agent communications
check_agent_communications() {
  echo -e "${BLUE}Analyzing recent log files for agent communications...${NC}"
  
  # Find recent log files
  local logs=$(run_ssh_cmd "find $PROJECT_DIR/data/logs -type f -name '*backtest*.log' -o -name '*agent*.log' | sort -r | head -n 3" true)
  
  if [ -z "$logs" ]; then
    echo -e "${RED}No recent log files found${NC}"
    return 1
  fi
  
  # Check the first log file for agent communications
  local first_log=$(echo "$logs" | head -n 1)
  echo -e "${BLUE}Analyzing log: $first_log${NC}"
  
  # Search for agent communication patterns
  run_ssh_cmd "grep -A 3 -B 3 'Agent:' $PROJECT_DIR/$first_log 2>/dev/null || grep -A 3 -B 3 'AGENT' $PROJECT_DIR/$first_log 2>/dev/null || grep -A 3 -B 3 'agent' $PROJECT_DIR/$first_log 2>/dev/null || echo 'No agent communications found'"
  
  # Search for group chat or conversation patterns
  run_ssh_cmd "grep -A 3 -B 3 'GroupChat' $PROJECT_DIR/$first_log 2>/dev/null || grep -A 3 -B 3 'Conversation' $PROJECT_DIR/$first_log 2>/dev/null || grep -A 3 -B 3 'conversation' $PROJECT_DIR/$first_log 2>/dev/null || echo 'No group chat communications found'"
  
  return 0
}

# Check for the existence of expected result files
check_result_files() {
  echo -e "${BLUE}Checking for expected result files...${NC}"
  
  # Check results directory
  run_ssh_cmd "test -d $PROJECT_DIR/results" true
  if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Results directory not found${NC}"
    return 1
  fi
  
  # Check recent result files
  run_ssh_cmd "ls -la $PROJECT_DIR/results/ | tail -n 10"
  
  # Check if any results have the collaborative/multi-agent pattern
  run_ssh_cmd "find $PROJECT_DIR/results -name '*combined*' -o -name '*multi*' -o -name '*collab*' | sort"
  
  return 0
}

# Check the command-line options of the ec2-multi-agent-backtest.sh script
check_script_options() {
  echo -e "${BLUE}Checking command-line options of the backtest script...${NC}"
  
  # Check if the script exists
  run_ssh_cmd "test -f $PROJECT_DIR/ec2-multi-agent-backtest.sh" true
  if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Backtest script not found${NC}"
    return 1
  fi
  
  # Check the script's help output or options
  run_ssh_cmd "grep -A 20 'options' $PROJECT_DIR/ec2-multi-agent-backtest.sh || grep -A 20 'usage' $PROJECT_DIR/ec2-multi-agent-backtest.sh"
  
  return 0
}

# Run a very brief test with debug/verbose flags
run_debug_test() {
  echo -e "${BLUE}Running a brief test with debug flags...${NC}"
  
  # Find if the script supports any debug or verbose flags
  local debug_flags=$(run_ssh_cmd "grep -oE -- '--debug|--verbose|--trace|--log-level' $PROJECT_DIR/ec2-multi-agent-backtest.sh" true)
  
  local debug_cmd=""
  if [[ "$debug_flags" == *"--debug"* ]]; then
    debug_cmd="--debug"
  elif [[ "$debug_flags" == *"--verbose"* ]]; then
    debug_cmd="--verbose"
  elif [[ "$debug_flags" == *"--trace"* ]]; then
    debug_cmd="--trace"
  elif [[ "$debug_flags" == *"--log-level"* ]]; then
    debug_cmd="--log-level debug"
  fi
  
  # Run a very short backtest with any available debug flags
  if [ -n "$debug_cmd" ]; then
    echo -e "${BLUE}Running with debug flag: $debug_cmd${NC}"
    run_ssh_cmd "cd $PROJECT_DIR && ./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-02 --position_size 50 --local-llm $debug_cmd > /tmp/debug_test.log 2>&1"
    
    # Check the debug output
    run_ssh_cmd "tail -n 50 /tmp/debug_test.log"
  else
    echo -e "${YELLOW}No debug flags found in the script${NC}"
    echo -e "${BLUE}Let's examine the script itself...${NC}"
    
    # Check the beginning of the script for clues
    run_ssh_cmd "head -n 50 $PROJECT_DIR/ec2-multi-agent-backtest.sh"
  fi
  
  return 0
}

# Find all Python files related to the agent framework
find_agent_framework_files() {
  echo -e "${BLUE}Finding agent framework files...${NC}"
  
  # Find Python files in agents directory
  run_ssh_cmd "find $PROJECT_DIR/agents -name '*.py' | sort"
  
  # Find Python files in orchestration directory
  run_ssh_cmd "test -d $PROJECT_DIR/orchestration && find $PROJECT_DIR/orchestration -name '*.py' | sort"
  
  # Look for main entry points
  echo -e "${BLUE}Looking for main backtest entry points...${NC}"
  run_ssh_cmd "find $PROJECT_DIR -maxdepth 1 -name '*backtest*.py' | sort"
  
  return 0
}

# Main function
main() {
  echo -e "${YELLOW}=============================================${NC}"
  echo -e "${YELLOW}  MULTI-AGENT FRAMEWORK VERIFICATION TOOL   ${NC}"
  echo -e "${YELLOW}=============================================${NC}"
  
  # Setup SSH key
  setup_key || { echo -e "${RED}Failed to setup SSH key. Exiting.${NC}"; exit 1; }
  
  # Run verification steps
  check_multi_agent_setup
  check_agent_communications
  check_result_files
  check_script_options
  run_debug_test
  find_agent_framework_files
  
  echo -e "${YELLOW}=============================================${NC}"
  echo -e "${YELLOW}            VERIFICATION COMPLETE            ${NC}"
  echo -e "${YELLOW}=============================================${NC}"
}

# Execute main function
main

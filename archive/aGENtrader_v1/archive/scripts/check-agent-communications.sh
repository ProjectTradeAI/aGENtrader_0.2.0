#!/bin/bash
# Script to check for agent communications in existing log files

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Setup SSH key
KEY_PATH="/tmp/check_agent_key.pem"
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
echo -e "${YELLOW}  AGENT COMMUNICATIONS CHECKER TOOL   ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check available logs
echo -e "${BLUE}Checking available log files...${NC}"
run_cmd "find $PROJECT_DIR/data/logs -type f -name '*.log' | sort -r | head -n 10"

# Check the most recent log file for agent communications
echo
echo -e "${BLUE}Analyzing most recent log file for agent communications...${NC}"
recent_log=$(run_cmd "find $PROJECT_DIR/data/logs -type f -name '*.log' | sort -r | head -n 1" true)
recent_log=$(echo "$recent_log" | head -n 1)

if [ -n "$recent_log" ]; then
  echo -e "${GREEN}Most recent log: $recent_log${NC}"
  
  # Look for various agent-related patterns
  echo -e "${BLUE}Searching for agent-related patterns...${NC}"
  
  # Pattern 1: Direct agent mentions
  echo -e "${YELLOW}Pattern 1: Direct agent mentions${NC}"
  run_cmd "grep -i 'agent' $recent_log | head -n 10"
  
  # Pattern 2: Group chat mentions
  echo -e "${YELLOW}Pattern 2: Group chat mentions${NC}"
  run_cmd "grep -i 'group\\|chat\\|session' $recent_log | head -n 10"
  
  # Pattern 3: Decision-related mentions
  echo -e "${YELLOW}Pattern 3: Decision-related mentions${NC}"
  run_cmd "grep -i 'decision\\|recommend\\|analysis' $recent_log | head -n 10"
  
  # Pattern 4: LLM-related mentions
  echo -e "${YELLOW}Pattern 4: LLM-related mentions${NC}"
  run_cmd "grep -i 'llm\\|model\\|mixtral\\|openai' $recent_log | head -n 10"
  
  # Check the last 50 lines of the log
  echo
  echo -e "${BLUE}Last 50 lines of the log:${NC}"
  run_cmd "tail -n 50 $recent_log"
else
  echo -e "${RED}No log files found${NC}"
fi

# Check available result files for agent communications
echo
echo -e "${BLUE}Checking result files for agent communications...${NC}"
run_cmd "find $PROJECT_DIR/results -type f -name '*.json' | sort -r | head -n 5"

latest_result=$(run_cmd "find $PROJECT_DIR/results -type f -name '*.json' | sort -r | head -n 1" true)
latest_result=$(echo "$latest_result" | head -n 1)

if [ -n "$latest_result" ]; then
  echo -e "${GREEN}Latest result file: $latest_result${NC}"
  
  # Check for agent communications in the result file
  echo -e "${BLUE}Searching for agent communications in the result file...${NC}"
  run_cmd "grep -i 'agent\\|decision\\|recommendation' $latest_result | head -n 10"
  
  # Download the result file and analyze it locally
  echo
  echo -e "${BLUE}Downloading result file for local analysis...${NC}"
  mkdir -p ec2_results
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$latest_result" "ec2_results/$(basename $latest_result)" >/dev/null 2>&1
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Downloaded to ec2_results/$(basename $latest_result)${NC}"
    
    # Check if file contains agent communications
    if grep -q -i "agent\|communication\|decision\|message" "ec2_results/$(basename $latest_result)"; then
      echo -e "${GREEN}✓ Result file contains agent-related data${NC}"
      
      # Extract and display agent communications if they exist
      echo -e "${BLUE}Agent-related data from result file:${NC}"
      grep -A 3 -B 3 -i "agent\|communication\|decision\|message" "ec2_results/$(basename $latest_result)" | head -n 20
    else
      echo -e "${RED}✗ No agent communications found in result file${NC}"
    fi
  else
    echo -e "${RED}✗ Failed to download result file${NC}"
  fi
else
  echo -e "${RED}No result files found${NC}"
fi

# Check specifically for the verbose backtest script result
verbose_result=$(run_cmd "find $PROJECT_DIR/results -type f -name 'verbose_backtest_*.json' | sort -r | head -n 1" true)
verbose_result=$(echo "$verbose_result" | head -n 1)

if [ -n "$verbose_result" ]; then
  echo
  echo -e "${BLUE}Found verbose backtest result: $verbose_result${NC}"
  
  # Download the verbose result file
  mkdir -p ec2_results
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$verbose_result" "ec2_results/$(basename $verbose_result)" >/dev/null 2>&1
  
  if [ $? -eq 0 ]; then
    # Display agent communications
    echo -e "${BLUE}Agent communications from verbose backtest:${NC}"
    jq -r '.agent_communications[] | "\(.agent): \(.message)"' "ec2_results/$(basename $verbose_result)" 2>/dev/null || 
      grep -A 2 -B 2 -i "agent" "ec2_results/$(basename $verbose_result)" | head -n 20
  fi
fi

echo
echo -e "${YELLOW}Conclusion:${NC}"
if grep -q -i "agent\|communication\|decision\|message" "ec2_results/"* 2>/dev/null; then
  echo -e "${GREEN}✓ Found evidence of agent communications in logs or results${NC}"
  echo -e "${YELLOW}The multi-agent framework appears to be functioning, but may need better logging.${NC}"
else
  echo -e "${RED}✗ No clear evidence of agent communications found${NC}"
  echo -e "${YELLOW}The multi-agent framework may not be properly logging communications.${NC}"
  echo -e "${YELLOW}Try running the verbose script again with: ./run-multicommunicating-agent-backtest.sh${NC}"
fi

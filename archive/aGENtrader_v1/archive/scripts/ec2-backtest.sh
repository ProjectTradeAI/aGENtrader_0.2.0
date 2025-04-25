#!/bin/bash
# EC2 Backtest Runner
# This script runs backtests on the EC2 instance

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Configuration
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
KEY_PATH="/tmp/ec2_key.pem"
PROJECT_DIR="/home/ec2-user/aGENtrader"
MIXTRAL_MODEL_PATH="$PROJECT_DIR/models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"

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

# Check if the backtest script exists
check_backtest_script() {
  echo -e "${BLUE}Checking for backtest script...${NC}"
  run_ssh_cmd "test -f $PROJECT_DIR/ec2-multi-agent-backtest.sh" true
  if [ $? -eq 0 ]; then
    echo -e "${NC}Found backtest script"
    echo -e "${GREEN}✓ Backtest script verified${NC}"
    return 0
  else
    echo -e "${RED}✗ Backtest script not found. Ensure the script is located at:${NC}"
    echo -e "${BLUE}$PROJECT_DIR/ec2-multi-agent-backtest.sh${NC}"
    return 1
  fi
}

# Check if Mixtral model exists
check_mixtral_model() {
  echo -e "${BLUE}Checking Mixtral model availability...${NC}"
  run_ssh_cmd "test -f $MIXTRAL_MODEL_PATH" true
  if [ $? -eq 0 ]; then
    echo -e "${NC}Mixtral model found"
    return 0
  else
    echo -e "${RED}Mixtral model not found at $MIXTRAL_MODEL_PATH${NC}"
    return 1
  fi
}

# Run a backtest
run_backtest() {
  # Default values
  local type="simplified"
  local symbol="BTCUSDT"
  local interval="1h"
  local start_date="2025-03-01"
  local end_date="2025-04-01"
  local position_size=50
  local balance=10000
  local risk=0.02
  local decision_interval=2
  local min_confidence=75
  local use_local_llm=false
  local custom_cmd=""
  
  # Parse command line arguments
  while [[ "$#" -gt 0 ]]; do
    case $1 in
      --type) type="$2"; shift ;;
      --symbol) symbol="$2"; shift ;;
      --interval) interval="$2"; shift ;;
      --start) start_date="$2"; shift ;;
      --end) end_date="$2"; shift ;;
      --position_size) position_size="$2"; shift ;;
      --balance) balance="$2"; shift ;;
      --risk) risk="$2"; shift ;;
      --decision_interval) decision_interval="$2"; shift ;;
      --min_confidence) min_confidence="$2"; shift ;;
      --local-llm) use_local_llm=true ;;
      --custom) custom_cmd="$2"; shift ;;
      *) echo -e "${RED}Unknown option: $1${NC}"; show_help; return 1 ;;
    esac
    shift
  done
  
  # If a custom command was provided, run it directly
  if [ -n "$custom_cmd" ]; then
    echo -e "${BLUE}Running custom command: ${custom_cmd}${NC}"
    run_ssh_cmd "$custom_cmd"
    return $?
  fi
  
  # Check if the backtest script exists
  check_backtest_script || return 1
  
  # If using local LLM, check if Mixtral model exists
  if [ "$use_local_llm" = true ]; then
    check_mixtral_model || return 1
  fi
  
  # Print backtest configuration
  echo -e "${BLUE}======================== BACKTEST CONFIGURATION ========================${NC}"
  echo -e "${YELLOW}Type:         $type${NC}"
  echo -e "${YELLOW}Symbol:       $symbol${NC}"
  echo -e "${YELLOW}Interval:     $interval${NC}"
  echo -e "${YELLOW}Date Range:   $start_date to $end_date${NC}"
  
  if [ "$type" = "simplified" ]; then
    echo -e "${YELLOW}Position Size: $position_size${NC}"
  else
    echo -e "${YELLOW}Balance:       $balance${NC}"
    echo -e "${YELLOW}Risk:          $risk${NC}"
  fi
  
  if [ "$use_local_llm" = true ]; then
    echo -e "${YELLOW}Model:         Local Mixtral${NC}"
  else
    echo -e "${YELLOW}Model:         OpenAI API${NC}"
  fi
  echo -e "${BLUE}=====================================================================${NC}"
  
  # Build the backtest command
  local backtest_cmd="cd $PROJECT_DIR && ./ec2-multi-agent-backtest.sh --type $type --symbol $symbol --interval $interval --start_date $start_date --end_date $end_date"
  
  if [ "$type" = "simplified" ]; then
    backtest_cmd="$backtest_cmd --position_size $position_size"
  else
    backtest_cmd="$backtest_cmd --balance $balance --risk $risk --decision_interval $decision_interval --min_confidence $min_confidence"
  fi
  
  if [ "$use_local_llm" = true ]; then
    backtest_cmd="$backtest_cmd --local-llm"
  fi
  
  # Run the backtest
  echo -e "${BLUE}Starting backtest...${NC}"
  run_ssh_cmd "$backtest_cmd"
  
  local result=$?
  if [ $result -eq 0 ]; then
    echo -e "${GREEN}✓ Backtest completed successfully${NC}"
  else
    echo -e "${RED}✗ Backtest failed with code $result${NC}"
  fi
  
  return $result
}

# Check backtest status
check_status() {
  run_ssh_cmd "ps aux | grep -E 'run_.*backtest.py' | grep -v grep || echo 'No backtest running'"
}

# List available backtest results
list_results() {
  echo -e "${BLUE}Listing backtest results...${NC}"
  run_ssh_cmd "ls -la $PROJECT_DIR/results/"
}

# Get a specific backtest result
get_result() {
  local result_file="$1"
  if [ -z "$result_file" ]; then
    echo -e "${RED}Error: No result file specified${NC}"
    echo -e "Usage: $0 get <result_file>"
    return 1
  fi
  
  echo -e "${BLUE}Downloading $result_file...${NC}"
  mkdir -p results
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$PROJECT_DIR/results/$result_file" "results/$result_file"
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ File downloaded to results/$result_file${NC}"
  else
    echo -e "${RED}✗ Failed to download file${NC}"
    return 1
  fi
}

# View latest backtest log
view_log() {
  echo -e "${BLUE}Fetching latest backtest log...${NC}"
  local latest_log=$(run_ssh_cmd "find $PROJECT_DIR/data/logs -name '*backtest_*.log' | sort -r | head -n 1" true)
  
  if [ -z "$latest_log" ]; then
    echo -e "${RED}No log files found${NC}"
    return 1
  fi
  
  echo -e "${GREEN}Latest log: $(basename $latest_log)${NC}"
  echo -e "${BLUE}Log content (last 50 lines):${NC}"
  run_ssh_cmd "tail -n 50 $latest_log"
}

# Clean up old results and logs
clean_up() {
  echo -e "${BLUE}Cleaning up old backtest results and logs...${NC}"
  run_ssh_cmd "find $PROJECT_DIR/results -name '*.json' -type f -mtime +30 -delete"
  run_ssh_cmd "find $PROJECT_DIR/data/logs -name '*.log' -type f -mtime +30 -delete"
  echo -e "${GREEN}✓ Cleanup completed${NC}"
}

# Show help
show_help() {
  echo -e "${BOLD}EC2 Backtest Runner${NC}"
  echo -e "${BOLD}===================${NC}"
  echo
  echo -e "USAGE: "
  echo -e "  $0 [command] [options]"
  echo
  echo -e "COMMANDS:"
  echo -e "  run       Run a backtest with specified options"
  echo -e "  status    Check backtest status"
  echo -e "  list      List available backtest results"
  echo -e "  get       Download a specific result file"
  echo -e "  log       View the latest backtest log"
  echo -e "  clean     Clean up old results and logs"
  echo -e "  help      Show this help message"
  echo
  echo -e "OPTIONS FOR 'run':"
  echo -e "  --type TYPE       Backtest type: simplified, enhanced, full-scale (default: simplified)"
  echo -e "  --symbol SYM      Trading symbol (default: BTCUSDT)"
  echo -e "  --interval INT    Time interval: 1m, 5m, 15m, 1h, 4h, 1d (default: 1h)"
  echo -e "  --start DATE      Start date in YYYY-MM-DD format (default: 2025-03-01)"
  echo -e "  --end DATE        End date in YYYY-MM-DD format (default: 2025-04-01)"
  echo -e "  --position_size SIZE   Position size for simplified backtest (default: 50)"
  echo -e "  --balance AMT     Initial balance for enhanced/full-scale (default: 10000)"
  echo -e "  --risk PCT        Risk percentage as decimal (default: 0.02)"
  echo -e "  --local-llm       Use local Mixtral model instead of OpenAI API"
  echo -e "  --custom CMD      Run a custom command on EC2"
  echo -e "  "
  echo -e "EXAMPLES:"
  echo -e "  $0 run --type simplified --symbol BTCUSDT --interval 1h --local-llm"
  echo -e "  $0 run --type enhanced --start 2025-02-01 --end 2025-03-01"
  echo -e "  $0 run --custom \"cd $PROJECT_DIR && python3 run_simplified_backtest.py --help\""
  echo -e "  $0 list"
  echo -e "  $0 get backtest_result_20250401_120000.json"
}

# Main function
main() {
  # Handle the case when no arguments are provided
  if [ $# -eq 0 ]; then
    show_help
    exit 1
  fi
  
  # Setup SSH key
  setup_key
  
  # Process command
  case "$1" in
    run)
      shift
      run_backtest "$@"
      ;;
    status)
      check_status
      ;;
    list)
      list_results
      ;;
    get)
      shift
      get_result "$1"
      ;;
    log)
      view_log
      ;;
    clean)
      clean_up
      ;;
    help)
      show_help
      ;;
    *)
      echo -e "${RED}Unknown command: $1${NC}"
      show_help
      exit 1
      ;;
  esac
}

# Run the main function
main "$@"

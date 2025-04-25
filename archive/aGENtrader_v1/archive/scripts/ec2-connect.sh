#!/bin/bash
# EC2 Connection & Backtest Script

# Configuration
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
KEY_PATH="/tmp/ec2_ssh_key.pem"
PROJECT_DIR="/home/ec2-user/aGENtrader"

# Function for displaying colorful messages
print_msg() {
  local color=$1
  local msg=$2
  case $color in
    "green") echo -e "\033[0;32m$msg\033[0m" ;;
    "red") echo -e "\033[0;31m$msg\033[0m" ;;
    "yellow") echo -e "\033[0;33m$msg\033[0m" ;;
    "blue") echo -e "\033[0;34m$msg\033[0m" ;;
    *) echo "$msg" ;;
  esac
}

# Setup SSH key with proper formatting
setup_key() {
  print_msg "blue" "Setting up SSH key..."
  mkdir -p $(dirname "$KEY_PATH")
  
  # Create properly formatted key file
  echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
  echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
  echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
  
  chmod 600 "$KEY_PATH"
  
  # Validate key
  if openssl rsa -in "$KEY_PATH" -check -noout >/dev/null 2>&1; then
    print_msg "green" "✓ SSH key validated successfully"
    return 0
  else
    print_msg "red" "✗ SSH key validation failed"
    return 1
  fi
}

# Test SSH connection
test_connection() {
  print_msg "blue" "Testing connection to $EC2_IP..."
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$EC2_IP" "echo Connection successful" >/dev/null 2>&1
  
  if [ $? -eq 0 ]; then
    print_msg "green" "✓ Connection successful!"
    return 0
  else
    print_msg "red" "✗ Connection failed"
    return 1
  fi
}

# Run a command on EC2
run_command() {
  local cmd="$1"
  local silent=${2:-false}
  
  if [ "$silent" = false ]; then
    print_msg "blue" "Running command: $cmd"
    echo "---------------------------------------------------"
  fi
  
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "$cmd"
  local result=$?
  
  if [ "$silent" = false ]; then
    echo "---------------------------------------------------"
    if [ $result -eq 0 ]; then
      print_msg "green" "✓ Command completed successfully"
    else
      print_msg "red" "✗ Command failed with code $result"
    fi
  fi
  
  return $result
}

# Display help message
show_help() {
  cat << HELP
EC2 Connection & Backtest Tool
==============================

USAGE:
  ./ec2-connect.sh [command]
  
COMMANDS:
  connect                    Test connection to EC2
  ls [path]                  List files (default: project directory)
  check-status               Check EC2 instance status
  list-results               List backtest results
  backtest [options]         Run a backtest (see options below)
  get-result <filename>      Download a result file
  help                       Show this help message

BACKTEST OPTIONS:
  --type TYPE                Type of backtest: simplified, enhanced, full-scale
  --symbol SYMBOL            Trading symbol (default: BTCUSDT)
  --interval INTERVAL        Trading interval (default: 1h)
  --start DATE               Start date (YYYY-MM-DD, default: 2025-03-01)
  --end DATE                 End date (YYYY-MM-DD, default: 2025-04-01)
  --position-size SIZE       Position size for simplified backtest (default: 50)
  --balance AMOUNT           Initial balance for enhanced backtest (default: 10000)
  --risk PERCENTAGE          Risk percentage (default: 0.02) 
  --local-llm                Use local Mixtral model instead of OpenAI

EXAMPLES:
  ./ec2-connect.sh connect
  ./ec2-connect.sh ls
  ./ec2-connect.sh backtest --type simplified --symbol BTCUSDT --local-llm
  ./ec2-connect.sh get-result backtest_result_20250401_120000.json
HELP
}

# Run a backtest
run_backtest() {
  # Default values
  local type="simplified"
  local symbol="BTCUSDT"
  local interval="1h"
  local start_date="2025-03-01"
  local end_date="2025-04-01"
  local position_size="50"
  local balance="10000"
  local risk="0.02"
  local local_llm=""
  
  # Parse arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --type)
        type="$2"
        shift 2
        ;;
      --symbol)
        symbol="$2"
        shift 2
        ;;
      --interval)
        interval="$2"
        shift 2
        ;;
      --start)
        start_date="$2"
        shift 2
        ;;
      --end)
        end_date="$2"
        shift 2
        ;;
      --position-size)
        position_size="$2"
        shift 2
        ;;
      --balance)
        balance="$2"
        shift 2
        ;;
      --risk)
        risk="$2"
        shift 2
        ;;
      --local-llm)
        local_llm="--local-llm"
        shift
        ;;
      *)
        print_msg "red" "Unknown option: $1"
        return 1
        ;;
    esac
  done
  
  # Validate backtest type
  if [[ "$type" != "simplified" && "$type" != "enhanced" && "$type" != "full-scale" ]]; then
    print_msg "red" "Invalid backtest type: $type. Must be simplified, enhanced, or full-scale."
    return 1
  fi
  
  # Build the backtest command
  local backtest_cmd=""
  if [[ "$type" == "simplified" ]]; then
    backtest_cmd="cd $PROJECT_DIR && ./ec2-multi-agent-backtest.sh --type $type --symbol $symbol --interval $interval --start_date $start_date --end_date $end_date --position_size $position_size $local_llm"
  else
    backtest_cmd="cd $PROJECT_DIR && ./ec2-multi-agent-backtest.sh --type $type --symbol $symbol --interval $interval --start_date $start_date --end_date $end_date --balance $balance --risk $risk --decision_interval 2 --min_confidence 75 $local_llm"
  fi
  
  # Display configuration
  print_msg "blue" "======================== BACKTEST CONFIGURATION ========================"
  print_msg "yellow" "Type:         $type"
  print_msg "yellow" "Symbol:       $symbol"
  print_msg "yellow" "Interval:     $interval"
  print_msg "yellow" "Date Range:   $start_date to $end_date"
  if [[ "$type" == "simplified" ]]; then
    print_msg "yellow" "Position Size: $position_size"
  else
    print_msg "yellow" "Balance:       $balance"
    print_msg "yellow" "Risk:          $risk"
  fi
  if [[ -n "$local_llm" ]]; then
    print_msg "yellow" "Model:         Local Mixtral"
  else
    print_msg "yellow" "Model:         OpenAI API"
  fi
  print_msg "blue" "====================================================================="
  
  # Run the backtest
  run_command "$backtest_cmd"
  local result=$?
  
  if [ $result -eq 0 ]; then
    print_msg "green" "✓ Backtest completed successfully!"
    # List the latest result
    print_msg "blue" "Latest results:"
    run_command "cd $PROJECT_DIR && ls -t results/ | head -n 5"
  else
    print_msg "red" "✗ Backtest failed with code $result"
    print_msg "yellow" "Check logs for more details:"
    run_command "cd $PROJECT_DIR && ls -t data/logs/ | head -n 3"
  fi
}

# Download a result file
get_result_file() {
  local filename="$1"
  
  if [ -z "$filename" ]; then
    print_msg "red" "No filename specified"
    return 1
  fi
  
  print_msg "blue" "Downloading result file: $filename"
  
  # Create local directory for results
  mkdir -p ./ec2_results
  
  # Use scp to download the file
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$PROJECT_DIR/results/$filename" "./ec2_results/$filename"
  
  if [ $? -eq 0 ]; then
    print_msg "green" "✓ File downloaded successfully to ./ec2_results/$filename"
  else
    print_msg "red" "✗ Failed to download file"
  fi
}

# Main script execution
main() {
  # Setup SSH key
  setup_key || { print_msg "red" "Failed to setup SSH key. Exiting."; exit 1; }
  
  # No arguments, just test connection
  if [ $# -eq 0 ]; then
    test_connection
    if [ $? -eq 0 ]; then
      print_msg "green" "✓ EC2 connection is working properly!"
      print_msg "blue" "Try './ec2-connect.sh help' for available commands"
    fi
    exit 0
  fi
  
  # Process commands
  case "$1" in
    connect)
      test_connection
      ;;
    ls)
      path="${2:-$PROJECT_DIR}"
      run_command "ls -la $path"
      ;;
    check-status)
      print_msg "blue" "Checking EC2 instance status..."
      run_command "uptime && df -h && free -m"
      ;;
    list-results)
      print_msg "blue" "Listing backtest results..."
      run_command "cd $PROJECT_DIR && ls -la results/"
      ;;
    backtest)
      shift
      run_backtest "$@"
      ;;
    get-result)
      get_result_file "$2"
      ;;
    help)
      show_help
      ;;
    *)
      print_msg "red" "Unknown command: $1"
      print_msg "blue" "Try './ec2-connect.sh help' for available commands"
      exit 1
      ;;
  esac
}

# Execute main function with all arguments
main "$@"

#!/bin/bash
# Smart backtest runner with data integrity and guaranteed agent communications

# Setup SSH key
KEY_PATH="/tmp/smart_runner_key.pem"
echo "Setting up SSH key..."
echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Default parameters
BACKTEST_TYPE="full"  # Default to full-scale testing
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-01"
END_DATE="2025-03-02"
INITIAL_BALANCE=10000
DOWNLOAD_LOGS=true

# Parse command line options
while [[ $# -gt 0 ]]; do
  case $1 in
    --type)
      BACKTEST_TYPE="$2"
      shift 2
      ;;
    --symbol)
      SYMBOL="$2"
      shift 2
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --start)
      START_DATE="$2"
      shift 2
      ;;
    --end)
      END_DATE="$2"
      shift 2
      ;;
    --balance)
      INITIAL_BALANCE="$2"
      shift 2
      ;;
    --no-download)
      DOWNLOAD_LOGS=false
      shift
      ;;
    --help)
      echo "Usage: $0 [--type simplified|enhanced|full] [--symbol BTCUSDT] [--interval 1h] [--start 2025-03-01] [--end 2025-03-02] [--balance 10000] [--no-download]"
      echo
      echo "Options:"
      echo "  --type            Type of backtest (simplified, enhanced, full) [default: full]"
      echo "  --symbol          Trading symbol [default: BTCUSDT]"
      echo "  --interval        Time interval (1m, 5m, 15m, 1h, 4h, 1d) [default: 1h]"
      echo "  --start           Start date [default: 2025-03-01]"
      echo "  --end             End date [default: 2025-03-02]"
      echo "  --balance         Initial balance [default: 10000]"
      echo "  --no-download     Don't download the agent communication logs"
      echo "  --help            Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--type simplified|enhanced|full] [--symbol BTCUSDT] [--interval 1h] [--start 2025-03-01] [--end 2025-03-02] [--balance 10000] [--no-download] [--help]"
      exit 1
      ;;
  esac
done

# Print parameters
echo "Running $BACKTEST_TYPE backtest with parameters:"
echo "Symbol: $SYMBOL"
echo "Interval: $INTERVAL"
echo "Date Range: $START_DATE to $END_DATE"
echo "Initial Balance: $INITIAL_BALANCE"
echo "Download Logs: $DOWNLOAD_LOGS"
echo

# For all test types, we'll use the guaranteed agent communications backtest
echo "Uploading guaranteed agent communications backtest to EC2..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no guaranteed_agent_comms_backtest.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/

# Upload data integrity fix to EC2
echo "Uploading data integrity fix to EC2..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no data_integrity_fix.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/

# Apply data integrity fix first
echo "Applying data integrity fix on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 data_integrity_fix.py"

# Run the guaranteed backtest with appropriate parameters
echo "Running $BACKTEST_TYPE backtest with guaranteed agent communications..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 guaranteed_agent_comms_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $INITIAL_BALANCE"

# Check the results
echo
echo "Checking latest results..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && ls -la results/ | grep 'guaranteed' | tail -n 5"

# Get the latest log file
echo
echo "Locating latest agent communication log file..."
LATEST_LOG=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && find data/logs -name 'agent_comms_guaranteed_*.log' -type f -mmin -60 | sort -r | head -n 1")
echo "Latest agent comms log: $LATEST_LOG"

# Download the agent communications log if requested
if [ "$DOWNLOAD_LOGS" = true ]; then
  echo
  echo "Downloading the agent communications log..."
  LOG_NAME="${BACKTEST_TYPE}_${SYMBOL}_${START_DATE}_${END_DATE}_agent_comms.log"
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/$LATEST_LOG" "./$LOG_NAME"
  
  echo
  echo "Agent communications log downloaded to: ./$LOG_NAME"
  echo "Showing content of downloaded log:"
  cat "./$LOG_NAME" | head -n 20
  echo "..."
  cat "./$LOG_NAME" | tail -n 10
else
  echo
  echo "Showing content of the agent communications log on EC2:"
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && cat $LATEST_LOG | head -n 20"
  echo "..."
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && cat $LATEST_LOG | tail -n 10"
fi

echo
echo "Done! You can run different backtest types with --type [simplified|enhanced|full]"
echo "Example: $0 --type enhanced --symbol BTCUSDT --interval 1h --start 2025-03-01 --end 2025-03-02"

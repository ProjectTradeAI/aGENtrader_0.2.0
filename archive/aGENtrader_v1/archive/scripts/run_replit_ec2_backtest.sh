
#!/bin/bash
# Script to run full-scale backtesting on EC2 from Replit

# Default values
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-01"
END_DATE="2025-04-01"
INITIAL_BALANCE=10000
RISK_PER_TRADE=0.02
OUTPUT_DIR="data/backtests"

# Create temporary key file with proper OpenSSH format
KEY_FILE=$(mktemp)
echo "-----BEGIN OPENSSH PRIVATE KEY-----" > "$KEY_FILE"
echo "$EC2_SSH_KEY" | tr -d '\n' | sed 's/-----BEGIN OPENSSH PRIVATE KEY-----//g' | sed 's/-----END OPENSSH PRIVATE KEY-----//g' | fold -w 70 >> "$KEY_FILE"
echo "-----END OPENSSH PRIVATE KEY-----" >> "$KEY_FILE"
chmod 600 "$KEY_FILE"

# Debug key format (without exposing content)
echo "Checking key file format..."
echo "Key file permissions: $(ls -l $KEY_FILE)"
echo "First line of key file: $(head -n 1 $KEY_FILE)"
echo "Last line of key file: $(tail -n 1 $KEY_FILE)"

echo "======================================"
echo "Running Full-Scale Backtest on EC2"
echo "======================================"
echo "Symbol:          $SYMBOL"
echo "Interval:        $INTERVAL"
echo "Date Range:      $START_DATE to $END_DATE"
echo "Initial Balance: $INITIAL_BALANCE"
echo "======================================"

# Build the backtest command
BACKTEST_CMD="cd /home/ec2-user/aGENtrader && python run_backtest_with_local_llm.py \
  --symbol $SYMBOL \
  --interval $INTERVAL \
  --start_date $START_DATE \
  --end_date $END_DATE \
  --initial_balance $INITIAL_BALANCE \
  --risk_per_trade $RISK_PER_TRADE \
  --output_dir $OUTPUT_DIR"

# Execute backtest on EC2
echo "Executing backtest on EC2..."
ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "$BACKTEST_CMD"
EXIT_CODE=$?

# Clean up the key file
rm "$KEY_FILE"

if [ $EXIT_CODE -ne 0 ]; then
    echo "Error: Backtest failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
fi

echo "======================================"
echo "Backtest completed successfully!"
echo "Results are stored in: $OUTPUT_DIR"
echo "======================================"

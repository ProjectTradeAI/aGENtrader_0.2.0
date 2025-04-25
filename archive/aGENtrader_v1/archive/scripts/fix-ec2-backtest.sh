#!/bin/bash

# Create a backup of the original script
cp ec2-backtest.sh ec2-backtest.sh.bak

# Modify the ec2-backtest.sh script to use the correct parameters
sed -i 's/--position_size "$POSITION_SIZE"/--risk_per_trade "$RISK"/' ec2-backtest.sh

# Check if the modification was successful
if grep -q 'risk_per_trade' ec2-backtest.sh; then
  echo "Successfully updated ec2-backtest.sh to use correct parameters"
else
  echo "Failed to update script. Please modify ec2-backtest.sh manually to use --risk_per_trade instead of --position_size"
fi

echo
echo "To run a backtest with local LLM correctly, use:"
echo "./ec2-backtest.sh run --type simplified --symbol BTCUSDT --interval 1h --start 2025-03-01 --end 2025-03-07 --local-llm"
echo "or"
echo "./ec2-backtest.sh run --type enhanced --symbol BTCUSDT --interval 1h --start 2025-03-01 --end 2025-03-07 --balance 10000 --risk 0.02 --local-llm"

#!/bin/bash
# Script to run a backtest with the correct parameters

echo "This script will run a local LLM backtest with the correct parameters."
echo "Running a backtest for BTCUSDT from 2025-03-01 to 2025-03-07..."

# Run the command with the correct parameters
./ec2-backtest.sh run "cd /home/ec2-user/aGENtrader && python3 run_enhanced_backtest.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-07 --initial_balance 10000 --risk_per_trade 0.02 --use_local_llm"

echo
echo "To verify agent communications, we suggest running:"
echo "./ec2-backtest.sh run \"cd /home/ec2-user/aGENtrader && ./run_test.sh\""

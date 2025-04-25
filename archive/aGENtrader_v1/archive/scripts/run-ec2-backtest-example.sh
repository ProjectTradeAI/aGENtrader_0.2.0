#!/bin/bash
# Example script for running various backtests on EC2

# Enhanced backtest with OpenAI
function run_enhanced_backtest() {
  echo "Running enhanced backtest with OpenAI..."
  ./ec2-run.sh "./ec2-multi-agent-backtest.sh --type enhanced --symbol BTCUSDT --interval 4h --start_date 2025-03-01 --end_date 2025-04-01 --balance 10000 --risk 0.02 --decision_interval 2 --min_confidence 75"
}

# Simplified backtest with local Mixtral model
function run_simplified_local() {
  echo "Running simplified backtest with local Mixtral model..."
  ./ec2-run.sh "./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-04-01 --position_size 50 --local-llm"
}

# Full-scale backtest
function run_full_scale() {
  echo "Running full-scale backtest..."
  ./ec2-run.sh "./ec2-multi-agent-backtest.sh --type full-scale --symbol BTCUSDT --interval 4h --start_date 2025-03-01 --end_date 2025-04-01 --balance 10000 --risk 0.02 --decision_interval 2 --min_confidence 75"
}

# Show options
echo "EC2 Backtest Examples"
echo "====================="
echo "1) Run enhanced backtest with OpenAI"
echo "2) Run simplified backtest with local Mixtral model"
echo "3) Run full-scale backtest"
echo "q) Quit"
echo
read -p "Choose an option: " choice

case $choice in
  1) run_enhanced_backtest ;;
  2) run_simplified_local ;;
  3) run_full_scale ;;
  q|Q) echo "Exiting..." ;;
  *) echo "Invalid option" ;;
esac

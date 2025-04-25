#!/bin/bash
# Solution Script for Backtest Parameter Issues

echo "Backtest Parameter Issue - Solution"
echo "=================================="
echo
echo "The issue with the backtest scripts was a parameter mismatch."
echo "The PaperTradingSystem class only accepts three parameters:"
echo "  - data_dir (default: 'data/paper_trading')"
echo "  - default_account_id (default: 'default')"
echo "  - initial_balance (default: 10000.0)"
echo
echo "However, the backtest scripts were trying to pass additional parameters like:"
echo "  - symbol"
echo "  - trade_size_percent"
echo "  - take_profit_percent"
echo "  - stop_loss_percent"
echo "  - etc."
echo
echo "These are not valid parameters for PaperTradingSystem.__init__()"
echo
echo "The solution is to:"
echo "1. Initialize PaperTradingSystem with only the parameters it accepts"
echo "2. Handle the other parameters in your trading logic"
echo
echo "Here's a demonstration of a working backtest script:"
./working_backtest.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-02 --initial_balance 10000 --use_local_llm
echo
echo "To fix your EC2 scripts:"
echo "1. Update all backtest scripts to initialize PaperTradingSystem correctly"
echo "2. Modify the scripts to handle the additional parameters in the trading logic"
echo "3. Test the updated scripts with simple test cases first"
echo
echo "For quick backtesting, you can use the command:"
echo "./ec2-backtest.sh run \"cd /home/ec2-user/aGENtrader && python3 run_simplified_backtest.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-02 --initial_balance 10000 --use_local_llm\""

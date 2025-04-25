#!/bin/bash

# Instructions for running a backtest with the correct parameters

echo "Based on our examination, here's how to properly run a backtest with the local LLM:"
echo
echo "For enhanced backtest (recommended):"
echo "./ec2-backtest.sh run \"cd /home/ec2-user/aGENtrader && python3 run_enhanced_backtest.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-07 --initial_balance 10000 --risk_per_trade 0.02 --use_local_llm\""
echo
echo "For simplified backtest:"
echo "./ec2-backtest.sh run \"cd /home/ec2-user/aGENtrader && python3 run_simplified_backtest.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-02 --position_size 100 --use_local_llm\""
echo
echo "The problem in your original command was that you were trying to use the parameter --position_size with run_backtest_with_local_llm.py, but that script doesn't accept that parameter."
echo
echo "Additionally, to see agent communications in the backtest logs, use one of the logging scripts we created earlier:"
echo "./ec2-backtest.sh run \"cd /home/ec2-user/aGENtrader && ./run_test.sh\""

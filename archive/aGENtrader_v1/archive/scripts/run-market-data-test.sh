#!/bin/bash
# Script to run a market data test on EC2

python check_market_data.py --symbol BTCUSDT --interval 1h --days 7 --format text

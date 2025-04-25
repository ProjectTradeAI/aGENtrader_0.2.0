#!/bin/bash

# Script to run the timeframe consistency checker
echo "Running Timeframe Consistency Check"

# Make script executable
chmod +x scripts/check_timeframe_consistency.py

# Check for Binance API keys
if [ -z "$BINANCE_API_KEY" ]; then
    echo "Warning: BINANCE_API_KEY environment variable not set"
    echo "Public endpoints will be tested, but rate limiting may occur"
    
    # Ask for API keys if needed
    read -p "Would you like to provide a Binance API key? (y/n): " provide_key
    if [ "$provide_key" = "y" ] || [ "$provide_key" = "Y" ]; then
        read -p "Enter Binance API key: " BINANCE_API_KEY
        export BINANCE_API_KEY
    fi
fi

if [ -z "$BINANCE_API_SECRET" ] && [ ! -z "$BINANCE_API_KEY" ]; then
    # Ask for API secret if we have a key
    read -p "Would you like to provide a Binance API secret? (y/n): " provide_secret
    if [ "$provide_secret" = "y" ] || [ "$provide_secret" = "Y" ]; then
        read -p "Enter Binance API secret: " BINANCE_API_SECRET
        export BINANCE_API_SECRET
    fi
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the consistency check script
echo "Running consistency check for BTC/USDT across 1h, 4h, and 1d timeframes..."
python scripts/check_timeframe_consistency.py "$@"

# Check the exit code
if [ $? -eq 0 ]; then
    echo "✅ Consistency check completed successfully"
else
    echo "⚠️ Consistency check completed with warnings"
fi

# Display the output location
echo "Detailed results saved to logs/timeframe_data_debug.jsonl"
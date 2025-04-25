#!/bin/bash

# Make sure the logs directory exists
mkdir -p logs

echo "Running TradeBookManager test..."
python test_trade_book.py

# Print test results
if [ $? -eq 0 ]; then
    echo "✅ Test completed successfully!"
else
    echo "❌ Test failed!"
fi
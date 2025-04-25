#!/bin/bash

# run-workflow.sh - Entry point for aGENtrader v2.1 test

# Create required directories
mkdir -p logs
mkdir -p datasets

echo "==============================================="
echo "aGENtrader v2.1 Full Test Run"
echo "==============================================="

# Check Python environment
echo "Python version:"
python --version

# 1. Run test decision logger to create sample logs
echo -e "\n=== Step 1: Generate test decision logs ==="
python test_decision_logger.py

# 2. Run main application for one cycle
echo -e "\n=== Step 2: Run main application for one cycle ==="
python run.py --mode test --interval 1h --symbol BTCUSDT

# 3. Export decision dataset
echo -e "\n=== Step 3: Export decision dataset ==="
python scripts/export_decision_dataset.py --limit 100

# 4. Check log files
echo -e "\n=== Step 4: Checking log files ==="
if [ -f "logs/decision_summary.logl" ]; then
  echo "✅ Decision log created successfully"
else
  echo "❌ Decision log not found"
fi

if [ -f "logs/trade_book.jsonl" ]; then
  echo "✅ Trade book log created successfully"
else
  echo "❌ Trade book log not found"
fi

# Check for any decision dataset file (uses timestamp in filename)
if ls datasets/decision_log_dataset_v*.jsonl 1> /dev/null 2>&1; then
  echo "✅ Decision dataset exported successfully"
else
  echo "❌ Decision dataset export failed"
fi

echo -e "\nFull test run completed!"
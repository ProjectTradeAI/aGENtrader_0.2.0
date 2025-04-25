#!/bin/bash
# Authentic Multi-Agent Backtest Runner

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="data/logs"
mkdir -p $LOG_DIR

# Log file for this run
LOG_FILE="$LOG_DIR/authentic_backtest_$TIMESTAMP.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Authentic Multi-Agent Backtest" | tee -a $LOG_FILE
echo "Symbol: BTCUSDT, Interval: 1h, Date Range: 2025-03-20 to 2025-03-22" | tee -a $LOG_FILE
echo "-----------------------------------------------------" | tee -a $LOG_FILE

# Set Python path to include the current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "PYTHONPATH set to: $PYTHONPATH" | tee -a $LOG_FILE

# Make sure we have the agent_logging_patch.py file
if [ ! -f "agent_logging_patch.py" ]; then
  echo "❌ ERROR: agent_logging_patch.py not found!" | tee -a $LOG_FILE
  exit 1
fi

# Create a wrapper script that applies the agent logging patch
cat > run_with_agent_logging.py << 'PYEOF'
#!/usr/bin/env python3
"""
Run backtest with enhanced agent logging
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Configure main logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'data/logs/run_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("backtest")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run authentic backtest with agent logging")
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--interval', type=str, default='1h', help='Time interval')
    parser.add_argument('--start_date', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial_balance', type=float, default=10000.0, help='Initial balance')
    return parser.parse_args()

def main():
    """Run backtest with agent logging"""
    args = parse_args()
    
    logger.info(f"Starting backtest for {args.symbol} {args.interval} from {args.start_date} to {args.end_date}")
    
    # Import and apply agent logging patch
    logger.info("Applying agent logging patch...")
    try:
        from agent_logging_patch import monkey_patch_agent_framework
        result = monkey_patch_agent_framework()
        logger.info(f"Agent logging patch applied: {result}")
    except Exception as e:
        logger.error(f"Failed to apply agent logging patch: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Import backtest module after patching
    try:
        logger.info("Importing authentic_backtest module...")
        from backtesting.core.authentic_backtest import run_backtest
        
        # Run the backtest
        logger.info(f"Running backtest...")
        result = run_backtest(
            symbol=args.symbol,
            interval=args.interval,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_balance=args.initial_balance
        )
        
        # Save result to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_dir = 'results'
        os.makedirs(result_dir, exist_ok=True)
        result_file = os.path.join(result_dir, f'authentic_backtest_{args.symbol}_{args.interval}_{timestamp}.json')
        
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Backtest completed, results saved to {result_file}")
        
        # Print performance summary
        metrics = result.get('performance_metrics', {})
        print("\n===== PERFORMANCE SUMMARY =====")
        print(f"Initial Balance: ${metrics.get('initial_balance', 0):.2f}")
        print(f"Final Equity: ${metrics.get('final_equity', 0):.2f}")
        print(f"Total Return: {metrics.get('total_return_pct', 0):.2f}%")
        print(f"Win Rate: {metrics.get('win_rate', 0):.2f}% ({metrics.get('winning_trades', 0)}/{metrics.get('total_trades', 0)})")
        print(f"Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
        print("==============================")
        
    except ImportError as e:
        logger.error(f"Failed to import authentic_backtest: {e}")
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
PYEOF

chmod +x run_with_agent_logging.py

# Run the enhanced backtest
echo "Starting backtest with enhanced agent logging..." | tee -a $LOG_FILE
python3 run_with_agent_logging.py \
  --symbol "BTCUSDT" \
  --interval "1h" \
  --start_date "2025-03-20" \
  --end_date "2025-03-22" \
  --initial_balance "10000" | tee -a $LOG_FILE

# Find and display agent communications logs
echo -e "\nRetrieving agent communications logs..." | tee -a $LOG_FILE
AGENT_LOG=$(find data/logs -name "agent_comms_*.log" | sort -r | head -n 1)

if [ -n "$AGENT_LOG" ]; then
  echo "Found agent communications log: $AGENT_LOG" | tee -a $LOG_FILE
  echo "===== AGENT COMMUNICATIONS =====" | tee -a $LOG_FILE
  cat "$AGENT_LOG" | tee -a $LOG_FILE
  echo "================================" | tee -a $LOG_FILE
else
  echo "No agent communications log found" | tee -a $LOG_FILE
fi

echo "Backtest completed at $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $LOG_FILE

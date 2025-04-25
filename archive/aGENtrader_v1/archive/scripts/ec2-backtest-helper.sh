#!/bin/bash
# Helper script for running backtests on EC2

# Default values
SYMBOL="BTCUSDT"
INTERVAL="4h"
INITIAL_BALANCE=10000.0
POSITION_SIZE=100.0
USE_STOP_LOSS=true
STOP_LOSS_PCT=5.0
USE_TAKE_PROFIT=true
TAKE_PROFIT_PCT=10.0
VERBOSE=true

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Display help
function show_help {
  echo "EC2 Backtest Helper Script"
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  --symbol SYMBOL         Trading symbol (default: BTCUSDT)"
  echo "  --interval INTERVAL     Time interval (default: 4h)"
  echo "  --start_date DATE       Start date in YYYY-MM-DD format (required)"
  echo "  --end_date DATE         End date in YYYY-MM-DD format (required)"
  echo "  --balance AMOUNT        Initial account balance (default: 10000.0)"
  echo "  --position_size PCT     Position size percentage (default: 100.0)"
  echo "  --no-stop-loss          Disable stop loss (default: enabled)"
  echo "  --stop-loss-pct PCT     Stop loss percentage (default: 5.0)"
  echo "  --no-take-profit        Disable take profit (default: enabled)"
  echo "  --take-profit-pct PCT   Take profit percentage (default: 10.0)"
  echo "  --trailing-stop         Enable trailing stop (default: disabled)"
  echo "  --no-verbose            Disable verbose logging (default: enabled)"
  echo "  --help                  Display this help message"
  echo ""
  echo "Example:"
  echo "  $0 --symbol BTCUSDT --interval 4h --start_date 2025-03-01 --end_date 2025-04-01"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --symbol)
      SYMBOL="$2"
      shift 2
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --start_date)
      START_DATE="$2"
      shift 2
      ;;
    --end_date)
      END_DATE="$2"
      shift 2
      ;;
    --balance)
      INITIAL_BALANCE="$2"
      shift 2
      ;;
    --position_size)
      POSITION_SIZE="$2"
      shift 2
      ;;
    --no-stop-loss)
      USE_STOP_LOSS=false
      shift
      ;;
    --stop-loss-pct)
      STOP_LOSS_PCT="$2"
      shift 2
      ;;
    --no-take-profit)
      USE_TAKE_PROFIT=false
      shift
      ;;
    --take-profit-pct)
      TAKE_PROFIT_PCT="$2"
      shift 2
      ;;
    --trailing-stop)
      TRAILING_STOP=true
      shift
      ;;
    --no-verbose)
      VERBOSE=false
      shift
      ;;
    --help)
      show_help
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      show_help
      exit 1
      ;;
  esac
done

# Check for required parameters
if [ -z "$START_DATE" ] || [ -z "$END_DATE" ]; then
  echo -e "${RED}Error: --start_date and --end_date are required.${NC}"
  show_help
  exit 1
fi

# Build the command
CMD="python3 run_simplified_full_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $INITIAL_BALANCE --position_size $POSITION_SIZE"

if [ "$USE_STOP_LOSS" = true ]; then
  CMD="$CMD --use_stop_loss --stop_loss_pct $STOP_LOSS_PCT"
fi

if [ "$USE_TAKE_PROFIT" = true ]; then
  CMD="$CMD --use_take_profit --take_profit_pct $TAKE_PROFIT_PCT"
fi

if [ "$TRAILING_STOP" = true ]; then
  CMD="$CMD --trailing_stop"
fi

if [ "$VERBOSE" = true ]; then
  CMD="$CMD --verbose"
fi

# Display summary
echo -e "${GREEN}Running Backtest with the following parameters:${NC}"
echo "Symbol:          $SYMBOL"
echo "Interval:        $INTERVAL"
echo "Date Range:      $START_DATE to $END_DATE"
echo "Initial Balance: $INITIAL_BALANCE"
echo "Position Size:   $POSITION_SIZE%"
echo "Stop Loss:       $([ "$USE_STOP_LOSS" = true ] && echo "Enabled ($STOP_LOSS_PCT%)" || echo "Disabled")"
echo "Take Profit:     $([ "$USE_TAKE_PROFIT" = true ] && echo "Enabled ($TAKE_PROFIT_PCT%)" || echo "Disabled")"
echo "Trailing Stop:   $([ "$TRAILING_STOP" = true ] && echo "Enabled" || echo "Disabled")"
echo "Verbose Logging: $([ "$VERBOSE" = true ] && echo "Enabled" || echo "Disabled")"
echo ""
echo -e "${YELLOW}Command:${NC} $CMD"
echo ""

# Confirm and run
read -p "Press ENTER to start the backtest or CTRL+C to cancel..." 

echo -e "${GREEN}Starting backtest...${NC}"
echo ""

# Execute the command
$CMD

# Check exit status
if [ $? -eq 0 ]; then
  echo ""
  echo -e "${GREEN}Backtest completed successfully!${NC}"
  echo ""
  echo "Results should be available in the data/backtests directory."
  echo "Check the latest files:"
  ls -lt data/backtests | head -10
else
  echo ""
  echo -e "${RED}Backtest failed with errors.${NC}"
  echo "Check logs for details."
fi

#!/bin/bash
# Verify Authentic Backtesting Framework
# This script checks that the new authentic backtesting framework is working properly

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
  echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

log_info() {
  echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Make the script executable
chmod +x ./backtesting/scripts/run_authentic_backtest.sh

# Check for EC2_KEY
if [ -z "$EC2_KEY" ]; then
  log_warning "EC2_KEY environment variable is not set. Only local testing will be available."
fi

if [ -z "$EC2_PUBLIC_IP" ]; then
  log_warning "EC2_PUBLIC_IP environment variable is not set. Only local testing will be available."
fi

# Step 1: Check database connection
log "Step 1: Checking database connection..."
python3 -c "import sys; sys.path.append('.'); from backtesting.utils.data_integrity_checker import check_database_access; print('Database connection test:'); print(check_database_access())"

if [ $? -ne 0 ]; then
  log_warning "Database connection check failed. Please check your DATABASE_URL environment variable."
  log_warning "Continuing with other checks..."
fi

# Step 2: Check market data utilities
log "Step 2: Checking market data utilities..."
python3 -c "import sys; sys.path.append('.'); from backtesting.utils.market_data import get_available_symbols, get_available_intervals; print('Available symbols:', get_available_symbols()[:5]); print('Available intervals:', get_available_intervals())"

if [ $? -ne 0 ]; then
  log_error "Market data utilities check failed."
  exit 1
fi

# Step 3: Check data integrity utilities
log "Step 3: Checking data integrity utilities..."
python3 backtesting/utils/data_integrity_checker.py

if [ $? -ne 0 ]; then
  log_warning "Data integrity utilities check had issues, but continuing."
fi

# Step 4: Run a short test backtest
log "Step 4: Running a short test backtest..."

# Get the current date
CURRENT_DATE=$(date +%Y-%m-%d)

# Calculate the date 3 days ago
THREE_DAYS_AGO=$(date -d "3 days ago" +%Y-%m-%d)

./backtesting/scripts/run_authentic_backtest.sh --symbol BTCUSDT --interval 1h --start $THREE_DAYS_AGO --end $CURRENT_DATE --verbose

if [ $? -ne 0 ]; then
  log_error "Test backtest failed."
  exit 1
fi

# Step 5: Check for result files
log "Step 5: Checking for result files..."
LATEST_RESULT=$(ls -t ./results/backtest_*.json 2>/dev/null | head -n 1)

if [ -n "$LATEST_RESULT" ]; then
  log_info "Latest result file: $LATEST_RESULT"
  
  # Visualize the results
  log "Step 6: Visualizing backtest results..."
  python3 backtesting/analysis/visualize_backtest.py --backtest-file "$LATEST_RESULT" --output-dir "./data/analysis"
  
  if [ $? -ne 0 ]; then
    log_warning "Visualization failed, but the backtesting framework is still functional."
  else
    log_info "Visualization successful! Check the data/analysis directory for plots."
  fi
else
  log_warning "No result files found. The backtest may have failed or not produced any results."
fi

log "✅ Verification of authentic backtesting framework complete!"
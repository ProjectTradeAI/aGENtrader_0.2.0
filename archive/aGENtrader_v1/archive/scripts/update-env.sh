#!/bin/bash
# Script to update the .env file with actual environment variables

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

log "Updating .env file with actual environment variables..."

# Check if DATABASE_URL is set
if [ -z "${DATABASE_URL}" ]; then
  log_error "DATABASE_URL environment variable is not set!"
  log_info "Please set it with: export DATABASE_URL=your_database_url"
  exit 1
fi

# Create or update .env file
cat > .env << EOF
SESSION_SECRET=bZyxYOvBxEertvn1IINT7PmaYKyp44ha
NODE_ENV=production
PORT=5000

# Database configuration for backtesting
DATABASE_URL=${DATABASE_URL}
ALPACA_API_KEY=${ALPACA_API_KEY}
ALPACA_API_SECRET=${ALPACA_API_SECRET}
EOF

log "✅ .env file updated successfully with current environment variables."
log_info "Environment variables set:"
log_info "- DATABASE_URL: ${DATABASE_URL:0:20}... (truncated for security)"
log_info "- ALPACA_API_KEY: ${ALPACA_API_KEY:+✓ Set}"
log_info "- ALPACA_API_SECRET: ${ALPACA_API_SECRET:+✓ Set}"

log "You can now run:"
log_info "./deploy-backtest-hardcoded.sh && ./run-backtest-hardcoded.sh --symbol BTCUSDT --interval 1h --start 2025-04-01 --end 2025-04-10"
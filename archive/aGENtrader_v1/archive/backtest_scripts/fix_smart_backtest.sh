#!/bin/bash
# Script to find and fix smart-backtest-runner.sh

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Log function
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
  echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Upload this script to EC2
scp -i /tmp/manual_key.pem fix_smart_backtest.sh ec2-user@$EC2_PUBLIC_IP:~/

# Execute the script on EC2
./ec2-connect-working.sh "
cd ~/
chmod +x fix_smart_backtest.sh

echo '======================================='
echo 'Searching for smart-backtest-runner.sh'
echo '======================================='
find ~ -type f -exec grep -l 'smart.*backtest' {} \\; 2>/dev/null | sort

echo
echo '======================================='
echo 'Looking for the file you mentioned...'
echo '======================================='
find ~ -type f -name '*.sh' -exec grep -l 'smart.*backtest' {} \\; 2>/dev/null | sort

echo
echo '======================================='
echo 'Creating a fix for your backtest script'
echo '======================================='

# Create the data integrity runner wrapper
cat > ~/data_integrity_runner.sh << 'EOFINNER'
#!/bin/bash
# Data Integrity Runner Wrapper
# This script ensures data integrity is applied before running any backtests

# First apply the data integrity fix
cd ~/aGENtrader
python3 direct_fix.py

# Then run the original command with all arguments
exec \"\$@\"
EOFINNER

chmod +x ~/data_integrity_runner.sh
echo 'Created data_integrity_runner.sh wrapper script'

# Create a simple README with instructions
cat > ~/SMART_BACKTEST_FIX_INSTRUCTIONS.md << 'EOFREADME'
# Smart Backtest Runner Fix Instructions

To ensure data integrity is applied before running your backtests:

## Option 1: Use the wrapper script

Run your smart-backtest-runner.sh like this:
```bash
~/data_integrity_runner.sh ~/path/to/your/smart-backtest-runner.sh [args]
```

This approach works without modifying your original script.

## Option 2: Modify your script directly

1. Edit your smart-backtest-runner.sh
2. Add this line at the beginning (after #!/bin/bash):
   ```bash
   # Apply data integrity fix
   cd ~/aGENtrader && python3 direct_fix.py
   ```

## Option 3: Create a new script (recommended)

Create a new script that combines both:
```bash
#!/bin/bash
# smart-backtest-runner-with-integrity.sh

# Apply data integrity fix
cd ~/aGENtrader && python3 direct_fix.py

# Then run your original smart-backtest-runner.sh with all arguments
~/path/to/your/smart-backtest-runner.sh \"$@\"
```

This ensures data integrity is always applied before running backtests.
EOFREADME

echo 'Created SMART_BACKTEST_FIX_INSTRUCTIONS.md with detailed instructions'
"

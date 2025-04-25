#!/bin/bash
# Script to fetch backtest results from EC2

# Source the SSH key setup script if it exists
if [ -f "fix-ssh-key.sh" ]; then
    source fix-ssh-key.sh
fi

# Set variables
SSH_KEY_PATH="ec2_ssh_key.pem"
SSH_USER="ec2-user"
EC2_IP="${EC2_PUBLIC_IP}"
LOCAL_DIR="ec2_results"

# Ensure the local directory exists
mkdir -p "$LOCAL_DIR"

echo "Fetching backtest results from EC2 instance..."

# Create a script to find and prepare results on EC2
cat > ec2_gather_results.sh << 'REMOTE_CMD'
#!/bin/bash
echo "Gathering backtest results..."

# Create a directory for results if it doesn't exist
mkdir -p ~/backtest_results

# Locate all json result files from backtests
find ~/aGENtrader -name "*backtest*.json" -type f -exec cp {} ~/backtest_results/ \;

# Create a summary file
echo "Creating summary..."
cd ~/backtest_results

echo "====================================================================================================
BACKTEST RESULTS SUMMARY
====================================================================================================" > summary.md

# Loop through all JSON files and extract key metrics
for file in *.json; do
  echo "Processing $file..."
  
  # Extract key metrics using Python
  python3 -c "
import json
import os

filename = '$file'
with open(filename, 'r') as f:
    data = json.load(f)

# Extract key metrics
symbol = data.get('symbol', 'Unknown')
strategy = data.get('strategy_name', 'Unknown')
return_pct = data.get('total_return_pct', 0)
profit = data.get('net_profit', 0)
win_rate = data.get('win_rate', 0) * 100 if 'win_rate' in data else 0
pf = data.get('profit_factor', 0)
sharpe = data.get('sharpe_ratio', 0)
max_dd = data.get('max_drawdown_pct', 0)
trades = data.get('total_trades', 0)
expectancy = data.get('expectancy', 0)

# Print metrics to summary file
with open('summary.md', 'a') as summary:
    summary.write(f'\n{symbol}_{strategy}_{os.path.basename(filename)}\n')
    summary.write(f'Return: {return_pct:.2f}%, Profit: ${profit:.2f}, Win Rate: {win_rate:.1f}%\n')
    summary.write(f'Profit Factor: {pf:.2f}, Sharpe: {sharpe:.2f}, Max Drawdown: {max_dd:.1f}%\n')
    summary.write(f'Trades: {trades}, Expectancy: ${expectancy:.2f}\n')
    summary.write('-' * 100 + '\n')
  "
done

echo "Results gathered successfully!"
REMOTE_CMD

# Transfer the script to EC2
echo "Transferring script to EC2..."
scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no ec2_gather_results.sh "${SSH_USER}@${EC2_IP}:~/ec2_gather_results.sh"

# Execute the script on EC2
echo "Executing script on EC2..."
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "${SSH_USER}@${EC2_IP}" "chmod +x ~/ec2_gather_results.sh && ~/ec2_gather_results.sh"

# Fetch the results from EC2
echo "Downloading results from EC2..."
scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -r "${SSH_USER}@${EC2_IP}:~/backtest_results/*" "$LOCAL_DIR/"

# Clean up the temporary script
rm ec2_gather_results.sh

echo "Backtest results successfully fetched from EC2 to $LOCAL_DIR/"

#!/bin/bash
# Check all agent files for methods and classes

# Setup SSH key
KEY_PATH="/tmp/check_agent_files_key.pem"
echo "Setting up SSH key..."
echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Upload the test scripts to EC2
echo "Uploading test scripts to EC2..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no simple_agent_test.py simple_paper_trading_test.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/

# Run the paper trading test
echo "Running paper trading test on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 simple_paper_trading_test.py"

echo
echo "Checking for decision_session_updated.py file..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && ls -la orchestration/decision_session_updated.py || echo 'File not found'"

echo
echo "Looking for working full-scale backtest scripts..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && find . -type f -name '*full*scale*backtest*.py'"

echo
echo "Testing if the run_full_scale_backtest.py actually exists..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && ls -la run_full_scale_backtest.py || echo 'File not found'"

echo
echo "Creating a check-agent-communications.sh script..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && cat > check-agent-communications.sh << 'CHECKSCRIPT'
#!/bin/bash
# Check agent communications

timestamp=\$(date +%Y%m%d_%H%M%S)
log_file=data/logs/agent_comms_check_\${timestamp}.log

# Configure logging
mkdir -p data/logs

# Run the agent logging patch directly
python3 -c \"
import sys
sys.path.insert(0, '.')
from agent_logging_patch import monkey_patch_agent_framework
print('Applying agent logging patch...')
monkey_patch_agent_framework()
print('Agent logging patch applied')
\" | tee \$log_file

# Check for agent communication log files
echo \"Checking for agent communication log files...\" | tee -a \$log_file
find data/logs -name 'agent_comms_*.log' -type f -mmin -60 | sort -r | tee -a \$log_file

# Show the content of the latest agent communication log
echo \"Content of the latest agent communication log:\" | tee -a \$log_file
find data/logs -name 'agent_comms_*.log' -type f -mmin -60 | sort -r | head -n 1 | xargs cat | tee -a \$log_file

echo \"Check completed. Results saved to \$log_file\"
CHECKSCRIPT
chmod +x check-agent-communications.sh"

echo
echo "Running check-agent-communications.sh on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && ./check-agent-communications.sh"

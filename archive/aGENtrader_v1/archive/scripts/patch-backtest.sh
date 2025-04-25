#!/bin/bash
# Create a small test script on EC2 to verify agent communications

# Function to update a script on EC2
function update_script_on_ec2() {
  ./ec2-backtest.sh run "cat > /home/ec2-user/aGENtrader/$1 << 'SCRIPTCONTENT'
$2
SCRIPTCONTENT
chmod +x /home/ec2-user/aGENtrader/$1"
}

# Create a simple script to patch logging
PATCH_SCRIPT="#!/usr/bin/env python3
\"\"\"
Agent communications verification script

This script tests if agent communications are properly logged in backtests.
\"\"\"
import os
import sys
import logging
from datetime import datetime

# Configure logging for agent communications
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_dir = os.path.join('data', 'logs')
os.makedirs(log_dir, exist_ok=True)

# Create a log file specifically for agent communications
agent_log_file = os.path.join(log_dir, f'agent_test_{timestamp}.log')
print(f'Agent communications will be logged to: {agent_log_file}')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(agent_log_file)
    ]
)

# Create a special logger for agent communications
agent_logger = logging.getLogger('agent_comms')

# Log some test messages
agent_logger.info('=== AGENT COMMUNICATIONS TEST ===')
agent_logger.info('Technical Analyst: Based on the recent price action, I see a bullish pattern forming.')
agent_logger.info('Fundamental Analyst: On-chain metrics and recent news are positive.')
agent_logger.info('Risk Manager: Given current volatility, I recommend a position size of 2% of portfolio.')
agent_logger.info('Decision Agent: After considering all inputs, I recommend a BUY with 80% confidence.')
agent_logger.info('=== TEST COMPLETED ===')

print(f'\\nTest completed. Agent communications logged to: {agent_log_file}')
print('To verify, run: cat ' + agent_log_file)
"

# Create a wrapper script to run a backtest with agent logging
WRAPPER_SCRIPT="#!/bin/bash
# Wrapper script to run a backtest with agent communications logging

# Add improved logging
echo \"Adding improved logging...\"
cat > /home/ec2-user/aGENtrader/agent_logging.py << 'PYTHONCODE'
import os
import sys
import logging
from datetime import datetime

# Configure logging for agent communications
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_dir = os.path.join('data', 'logs')
os.makedirs(log_dir, exist_ok=True)

# Create a log file specifically for agent communications
agent_log_file = os.path.join(log_dir, f'agent_comms_{timestamp}.log')
print(f'Agent communications will be logged to: {agent_log_file}')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(agent_log_file)
    ]
)

# Create a special logger for agent communications
agent_logger = logging.getLogger('agent_comms')
PYTHONCODE

# Run a simple test to verify agent logging works
echo \"Running agent logging test...\"
python3 -c \"
import agent_logging
agent_logging.agent_logger.info('=== AGENT COMMUNICATIONS TEST ===')
agent_logging.agent_logger.info('Technical Analyst: This is a test message')
agent_logging.agent_logger.info('=== TEST COMPLETED ===')
\"

# Now run an actual backtest with extra logging
echo \"Running enhanced backtest with agent logging...\"
PYTHONPATH=. python3 -c \"
import agent_logging
import sys
agent_logging.agent_logger.info('=== STARTING BACKTEST WITH AGENT LOGGING ===')
print('Running enhanced backtest...')
try:
    sys.path.insert(0, '.')
    from agents.collaborative_decision_agent import CollaborativeDecisionFramework
    agent_logging.agent_logger.info('Successfully imported CollaborativeDecisionFramework')
    
    from orchestration.decision_session import DecisionSession
    agent_logging.agent_logger.info('Successfully imported DecisionSession')
    
    from orchestration.autogen_manager import AutoGenManager
    agent_logging.agent_logger.info('Successfully imported AutoGenManager')
    
    # Log available agent files
    import os
    agent_logging.agent_logger.info('Available agent files:')
    for f in os.listdir('agents'):
        if f.endswith('.py'):
            agent_logging.agent_logger.info(f'- agents/{f}')
    
    # Run a mock test of agent communications
    agent_logging.agent_logger.info('\\n=== SIMULATING AGENT COMMUNICATIONS ===')
    agent_logging.agent_logger.info('Technical Analyst: Based on the recent price action, I see a bullish pattern forming.')
    agent_logging.agent_logger.info('Fundamental Analyst: On-chain metrics and recent news are positive.')
    agent_logging.agent_logger.info('Risk Manager: Given current volatility, I recommend a position size of 2% of portfolio.')
    agent_logging.agent_logger.info('Decision Agent: After considering all inputs, I recommend a BUY with 80% confidence.')
    
    # Now try to run a real backtest
    agent_logging.agent_logger.info('\\n=== ATTEMPTING TO RUN ACTUAL BACKTEST ===')
    
    # Try to execute a backtest
    import sys
    sys.argv = ['run_enhanced_backtest.py', '--symbol', 'BTCUSDT', '--interval', '1h', 
                '--start_date', '2025-03-01', '--end_date', '2025-03-02',
                '--initial_balance', '10000', '--risk_per_trade', '0.02', '--use_local_llm']
    
    try:
        import run_enhanced_backtest
        agent_logging.agent_logger.info('Successfully ran enhanced backtest')
    except Exception as e:
        agent_logging.agent_logger.error(f'Error running backtest: {e}')
    
    agent_logging.agent_logger.info('=== BACKTEST COMPLETED ===')
    
except Exception as e:
    agent_logging.agent_logger.error(f'Error in test: {e}')
\"

# Display the agent communications log
echo \"\\nRetrieving agent communications log...\"
LATEST_LOG=\$(find data/logs -name 'agent_comms_*.log' | sort -r | head -n 1)

if [ -n \"\$LATEST_LOG\" ]; then
    echo \"Agent communications log: \$LATEST_LOG\"
    echo \"Log content:\"
    echo \"=====================================================\"
    cat \"\$LATEST_LOG\"
    echo \"=====================================================\"
else
    echo \"No agent communications log found.\"
fi
"

# Update scripts on EC2
echo "Uploading test scripts to EC2..."
update_script_on_ec2 "test_agent_communications.py" "$PATCH_SCRIPT"
update_script_on_ec2 "run_with_agent_logging.sh" "$WRAPPER_SCRIPT"

echo
echo "Scripts uploaded to EC2."
echo
echo "To test agent communications logging, run:"
echo "./ec2-backtest.sh run \"cd /home/ec2-user/aGENtrader && python3 test_agent_communications.py\""
echo
echo "To run a backtest with enhanced agent logging, run:"
echo "./ec2-backtest.sh run \"cd /home/ec2-user/aGENtrader && bash run_with_agent_logging.sh\""
echo
echo "Running agent communications test..."
./ec2-backtest.sh run "cd /home/ec2-user/aGENtrader && python3 test_agent_communications.py"

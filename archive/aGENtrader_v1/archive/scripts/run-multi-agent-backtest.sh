#!/bin/bash
# Script to run a multi-agent backtest with visible agent communications

# Setup
KEY_PATH="/tmp/multi_agent_key.pem"
echo "Setting up SSH key..."
echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
chmod 600 "$KEY_PATH"

# First, create our custom logging patch
cat > agent_logging_patch.py << 'PYTHONCODE'
#!/usr/bin/env python3
"""
Agent logging patch for multi-agent backtests
"""

import sys
import os
import logging
from datetime import datetime

# Configure logging for agent communications
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_dir = os.path.join('data', 'logs')
os.makedirs(log_dir, exist_ok=True)

# Create a log file specifically for agent communications
agent_log_file = os.path.join(log_dir, f'agent_comms_{timestamp}.log')
print(f'Agent communications will be logged to: {agent_log_file}')

# Create a special formatter for agent communications
agent_formatter = logging.Formatter('%(asctime)s - AGENT - %(message)s')

# Create file handler for agent communications
agent_handler = logging.FileHandler(agent_log_file)
agent_handler.setFormatter(agent_formatter)
agent_handler.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(agent_formatter)
console_handler.setLevel(logging.INFO)

# Create a dedicated logger for agent communications
agent_logger = logging.getLogger('agent_comms')
agent_logger.setLevel(logging.INFO)
agent_logger.addHandler(agent_handler)
agent_logger.addHandler(console_handler)

# Log the start of the patched run
agent_logger.info('=== MULTI-AGENT BACKTEST WITH ENHANCED LOGGING STARTED ===')

# Monkey patch key agent classes to add logging
def monkey_patch_agent_framework():
    """Monkey patch the agent framework to add enhanced logging"""
    try:
        # Try to import the agent classes
        agent_logger.info('Attempting to monkey patch agent framework classes...')
        
        # Patch CollaborativeDecisionFramework
        try:
            from agents.collaborative_decision_agent import CollaborativeDecisionFramework
            
            # Store original method
            original_run_decision = CollaborativeDecisionFramework.run_decision_session
            
            # Create patched method
            def patched_run_decision(self, symbol, prompt=None):
                agent_logger.info(f'=== STARTING COLLABORATIVE DECISION SESSION FOR {symbol} ===')
                result = original_run_decision(self, symbol, prompt)
                agent_logger.info(f'=== COMPLETED COLLABORATIVE DECISION SESSION ===')
                if isinstance(result, dict):
                    agent_logger.info(f'Decision: {result.get("decision", "Unknown")}')
                    agent_logger.info(f'Confidence: {result.get("confidence", "Unknown")}')
                    agent_logger.info(f'Reasoning: {result.get("reasoning", "None provided")}')
                return result
            
            # Replace original method
            CollaborativeDecisionFramework.run_decision_session = patched_run_decision
            agent_logger.info('Successfully patched CollaborativeDecisionFramework.run_decision_session')
            
        except (ImportError, AttributeError) as e:
            agent_logger.warning(f'Failed to patch CollaborativeDecisionFramework: {e}')
        
        # Patch DecisionSession
        try:
            from orchestration.decision_session import DecisionSession
            
            # Store original method
            if hasattr(DecisionSession, 'initiate_chat'):
                original_initiate_chat = DecisionSession.initiate_chat
                
                # Create patched method
                def patched_initiate_chat(self, *args, **kwargs):
                    agent_logger.info('=== INITIATING GROUP CHAT ===')
                    result = original_initiate_chat(self, *args, **kwargs)
                    agent_logger.info('=== GROUP CHAT INITIATED ===')
                    return result
                
                # Replace original method
                DecisionSession.initiate_chat = patched_initiate_chat
                agent_logger.info('Successfully patched DecisionSession.initiate_chat')
                
        except (ImportError, AttributeError) as e:
            agent_logger.warning(f'Failed to patch DecisionSession: {e}')
            
        # Patch AutoGen's GroupChatManager
        try:
            # Import AutoGen directly
            import autogen
            
            # Check if initiate_chat exists
            if hasattr(autogen.GroupChatManager, 'initiate_chat'):
                original_autogen_initiate = autogen.GroupChatManager.initiate_chat
                
                # Create patched method
                def patched_autogen_initiate(self, *args, **kwargs):
                    agent_logger.info('=== AUTOGEN INITIATING GROUP CHAT ===')
                    result = original_autogen_initiate(self, *args, **kwargs)
                    agent_logger.info('=== AUTOGEN GROUP CHAT INITIATED ===')
                    return result
                
                # Replace original method
                autogen.GroupChatManager.initiate_chat = patched_autogen_initiate
                agent_logger.info('Successfully patched autogen.GroupChatManager.initiate_chat')
                
            # Also patch the chat method if it exists
            if hasattr(autogen.GroupChat, 'chat'):
                original_autogen_chat = autogen.GroupChat.chat
                
                # Create patched method
                def patched_autogen_chat(self, *args, **kwargs):
                    agent_logger.info('=== AUTOGEN GROUP CHAT STARTED ===')
                    result = original_autogen_chat(self, *args, **kwargs)
                    agent_logger.info('=== AUTOGEN GROUP CHAT COMPLETED ===')
                    return result
                
                # Replace original method
                autogen.GroupChat.chat = patched_autogen_chat
                agent_logger.info('Successfully patched autogen.GroupChat.chat')
                
        except (ImportError, AttributeError) as e:
            agent_logger.warning(f'Failed to patch AutoGen classes: {e}')
            
        agent_logger.info('Monkey patching completed')
        
    except Exception as e:
        agent_logger.error(f'Error in monkey_patch_agent_framework: {e}')

# Export agent logger
__all__ = ['agent_logger', 'monkey_patch_agent_framework']
PYTHONCODE

# Upload our patch to EC2
echo "Uploading agent logging patch to EC2..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no agent_logging_patch.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/

# Create a wrapper script on EC2 to run a backtest with our patch
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cat > /home/ec2-user/aGENtrader/run_with_agent_logging.py << 'PYTHONSCRIPT'
#!/usr/bin/env python3
\"\"\"
Run a backtest with enhanced agent communications logging
\"\"\"
import sys
import os
import importlib.util

# First, load our agent logging patch
spec = importlib.util.spec_from_file_location('agent_logging_patch', 'agent_logging_patch.py')
agent_logging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_logging)

# Apply monkey patches
agent_logging.monkey_patch_agent_framework()

# Now run the actual backtest by importing the module
agent_logging.agent_logger.info('Importing backtest module...')

# Use arguments for backtest settings
if len(sys.argv) < 2:
    # Default to enhanced backtest if no arguments provided
    sys.argv = ['run_with_agent_logging.py', 'run_enhanced_backtest.py', 
                '--symbol', 'BTCUSDT', '--interval', '1h', 
                '--start_date', '2025-03-01', '--end_date', '2025-03-02',
                '--initial_balance', '10000', '--risk_per_trade', '0.02', 
                '--use_local_llm']

# Extract backtest module name from arguments
backtest_module = sys.argv[1]
agent_logging.agent_logger.info(f'Running backtest module: {backtest_module}')

# Shift arguments to match the target script's expectations
sys.argv = [backtest_module] + sys.argv[2:]

try:
    # Run the backtest
    agent_logging.agent_logger.info(f'Running {backtest_module} with arguments: {sys.argv[1:]}')
    
    # Import the backtest module
    if backtest_module.endswith('.py'):
        backtest_module = backtest_module[:-3]
    module = __import__(backtest_module)
    
    # If the module has a main function, call it
    if hasattr(module, 'main'):
        agent_logging.agent_logger.info('Calling main() function...')
        module.main()
    else:
        agent_logging.agent_logger.warning('No main() function found in module')
        
    agent_logging.agent_logger.info('=== BACKTEST COMPLETED ===')
    
except Exception as e:
    agent_logging.agent_logger.error(f'Error running backtest: {e}')
    import traceback
    agent_logging.agent_logger.error(traceback.format_exc())
PYTHONSCRIPT"

# Make the script executable
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "chmod +x /home/ec2-user/aGENtrader/run_with_agent_logging.py"

# Create a shell wrapper to run the backtest
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cat > /home/ec2-user/aGENtrader/run_multi_agent_backtest.sh << 'SHELLSCRIPT'
#!/bin/bash
# Shell wrapper to run a multi-agent backtest with enhanced logging

# Default parameters
BACKTEST_TYPE='run_enhanced_backtest.py'
SYMBOL='BTCUSDT'
INTERVAL='1h'
START_DATE='2025-03-01'
END_DATE='2025-03-02'
BALANCE=10000
RISK=0.02
USE_LOCAL_LLM=true

# Parse command line arguments
while [[ \$# -gt 0 ]]; do
    case \$1 in
        --type)
            case \$2 in
                simplified) BACKTEST_TYPE='run_simplified_backtest.py' ;;
                enhanced) BACKTEST_TYPE='run_enhanced_backtest.py' ;;
                full-scale) BACKTEST_TYPE='run_full_scale_backtest.py' ;;
                *) echo \"Unknown backtest type: \$2\"; exit 1 ;;
            esac
            shift
            ;;
        --symbol) SYMBOL=\"\$2\"; shift ;;
        --interval) INTERVAL=\"\$2\"; shift ;;
        --start_date) START_DATE=\"\$2\"; shift ;;
        --end_date) END_DATE=\"\$2\"; shift ;;
        --balance) BALANCE=\"\$2\"; shift ;;
        --risk) RISK=\"\$2\"; shift ;;
        --use_local_llm) USE_LOCAL_LLM=true ;;
        --use_openai) USE_LOCAL_LLM=false ;;
        *) echo \"Unknown parameter: \$1\"; exit 1 ;;
    esac
    shift
done

# Construct the command
CMD=\"python3 run_with_agent_logging.py \$BACKTEST_TYPE --symbol \$SYMBOL --interval \$INTERVAL --start_date \$START_DATE --end_date \$END_DATE --initial_balance \$BALANCE --risk_per_trade \$RISK\"

# Add local LLM option if enabled
if [ \"\$USE_LOCAL_LLM\" = true ]; then
    CMD=\"\$CMD --use_local_llm\"
fi

# Print the command
echo \"Running: \$CMD\"
echo \"====================================================\"

# Set PYTHONPATH to include current directory
export PYTHONPATH=\${PYTHONPATH:-.}

# Run the command
\$CMD

# Check for agent communications log
echo \"====================================================\"
echo \"Checking for agent communications log...\"
LATEST_LOG=\$(find data/logs -name 'agent_comms_*.log' | sort -r | head -n 1)

if [ -n \"\$LATEST_LOG\" ]; then
    echo \"Agent communications log: \$LATEST_LOG\"
    echo \"Log content:\"
    echo \"====================================================\"
    cat \"\$LATEST_LOG\"
    echo \"====================================================\"
else
    echo \"No agent communications log found.\"
fi
SHELLSCRIPT"

# Make the shell wrapper executable
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "chmod +x /home/ec2-user/aGENtrader/run_multi_agent_backtest.sh"

echo
echo "Solution deployed to EC2."
echo
echo "To run a backtest with visible agent communications, use:"
echo "./ec2-backtest.sh run \"cd /home/ec2-user/aGENtrader && ./run_multi_agent_backtest.sh --type enhanced --start_date 2025-03-01 --end_date 2025-03-02 --use_local_llm\""
echo 
echo "This will run a short backtest (1 day) and show the agent communications in the log."
echo "The solution patches the agent framework to add logging at key points in the agent communication flow."
echo
echo "Let's run a brief test to verify the solution works:"
./ec2-backtest.sh run "cd /home/ec2-user/aGENtrader && ./run_multi_agent_backtest.sh --type simplified --start_date 2025-03-01 --end_date 2025-03-02 --use_local_llm"

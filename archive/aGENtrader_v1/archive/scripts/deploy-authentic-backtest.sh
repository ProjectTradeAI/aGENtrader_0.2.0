#!/bin/bash
# Deploy and run authentic, full-scale multi-agent backtesting

# Set parameters
EC2_IP="51.20.250.135"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Command line arguments
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-20"
END_DATE="2025-03-22"
BALANCE="10000"

while [[ $# -gt 0 ]]; do
  case $1 in
    --symbol)
      SYMBOL="$2"
      shift 2
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --start)
      START_DATE="$2"
      shift 2
      ;;
    --end)
      END_DATE="$2"
      shift 2
      ;;
    --balance)
      BALANCE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create key file if needed
if [ ! -f "$KEY_PATH" ]; then
  echo "Creating EC2 key file..."
  cat > "$KEY_PATH" << 'KEYEOF'
-----BEGIN RSA PRIVATE KEY-----
MIIEoQIBAAKCAQEAyxNT6X+1frDllJPAbCAjOjNV6+IYbJTBJF+NNUESxrYsMK8J
1Dt4OBuXKSMV7nttmb6/jy6tItkztExoPyqr1QuKwHUInkbkKTm15Cl90o6yzXba
UfntOfpwZHwmEOJRVniLRJPzkOldOplyTiIxaf8mZKLeaXDlleaHZlNyrBWs9wNN
gJJbCBve2Z1TJsZeRig3u0Tg0+xo1BPxSm8dROalr8/30UrXpCkDQVL5S3oA2kSd
6hvwQhUZclGNheGgLOGTMtZ/FxGAI/mVsD29ErWnEoysLGCpbLfXpw7o3yEDCND+
cpqtV+ckbTeX2gqbugyZmBVrxcnbafwW1ykoaQIDAQABAoIBAE53gmXn1c5FNgBp
8uEUrefwLBQAAeX6uIKAdUSNh17Gx15sVATwkaxEZO0dRH0orhnJDaWaqIWdnY/e
Mi2uJEUmt49T6WeXBtQzG2g07Awu3UHs2cDxLEvJzCHXorHFcR5TZ6Sw8l0c/swE
vJkaNzO4xjH+iKf/WobIU6sjNVzuNjJF7TNUJ/kZmfZHOjOKCSBF/ahY+weeVBFp
lqaSKrNINPYoYn4nrAgWVxMiPqItWhm3Y9G3c3z9ePNJKRkNKnRB+pCfGS3EZTq0
deI3rcurPsBe34B/SxZF7G1hLVhEtom18YUbZvSBxgCJmI7D239e/Qz6bgqB7FAo
rFJ/S3ECgYEA+oCEP5NjBilqOHSdLLPhI/Ak6pNIK017xMBdiBTjnRh93D8Xzvfh
glkHRisZo8gmIZsgW3izlEeUv4CaVf7OzlOUiu2KmmrLxGHPoT+QPLf/Ak3GZE14
XY9vtaQQSwxM+i5sNtAD/3/KcjH6wT1B+8R4xqtHUYXw7VoEQWRSs/UCgYEAz4hW
j7+ooYlyHzkfuiEMJG0CtKR/fYsd9Zygn+Y6gGQvCiL+skAmx/ymG/qU6D8ZejkN
Azzv7JGQ+1z8OtTNStgDPE7IT74pA0BC60jHySDYzyGAaoMJDhHxA2CPm60EwPDU
5pRVy+FN5LmCCT8oDgcpsPpgjALOqR2TUkcOziUCgYAFXdN3eTTZ4PFBnF3xozjj
iDWCQP1+z/4izOw0Ch6GMwwfN8rOyEiwfi/FtQ6rj5Ihji03SHKwboglQiAMT5Um
nmvEPiqF/Fu5LU9BaRcx9c8kwX3KkE5P0s7V2VnwAad0hKIU2of7ZUV1BNUWZrWP
KzpbJzgz6uaqbw9AR2HuMQJ/YuaWWer8cf8OY9LVS95z6ugIYg4Cs9GYdXQvGASf
3I/h2vLSbiAkWyoL/0lrrUJk4dpOWTyxGgxFC4VErsS7EO/gmtzwmRAGe4YkXfxR
OYhtykgs6pWHuyzRrspVpdrOaSRcUYZfXMoCVP4S+lUewZCoTa8EU7UCx5VQn+U9
KQKBgQDsjVRcsfC/szL7KgeheEN/2zRADix5bqrg0rAB1y+sw+yzkCCh3jcRn2O2
wNIMroggGNy+vcR8Xo/V1wLCsEn45cxB6W7onqxFRM6IkGxkBgdatEL/aBnETSAI
x4C5J+IqaT2T53O2n3DR+GsVoeNUbz8j/lPONNQnV0ZqHRVWpA==
-----END RSA PRIVATE KEY-----
KEYEOF
  chmod 600 "$KEY_PATH"
fi

# Get environment variables
DB_URL=$(node -e "console.log(process.env.DATABASE_URL || '')")
ALPACA_API_KEY=$(node -e "console.log(process.env.ALPACA_API_KEY || '')")
ALPACA_API_SECRET=$(node -e "console.log(process.env.ALPACA_API_SECRET || '')")
OPENAI_API_KEY=$(node -e "console.log(process.env.OPENAI_API_KEY || '')")

# Format timestamp for log files
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")
LOG_FILE="authentic-backtest-$TIMESTAMP.log"

echo "📈 Deploying Authentic Full-Scale Multi-Agent Backtesting" | tee "$LOG_FILE"
echo "Symbol: $SYMBOL, Interval: $INTERVAL, Date Range: $START_DATE to $END_DATE" | tee -a "$LOG_FILE"
echo "-----------------------------------------------------" | tee -a "$LOG_FILE"

# Test EC2 connection
echo "Testing EC2 connection..." | tee -a "$LOG_FILE"
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'" >> "$LOG_FILE" 2>&1; then
  echo "Failed to connect to EC2. Please check your connection settings." | tee -a "$LOG_FILE"
  exit 1
fi
echo "✅ EC2 connection successful" | tee -a "$LOG_FILE"

# Verify directory structure on EC2
echo "Verifying directory structure on EC2..." | tee -a "$LOG_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "mkdir -p $EC2_DIR/orchestration $EC2_DIR/utils/test_logging $EC2_DIR/utils/decision_tracker $EC2_DIR/agents $EC2_DIR/data/logs" >> "$LOG_FILE" 2>&1

# Create the authentic logging bridge that doesn't introduce any simulated data
cat > authentic_logging_bridge.py << 'EOF'
#!/usr/bin/env python3
"""
Authentic Agent Communications Logging Bridge

This module provides logging capabilities for agent communications
without introducing any simulated or hard-coded responses.
It simply captures and logs the authentic agent communications.
"""
import os
import sys
import logging
from datetime import datetime
import inspect

# Configure base logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("authentic_logging")

# Create agent communications logger
agent_log_dir = os.path.join('data', 'logs')
os.makedirs(agent_log_dir, exist_ok=True)
agent_log_file = os.path.join(agent_log_dir, f'authentic_agent_comms_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

agent_logger = logging.getLogger('agent_comms')
agent_logger.setLevel(logging.INFO)

# Add file handler
file_handler = logging.FileHandler(agent_log_file)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - AGENT - %(message)s')
file_handler.setFormatter(file_formatter)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('>>> AGENT: %(message)s')
console_handler.setFormatter(console_formatter)

agent_logger.addHandler(file_handler)
agent_logger.addHandler(console_handler)

logger.info(f"Agent communications will be logged to: {agent_log_file}")

def setup_logging_bridge():
    """
    Setup the logging bridge for the decision session without adding any simulated responses.
    This only captures authentic communications from the existing framework.
    """
    logger.info("Setting up authentic agent communications logging bridge")
    
    # Try to import the decision session module
    try:
        from orchestration.decision_session import DecisionSession
        logger.info("Successfully imported DecisionSession class")
        
        # Store reference to original methods that might contain agent communications
        original_methods = {}
        
        # Find methods that might contain agent communications
        methods_to_patch = [
            'run_session',
            'initiate_chat',
            '_run_agent_session'
        ]
        
        # Additional methods that might exist in the class
        for name, method in inspect.getmembers(DecisionSession, predicate=inspect.isfunction):
            if 'agent' in name.lower() or 'chat' in name.lower() or 'decision' in name.lower():
                if name not in methods_to_patch:
                    methods_to_patch.append(name)
        
        logger.info(f"Methods that will be monitored for agent communications: {methods_to_patch}")
        
        # Create patched versions of the methods
        patched_methods = []
        
        # Patch run_session method if it exists
        if hasattr(DecisionSession, 'run_session'):
            original_methods['run_session'] = DecisionSession.run_session
            
            def patched_run_session(self, *args, **kwargs):
                # Log the start of the session with available parameters
                symbol = kwargs.get('symbol', getattr(self, 'symbol', None))
                if args and len(args) > 0:
                    first_arg = args[0]
                    if isinstance(first_arg, str):
                        # Assume first arg is symbol if it's a string
                        symbol = first_arg
                
                current_price = kwargs.get('current_price', None)
                agent_logger.info(f"=== STARTING AUTHENTIC DECISION SESSION FOR {symbol} ===")
                
                # Call original method to get authentic response
                result = original_methods['run_session'](self, *args, **kwargs)
                
                # Log the decision result without adding simulated content
                if isinstance(result, dict):
                    status = result.get('status', 'unknown')
                    agent_logger.info(f"Session status: {status}")
                    
                    if 'decision' in result:
                        decision = result['decision']
                        if isinstance(decision, dict):
                            action = decision.get('action', 'UNKNOWN')
                            confidence = decision.get('confidence', 0)
                            reasoning = decision.get('reasoning', 'No reasoning provided')
                            
                            agent_logger.info(f"Decision: {action} with {confidence*100:.0f}% confidence")
                            agent_logger.info(f"Reasoning: {reasoning}")
                
                agent_logger.info(f"=== COMPLETED AUTHENTIC DECISION SESSION FOR {symbol} ===")
                return result
            
            # Apply the patch
            DecisionSession.run_session = patched_run_session
            patched_methods.append('run_session')
            logger.info("Successfully patched DecisionSession.run_session")
        
        # Patch _run_agent_session method if it exists
        if hasattr(DecisionSession, '_run_agent_session'):
            original_methods['_run_agent_session'] = DecisionSession._run_agent_session
            
            def patched_run_agent_session(self, *args, **kwargs):
                agent_type = kwargs.get('agent_type', 'Unknown')
                agent_logger.info(f"Running agent session for agent type: {agent_type}")
                
                # Call original method to get authentic response
                result = original_methods['_run_agent_session'](self, *args, **kwargs)
                
                # Log the result without adding simulated content
                if result:
                    agent_logger.info(f"Agent session completed for {agent_type}")
                    if isinstance(result, str):
                        # If result is a string, it's likely the agent's response
                        agent_logger.info(f"{agent_type}: {result}")
                    elif isinstance(result, dict):
                        # If result is a dict, try to extract readable content
                        for key, value in result.items():
                            agent_logger.info(f"{agent_type} - {key}: {value}")
                
                return result
            
            # Apply the patch
            DecisionSession._run_agent_session = patched_run_agent_session
            patched_methods.append('_run_agent_session')
            logger.info("Successfully patched DecisionSession._run_agent_session")
        
        # Patch initiate_chat method if it exists
        if hasattr(DecisionSession, 'initiate_chat'):
            original_methods['initiate_chat'] = DecisionSession.initiate_chat
            
            def patched_initiate_chat(self, *args, **kwargs):
                agent_logger.info("Initiating agent group chat")
                
                # Call original method to get authentic response
                result = original_methods['initiate_chat'](self, *args, **kwargs)
                
                # Log completion without adding simulated content
                agent_logger.info("Agent group chat completed")
                
                return result
            
            # Apply the patch
            DecisionSession.initiate_chat = patched_initiate_chat
            patched_methods.append('initiate_chat')
            logger.info("Successfully patched DecisionSession.initiate_chat")
        
        # Try to patch AutoGen components if available
        try:
            import autogen
            logger.info("Found AutoGen module, patching AutoGen components")
            
            # Patch GroupChatManager if available
            if hasattr(autogen, 'GroupChatManager'):
                if hasattr(autogen.GroupChatManager, 'initiate_chat'):
                    original_autogen_initiate = autogen.GroupChatManager.initiate_chat
                    
                    def patched_autogen_initiate(self, *args, **kwargs):
                        agent_logger.info("AutoGen group chat initiated")
                        if hasattr(self, 'groupchat') and hasattr(self.groupchat, 'agents'):
                            agent_names = [getattr(agent, 'name', str(agent)) for agent in self.groupchat.agents]
                            agent_logger.info(f"Participating agents: {', '.join(agent_names)}")
                        
                        # Call original method
                        result = original_autogen_initiate(self, *args, **kwargs)
                        
                        agent_logger.info("AutoGen group chat completed")
                        return result
                    
                    # Apply the patch
                    autogen.GroupChatManager.initiate_chat = patched_autogen_initiate
                    logger.info("Successfully patched autogen.GroupChatManager.initiate_chat")
            
            # Patch ConversableAgent if available
            if hasattr(autogen, 'ConversableAgent'):
                if hasattr(autogen.ConversableAgent, 'generate_reply'):
                    original_generate_reply = autogen.ConversableAgent.generate_reply
                    
                    def patched_generate_reply(self, *args, **kwargs):
                        # Extract agent name
                        agent_name = getattr(self, 'name', str(self))
                        
                        # Extract message content if available
                        message = "No message content available"
                        if args and isinstance(args[0], list) and len(args[0]) > 0:
                            last_message = args[0][-1]
                            if isinstance(last_message, dict) and 'content' in last_message:
                                message = last_message['content'][:100] + "..." if len(last_message['content']) > 100 else last_message['content']
                        
                        agent_logger.info(f"Agent {agent_name} generating reply to: {message}")
                        
                        # Call original method
                        result = original_generate_reply(self, *args, **kwargs)
                        
                        # Log the reply if it's not None
                        if result:
                            reply = result[:100] + "..." if len(result) > 100 else result
                            agent_logger.info(f"Agent {agent_name} replied: {reply}")
                        
                        return result
                    
                    # Apply the patch
                    autogen.ConversableAgent.generate_reply = patched_generate_reply
                    logger.info("Successfully patched autogen.ConversableAgent.generate_reply")
            
        except ImportError:
            logger.info("AutoGen module not found, skipping AutoGen patches")
        
        if patched_methods:
            logger.info(f"Successfully patched {len(patched_methods)} methods for agent communications logging")
            return {
                "success": True,
                "patched_methods": patched_methods,
                "log_file": agent_log_file
            }
        else:
            logger.warning("No methods were patched for agent communications logging")
            return {
                "success": False,
                "error": "No methods were patched",
                "log_file": agent_log_file
            }
    
    except ImportError as e:
        logger.error(f"Failed to import DecisionSession: {e}")
        return {
            "success": False,
            "error": f"Import error: {e}",
            "log_file": agent_log_file
        }
    except Exception as e:
        logger.error(f"Error setting up logging bridge: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "log_file": agent_log_file
        }

# Function to create the authentic backtest runner
def create_authentic_backtest_runner():
    """Create the authentic backtest runner script"""
    script_path = "run_authentic_backtest.py"
    
    with open(script_path, "w") as f:
        f.write("""#!/usr/bin/env python3
"""
Authentic Multi-Agent Backtest Runner

This script runs a backtest using the authentic agent framework without
any simulated or hard-coded responses.
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'data/logs/authentic_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("authentic_backtest")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run authentic multi-agent backtest")
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--interval', type=str, default='1h', help='Time interval')
    parser.add_argument('--start_date', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial_balance', type=float, default=10000.0, help='Initial balance')
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    logger.info(f"Starting authentic multi-agent backtest for {args.symbol} {args.interval}")
    logger.info(f"Period: {args.start_date} to {args.end_date}")
    
    # Set up the authentic logging bridge
    try:
        import authentic_logging_bridge
        result = authentic_logging_bridge.setup_logging_bridge()
        
        if result['success']:
            logger.info(f"Authentic logging bridge setup successful: {result['patched_methods']}")
            logger.info(f"Agent communications will be logged to: {result['log_file']}")
        else:
            logger.warning(f"Authentic logging bridge setup failed: {result['error']}")
            logger.info(f"Will continue with backtest but agent communications may not be logged")
    except ImportError:
        logger.error("Failed to import authentic_logging_bridge module")
        logger.info("Will continue with backtest but agent communications will not be logged")
    
    # Run the authentic backtest
    try:
        from backtesting.core import authentic_backtest
        
        # Check if the module has a main function
        if hasattr(authentic_backtest, 'main'):
            logger.info("Running authentic_backtest.main()")
            # Create sys.argv for the main function
            sys.argv = [
                'authentic_backtest.py',
                '--symbol', args.symbol,
                '--interval', args.interval,
                '--start_date', args.start_date,
                '--end_date', args.end_date,
                '--initial_balance', str(args.initial_balance)
            ]
            authentic_backtest.main()
        else:
            # If no main function, call the module directly
            logger.info("Calling authentic_backtest module directly")
            cmd = f"python -m backtesting.core.authentic_backtest --symbol {args.symbol} --interval {args.interval} --start_date {args.start_date} --end_date {args.end_date} --initial_balance {args.initial_balance}"
            logger.info(f"Running command: {cmd}")
            exit_code = os.system(cmd)
            logger.info(f"Command completed with exit code: {exit_code}")
    except ImportError as e:
        logger.error(f"Failed to import authentic_backtest module: {e}")
    except Exception as e:
        logger.error(f"Error running authentic backtest: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
""")
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    logger.info(f"Created authentic backtest runner at {script_path}")
    return script_path

# Create the authentic runner script
runner_script = create_authentic_backtest_runner()

# Function to generate runner shell script
def create_runner_shell_script():
    """Create the shell script to run the authentic backtest"""
    script_path = "run_authentic_backtest.sh"
    
    with open(script_path, "w") as f:
        f.write(f"""#!/bin/bash
# Runner script for authentic multi-agent backtest

# Set Python path to include the current directory
export PYTHONPATH="\${{PYTHONPATH}}:\$(pwd)"
echo "PYTHONPATH set to: \$PYTHONPATH"

# Run the authentic backtest
echo "Starting authentic multi-agent backtest..."
python3 run_authentic_backtest.py \\
  --symbol "{SYMBOL}" \\
  --interval "{INTERVAL}" \\
  --start_date "{START_DATE}" \\
  --end_date "{END_DATE}" \\
  --initial_balance "{BALANCE}"

# Check for result files
echo "Checking for result files..."
LATEST_RESULT=\$(find results -name "*backtest*.json" | sort -r | head -n 1)

if [ -n "\$LATEST_RESULT" ]; then
  echo "Found result file: \$LATEST_RESULT"
  echo "Backtest results:"
  cat "\$LATEST_RESULT" | python -m json.tool
else
  echo "No result file found."
fi

# Check for agent communications log
echo "Checking for agent communications log..."
LATEST_LOG=\$(find data/logs -name "authentic_agent_comms_*.log" | sort -r | head -n 1)

if [ -n "\$LATEST_LOG" ]; then
  echo "Found agent communications log: \$LATEST_LOG"
  echo "Agent communications log content:"
  cat "\$LATEST_LOG"
else
  echo "No agent communications log found."
fi
""")
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    logger.info(f"Created runner shell script at {script_path}")
    return script_path

# Create the runner shell script
shell_script = create_runner_shell_script()

# Upload files to EC2
echo "Uploading files to EC2..." | tee -a "$LOG_FILE"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no authentic_logging_bridge.py "$SSH_USER@$EC2_IP:$EC2_DIR/authentic_logging_bridge.py" >> "$LOG_FILE" 2>&1
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no run_authentic_backtest.py "$SSH_USER@$EC2_IP:$EC2_DIR/run_authentic_backtest.py" >> "$LOG_FILE" 2>&1
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no run_authentic_backtest.sh "$SSH_USER@$EC2_IP:$EC2_DIR/run_authentic_backtest.sh" >> "$LOG_FILE" 2>&1

# Make scripts executable on EC2
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/run_authentic_backtest.py $EC2_DIR/run_authentic_backtest.sh" >> "$LOG_FILE" 2>&1

# Run the authentic backtest on EC2
echo "Running authentic multi-agent backtest on EC2..." | tee -a "$LOG_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' ./run_authentic_backtest.sh" | tee -a "$LOG_FILE"

# Check for agent communications logs
echo "Checking for agent communications logs on EC2..." | tee -a "$LOG_FILE"
AGENT_LOGS=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "find $EC2_DIR/data/logs -name 'authentic_agent_comms_*.log' | sort -r | head -n 3")

if [ -n "$AGENT_LOGS" ]; then
  echo "Found agent communications logs:" | tee -a "$LOG_FILE"
  echo "$AGENT_LOGS" | tee -a "$LOG_FILE"
  
  # Download the most recent log
  MOST_RECENT=$(echo "$AGENT_LOGS" | head -n 1)
  
  if [ -n "$MOST_RECENT" ]; then
    echo "Downloading most recent agent communications log..." | tee -a "$LOG_FILE"
    mkdir -p ./results/logs
    LOCAL_LOG="./results/logs/$(basename $MOST_RECENT)"
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$MOST_RECENT" "$LOCAL_LOG" >> "$LOG_FILE" 2>&1
    
    if [ -f "$LOCAL_LOG" ]; then
      echo "✅ Agent communications log downloaded to: $LOCAL_LOG" | tee -a "$LOG_FILE"
    fi
  fi
else
  echo "No agent communications logs found" | tee -a "$LOG_FILE"
fi

# Check for result files
echo "Checking for result files on EC2..." | tee -a "$LOG_FILE"
RESULT_FILES=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "find $EC2_DIR/results -name '*backtest*.json' -mmin -30 | sort -r | head -n 3")

if [ -n "$RESULT_FILES" ]; then
  echo "Found recent result files:" | tee -a "$LOG_FILE"
  echo "$RESULT_FILES" | tee -a "$LOG_FILE"
  
  # Download the most recent result file
  MOST_RECENT=$(echo "$RESULT_FILES" | head -n 1)
  
  if [ -n "$MOST_RECENT" ]; then
    echo "Downloading most recent result file..." | tee -a "$LOG_FILE"
    mkdir -p ./results
    LOCAL_RESULT="./results/$(basename $MOST_RECENT)"
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$MOST_RECENT" "$LOCAL_RESULT" >> "$LOG_FILE" 2>&1
    
    if [ -f "$LOCAL_RESULT" ]; then
      echo "✅ Result file downloaded to: $LOCAL_RESULT" | tee -a "$LOG_FILE"
      
      # Display result summary
      echo -e "\n📈 BACKTEST RESULTS SUMMARY" | tee -a "$LOG_FILE"
      echo "=========================" | tee -a "$LOG_FILE"
      python3 -c "
import json
import sys

try:
    with open('$LOCAL_RESULT', 'r') as f:
        data = json.load(f)
    
    print(f\"Symbol: {data.get('symbol')}\")
    print(f\"Interval: {data.get('interval')}\")
    print(f\"Period: {data.get('start_date')} to {data.get('end_date')}\")
    
    metrics = data.get('performance_metrics', {})
    print(f\"\\nPerformance Metrics:\")
    print(f\"Initial Balance: \${metrics.get('initial_balance', 0):.2f}\")
    print(f\"Final Equity: \${metrics.get('final_equity', 0):.2f}\")
    print(f\"Total Return: {metrics.get('total_return_pct', 0):.2f}%\")
    print(f\"Win Rate: {metrics.get('win_rate', 0):.2f}% ({metrics.get('winning_trades', 0)}/{metrics.get('total_trades', 0)})\")
    print(f\"Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%\")
except Exception as e:
    print(f\"Error reading result file: {e}\")
" | tee -a "$LOG_FILE"
    fi
  fi
else
  echo "No recent result files found" | tee -a "$LOG_FILE"
fi

echo -e "\n✅ Authentic multi-agent backtest completed" | tee -a "$LOG_FILE"
echo "Log file saved to: $LOG_FILE" | tee -a "$LOG_FILE"

# Clean up local files
rm -f authentic_logging_bridge.py run_authentic_backtest.py run_authentic_backtest.sh
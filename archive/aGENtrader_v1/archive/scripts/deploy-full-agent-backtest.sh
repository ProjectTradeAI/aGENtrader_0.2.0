#!/bin/bash
# Deploy and run full-scale multi-agent backtesting with comprehensive monitoring

# Set parameters
EC2_IP="51.20.250.135"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Command line arguments
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-04-01"
END_DATE="2025-04-10"
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
LOG_FILE="full-agent-backtest-$TIMESTAMP.log"

echo "🚀 Deploying Full Multi-Agent Backtesting System" | tee "$LOG_FILE"
echo "Symbol: $SYMBOL, Interval: $INTERVAL, Date Range: $START_DATE to $END_DATE" | tee -a "$LOG_FILE"
echo "---------------------------------------------------" | tee -a "$LOG_FILE"

# Test EC2 connection
echo "Testing EC2 connection..." | tee -a "$LOG_FILE"
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'" >> "$LOG_FILE" 2>&1; then
  echo "Failed to connect to EC2. Please check your connection settings." | tee -a "$LOG_FILE"
  exit 1
fi
echo "✅ EC2 connection successful" | tee -a "$LOG_FILE"

# Create full agent logging system
cat > agent_log_patch.py << 'EOF'
#!/usr/bin/env python3
"""
Agent Logging Patch for Multi-Agent Backtesting Framework

This script enhances logging of agent communications in the backtesting system.
It records all communications between agents without introducing any simulated data.
"""
import os
import sys
import logging
import inspect
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_log_patch")

# Create a dedicated logger for agent communications
agent_log_dir = os.path.join('data', 'logs')
os.makedirs(agent_log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
agent_log_file = os.path.join(agent_log_dir, f'full_agent_comms_{timestamp}.log')

agent_logger = logging.getLogger('agent_comms')
agent_logger.setLevel(logging.INFO)
agent_logger.propagate = False  # Don't propagate to parent logger

# File handler
file_handler = logging.FileHandler(agent_log_file)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
agent_logger.addHandler(file_handler)

# Console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('>>> AGENT: %(message)s')
console_handler.setFormatter(console_formatter)
agent_logger.addHandler(console_handler)

logger.info(f"Agent communications will be logged to: {agent_log_file}")

def patch_decision_session():
    """Patch the DecisionSession class to add logging"""
    try:
        from orchestration.decision_session import DecisionSession
        logger.info("Found DecisionSession class for patching")
        
        # Store references to original methods
        original_methods = {}
        
        # Patch run_session method
        if hasattr(DecisionSession, 'run_session'):
            original_methods['run_session'] = DecisionSession.run_session
            
            def patched_run_session(self, *args, **kwargs):
                """Patched run_session method with enhanced logging"""
                # Get parameters
                symbol = kwargs.get('symbol', None)
                current_price = kwargs.get('current_price', None)
                
                # Try to get symbol from positional args or self
                if symbol is None and args and len(args) > 0 and isinstance(args[0], str):
                    symbol = args[0]
                if symbol is None and hasattr(self, 'symbol'):
                    symbol = self.symbol
                
                # Log start of session
                agent_logger.info(f"===== STARTING DECISION SESSION FOR {symbol} =====")
                if current_price is not None:
                    agent_logger.info(f"Current price: ${current_price}")
                
                # Call original method
                result = original_methods['run_session'](self, *args, **kwargs)
                
                # Log the decision without altering anything
                if isinstance(result, dict):
                    session_id = result.get('session_id', 'unknown')
                    agent_logger.info(f"Session ID: {session_id}")
                    
                    if 'decision' in result:
                        decision = result['decision']
                        if isinstance(decision, dict):
                            action = decision.get('action', 'unknown')
                            confidence = decision.get('confidence', 0)
                            agent_logger.info(f"Decision: {action.upper()} with {confidence*100:.1f}% confidence")
                            
                            reasoning = decision.get('reasoning', '')
                            if reasoning:
                                agent_logger.info(f"Reasoning: {reasoning}")
                
                # Log end of session
                agent_logger.info(f"===== COMPLETED DECISION SESSION FOR {symbol} =====")
                return result
            
            # Apply patch
            DecisionSession.run_session = patched_run_session
            logger.info("Successfully patched DecisionSession.run_session")
        
        # Patch initiate_chat method
        if hasattr(DecisionSession, 'initiate_chat'):
            original_methods['initiate_chat'] = DecisionSession.initiate_chat
            
            def patched_initiate_chat(self, *args, **kwargs):
                """Patched initiate_chat method with enhanced logging"""
                agent_logger.info("Initiating multi-agent chat session")
                
                # Extract agents if available
                if hasattr(self, 'agents') and self.agents:
                    agent_names = [getattr(agent, 'name', str(agent)) for agent in self.agents]
                    agent_logger.info(f"Participating agents: {', '.join(agent_names)}")
                
                # Call original method
                result = original_methods['initiate_chat'](self, *args, **kwargs)
                
                agent_logger.info("Multi-agent chat session completed")
                return result
            
            # Apply patch
            DecisionSession.initiate_chat = patched_initiate_chat
            logger.info("Successfully patched DecisionSession.initiate_chat")
        
        # Patch _run_agent_session method if it exists
        if hasattr(DecisionSession, '_run_agent_session'):
            original_methods['_run_agent_session'] = DecisionSession._run_agent_session
            
            def patched_run_agent_session(self, *args, **kwargs):
                """Patched _run_agent_session method with enhanced logging"""
                agent_type = kwargs.get('agent_type', 'Unknown')
                agent_logger.info(f"Running {agent_type} agent session")
                
                # Call original method
                result = original_methods['_run_agent_session'](self, *args, **kwargs)
                
                # Log result without altering it
                if result:
                    if isinstance(result, str):
                        agent_logger.info(f"{agent_type} response: {result[:100]}...")
                    elif isinstance(result, dict):
                        agent_logger.info(f"{agent_type} response: {str(result)[:100]}...")
                
                return result
            
            # Apply patch
            DecisionSession._run_agent_session = patched_run_agent_session
            logger.info("Successfully patched DecisionSession._run_agent_session")
        
        return {
            "success": True,
            "patched_methods": list(original_methods.keys()),
            "log_file": agent_log_file
        }
    
    except ImportError as e:
        logger.error(f"Failed to import DecisionSession: {e}")
        return {
            "success": False,
            "error": f"ImportError: {e}",
            "log_file": agent_log_file
        }
    except Exception as e:
        logger.error(f"Error patching DecisionSession: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "log_file": agent_log_file
        }

def patch_agent_framework():
    """Patch the broader agent framework classes"""
    try:
        # Try to patch AutoGen components if available
        success = False
        
        try:
            import autogen
            logger.info("Found AutoGen module, patching AutoGen components")
            
            # Patch GroupChatManager
            if hasattr(autogen, 'GroupChatManager'):
                # Patch initiate_chat method
                if hasattr(autogen.GroupChatManager, 'initiate_chat'):
                    original_initiate = autogen.GroupChatManager.initiate_chat
                    
                    def patched_initiate_chat(self, *args, **kwargs):
                        """Patched GroupChatManager.initiate_chat with enhanced logging"""
                        agent_logger.info("Starting AutoGen group chat")
                        
                        # Extract agent names if available
                        if hasattr(self, 'groupchat') and hasattr(self.groupchat, 'agents'):
                            agent_names = [getattr(agent, 'name', str(agent)) for agent in self.groupchat.agents]
                            agent_logger.info(f"Participating agents: {', '.join(agent_names)}")
                        
                        # Call original method
                        result = original_initiate(self, *args, **kwargs)
                        
                        agent_logger.info("AutoGen group chat completed")
                        return result
                    
                    # Apply patch
                    autogen.GroupChatManager.initiate_chat = patched_initiate_chat
                    logger.info("Successfully patched autogen.GroupChatManager.initiate_chat")
                    success = True
            
            # Patch ConversableAgent
            if hasattr(autogen, 'ConversableAgent'):
                # Patch generate_reply method
                if hasattr(autogen.ConversableAgent, 'generate_reply'):
                    original_generate = autogen.ConversableAgent.generate_reply
                    
                    def patched_generate_reply(self, *args, **kwargs):
                        """Patched ConversableAgent.generate_reply with enhanced logging"""
                        agent_name = getattr(self, 'name', str(self))
                        
                        # Extract message if available
                        message = ""
                        if args and len(args) > 0 and isinstance(args[0], list) and args[0]:
                            last_message = args[0][-1]
                            if isinstance(last_message, dict) and 'content' in last_message:
                                message = last_message['content']
                                # Truncate long messages
                                if len(message) > 100:
                                    message = message[:100] + "..."
                        
                        agent_logger.info(f"Agent {agent_name} generating reply to: {message}")
                        
                        # Call original method
                        result = original_generate(self, *args, **kwargs)
                        
                        # Log result without altering it
                        if result:
                            # Truncate long replies
                            reply = result
                            if len(reply) > 100:
                                reply = reply[:100] + "..."
                            agent_logger.info(f"Agent {agent_name} replied: {reply}")
                        
                        return result
                    
                    # Apply patch
                    autogen.ConversableAgent.generate_reply = patched_generate_reply
                    logger.info("Successfully patched autogen.ConversableAgent.generate_reply")
                    success = True
            
            return {
                "success": success,
                "module": "autogen",
                "log_file": agent_log_file
            }
        
        except ImportError:
            logger.info("AutoGen module not found, skipping AutoGen patches")
            return {
                "success": False,
                "error": "AutoGen module not found",
                "log_file": agent_log_file
            }
    
    except Exception as e:
        logger.error(f"Error patching agent framework: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "log_file": agent_log_file
        }

def patch_all():
    """Patch all relevant components of the agent framework"""
    results = {}
    
    # Patch DecisionSession
    session_result = patch_decision_session()
    results['decision_session'] = session_result
    
    # Patch AutoGen components
    autogen_result = patch_agent_framework()
    results['autogen'] = autogen_result
    
    # Overall success status
    results['success'] = session_result.get('success', False) or autogen_result.get('success', False)
    results['log_file'] = agent_log_file
    
    # Log results
    if results['success']:
        logger.info("Successfully patched at least one component of the agent framework")
        patched_components = []
        if session_result.get('success', False):
            patched_components.append("DecisionSession")
        if autogen_result.get('success', False):
            patched_components.append("AutoGen")
        logger.info(f"Patched components: {', '.join(patched_components)}")
    else:
        logger.warning("No components were successfully patched")
    
    return results

if __name__ == "__main__":
    logger.info("Starting agent logging patch")
    results = patch_all()
    
    if results['success']:
        logger.info(f"✅ Agent logging setup complete. Communications will be logged to: {results['log_file']}")
    else:
        logger.error("❌ Failed to set up agent logging patch")
        # Get all error messages
        errors = []
        if 'decision_session' in results and not results['decision_session'].get('success', False):
            errors.append(results['decision_session'].get('error', 'Unknown error in DecisionSession patching'))
        if 'autogen' in results and not results['autogen'].get('success', False):
            errors.append(results['autogen'].get('error', 'Unknown error in AutoGen patching'))
        
        if errors:
            logger.error(f"Errors encountered: {', '.join(errors)}")
EOF

# Create the full agent backtest runner
cat > full_agent_backtest.py << 'EOF'
#!/usr/bin/env python3
"""
Full Agent Backtesting Script

This script runs a full-scale backtest with the multi-agent trading framework,
recording all authentic agent communications.
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
        logging.FileHandler(f'full_agent_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("full_agent_backtest")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run a full-scale agent-based backtest")
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--interval', type=str, default='1h', help='Time interval')
    parser.add_argument('--start_date', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial_balance', type=float, default=10000.0, help='Initial balance')
    parser.add_argument('--output_dir', type=str, default='results', help='Output directory')
    return parser.parse_args()

def setup_agent_logging():
    """Set up agent communications logging"""
    try:
        logger.info("Setting up agent communications logging")
        import agent_log_patch
        result = agent_log_patch.patch_all()
        
        if result['success']:
            logger.info(f"Agent logging setup successful, communications will be logged to: {result['log_file']}")
            return result['log_file']
        else:
            logger.warning("Agent logging setup failed, continuing without agent communications logging")
            return None
    except ImportError:
        logger.error("Failed to import agent_log_patch module")
        return None
    except Exception as e:
        logger.error(f"Error setting up agent logging: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def run_backtest(args):
    """Run the actual backtest"""
    logger.info(f"Running full agent backtest for {args.symbol} {args.interval}")
    logger.info(f"Period: {args.start_date} to {args.end_date}")
    
    # Ensure the output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Output file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(args.output_dir, f"full_agent_backtest_{args.symbol}_{args.interval}_{timestamp}.json")
    
    try:
        # Import the authentic backtest module
        from backtesting.core import authentic_backtest
        logger.info("Successfully imported authentic_backtest module")
        
        # Run the backtest
        if hasattr(authentic_backtest, 'main'):
            logger.info("Running authentic_backtest.main()")
            
            # Check available parameters for authentic_backtest
            import inspect
            if hasattr(authentic_backtest, 'parse_args'):
                arg_spec = inspect.getfullargspec(authentic_backtest.parse_args)
                logger.info(f"Available parameters for authentic_backtest: {arg_spec.args}")
                
                # Check if 'output_dir' or 'output_file' is in the parameters
                has_output_dir = 'output_dir' in arg_spec.args
                has_output_file = 'output_file' in arg_spec.args
                
                # Create appropriate sys.argv based on available parameters
                sys.argv = [
                    'authentic_backtest.py',
                    '--symbol', args.symbol,
                    '--interval', args.interval,
                    '--start_date', args.start_date,
                    '--end_date', args.end_date,
                    '--initial_balance', str(args.initial_balance)
                ]
                
                # Add appropriate output parameter
                if has_output_file:
                    sys.argv.extend(['--output_file', output_file])
                elif has_output_dir:
                    sys.argv.extend(['--output_dir', args.output_dir])
            else:
                # If we can't inspect, use conservative parameters
                sys.argv = [
                    'authentic_backtest.py',
                    '--symbol', args.symbol,
                    '--interval', args.interval,
                    '--start_date', args.start_date,
                    '--end_date', args.end_date,
                    '--initial_balance', str(args.initial_balance),
                    '--output_dir', args.output_dir
                ]
            
            # Log the actual command we're running
            logger.info(f"Running with arguments: {' '.join(sys.argv)}")
            
            # Run the backtest
            authentic_backtest.main()
            
            # Try to find the output file
            result_files = []
            for root, dirs, files in os.walk(args.output_dir):
                for file in files:
                    if file.endswith(".json") and args.symbol in file and "backtest" in file:
                        result_files.append(os.path.join(root, file))
            
            # Sort by modification time (newest first)
            result_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            if result_files:
                output_file = result_files[0]
                logger.info(f"Found result file: {output_file}")
                return output_file
            else:
                logger.warning("No result file found after backtest")
                return None
        else:
            # If no main function, try to run the backtest directly
            logger.info("Running authentic_backtest module directly")
            cmd = f"python -m backtesting.core.authentic_backtest --symbol {args.symbol} --interval {args.interval} --start_date {args.start_date} --end_date {args.end_date} --initial_balance {args.initial_balance} --output_dir {args.output_dir}"
            logger.info(f"Executing command: {cmd}")
            exit_code = os.system(cmd)
            
            if exit_code == 0:
                # Try to find the output file
                result_files = []
                for file in os.listdir(args.output_dir):
                    if file.endswith(".json") and args.symbol in file and "backtest" in file:
                        result_files.append(os.path.join(args.output_dir, file))
                
                # Sort by modification time (newest first)
                result_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                if result_files:
                    output_file = result_files[0]
                    logger.info(f"Found result file: {output_file}")
                    return output_file
                else:
                    logger.warning("No result file found after backtest")
                    return None
            else:
                logger.error(f"Backtest failed with exit code: {exit_code}")
                return None
    except ImportError as e:
        logger.error(f"Failed to import authentic_backtest module: {e}")
        return None
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_args()
    
    # Set up agent communications logging
    agent_log_file = setup_agent_logging()
    
    if agent_log_file:
        logger.info(f"Agent communications will be logged to: {agent_log_file}")
    
    # Run the backtest
    output_file = run_backtest(args)
    
    if output_file and os.path.exists(output_file):
        logger.info(f"Backtest completed successfully, results saved to: {output_file}")
        
        # Display summary of results
        try:
            with open(output_file, 'r') as f:
                results = json.load(f)
            
            logger.info("=== Backtest Results Summary ===")
            logger.info(f"Symbol: {results.get('symbol')}")
            logger.info(f"Interval: {results.get('interval')}")
            logger.info(f"Period: {results.get('start_date')} to {results.get('end_date')}")
            
            metrics = results.get('performance_metrics', {})
            logger.info(f"Initial Balance: ${metrics.get('initial_balance', 0):.2f}")
            logger.info(f"Final Equity: ${metrics.get('final_equity', 0):.2f}")
            logger.info(f"Total Return: {metrics.get('total_return_pct', 0):.2f}%")
            logger.info(f"Total Trades: {metrics.get('total_trades', 0)}")
            logger.info(f"Win Rate: {metrics.get('win_rate', 0):.2f}%")
            logger.info(f"Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
            
            # Save summary to a separate file
            summary_file = os.path.join(args.output_dir, f"summary_{os.path.basename(output_file)}")
            with open(summary_file, 'w') as f:
                json.dump({
                    'symbol': results.get('symbol'),
                    'interval': results.get('interval'),
                    'start_date': results.get('start_date'),
                    'end_date': results.get('end_date'),
                    'performance_metrics': metrics
                }, f, indent=2)
            
            logger.info(f"Summary saved to: {summary_file}")
        except Exception as e:
            logger.error(f"Error displaying results summary: {e}")
    else:
        logger.error("Backtest failed or output file not found")

if __name__ == "__main__":
    main()
EOF

# Create runner shell script
cat > run-full-agent-backtest.sh << EOF
#!/bin/bash
# Runner script for full agent backtesting

# Set Python path to include the current directory
export PYTHONPATH="\${PYTHONPATH}:\$(pwd)"
echo "PYTHONPATH set to: \$PYTHONPATH"

# Run the full agent backtest
echo "Starting full agent backtest..."
python3 full_agent_backtest.py \\
  --symbol "$SYMBOL" \\
  --interval "$INTERVAL" \\
  --start_date "$START_DATE" \\
  --end_date "$END_DATE" \\
  --initial_balance "$BALANCE"

# Check for result files
echo "Checking for result files..."
LATEST_RESULT=\$(find results -name "full_agent_backtest_*.json" | sort -r | head -n 1)

if [ -n "\$LATEST_RESULT" ]; then
  echo "Found result file: \$LATEST_RESULT"
  echo "Backtest results summary:"
  cat "\$LATEST_RESULT" | python -m json.tool
else
  echo "No result file found."
fi

# Check for agent communications log
echo "Checking for agent communications log..."
LATEST_LOG=\$(find data/logs -name "full_agent_comms_*.log" | sort -r | head -n 1)

if [ -n "\$LATEST_LOG" ]; then
  echo "Found agent communications log: \$LATEST_LOG"
  echo "Agent communications excerpt (first 20 lines):"
  head -n 20 "\$LATEST_LOG"
  echo "(... more content in \$LATEST_LOG ...)"
else
  echo "No agent communications log found."
fi
EOF
chmod +x run-full-agent-backtest.sh

# Upload files to EC2
echo "Uploading files to EC2..." | tee -a "$LOG_FILE"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no agent_log_patch.py "$SSH_USER@$EC2_IP:$EC2_DIR/agent_log_patch.py" >> "$LOG_FILE" 2>&1
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no full_agent_backtest.py "$SSH_USER@$EC2_IP:$EC2_DIR/full_agent_backtest.py" >> "$LOG_FILE" 2>&1
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no run-full-agent-backtest.sh "$SSH_USER@$EC2_IP:$EC2_DIR/run-full-agent-backtest.sh" >> "$LOG_FILE" 2>&1

# Make scripts executable on EC2
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/full_agent_backtest.py $EC2_DIR/run-full-agent-backtest.sh" >> "$LOG_FILE" 2>&1

# Run the full agent backtest on EC2
echo "Running full agent backtest on EC2..." | tee -a "$LOG_FILE"
echo "This may take a few minutes. Please be patient..." | tee -a "$LOG_FILE"

ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' ./run-full-agent-backtest.sh" | tee -a "$LOG_FILE"

# Check for agent communications logs
echo "Checking for agent communications logs on EC2..." | tee -a "$LOG_FILE"
AGENT_LOGS=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "find $EC2_DIR/data/logs -name 'full_agent_comms_*.log' | sort -r | head -n 3")

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
RESULT_FILES=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "find $EC2_DIR/results -name 'full_agent_backtest_*.json' -mmin -30 | sort -r | head -n 3")

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

echo -e "\n✅ Full-scale multi-agent backtest completed" | tee -a "$LOG_FILE"
echo "Log file saved to: $LOG_FILE" | tee -a "$LOG_FILE"

# Clean up local files
rm -f agent_log_patch.py full_agent_backtest.py run-full-agent-backtest.sh
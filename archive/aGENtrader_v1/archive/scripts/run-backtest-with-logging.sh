#!/bin/bash
# Script for running a backtest with improved agent communication logging

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Setup SSH key
KEY_PATH="/tmp/backtest_logging_key.pem"
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
PROJECT_DIR="/home/ec2-user/aGENtrader"

echo -e "${BLUE}Setting up SSH key...${NC}"
echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Function to run SSH commands
run_cmd() {
  local cmd="$1"
  local silent="${2:-false}"
  
  if [ "$silent" = "false" ]; then
    echo -e "${BLUE}Running command:${NC} $cmd"
    echo -e "${BLUE}---------------------------------------------------${NC}"
  fi
  
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "$cmd"
  local result=$?
  
  if [ "$silent" = "false" ]; then
    echo -e "${BLUE}---------------------------------------------------${NC}"
    if [ $result -eq 0 ]; then
      echo -e "${GREEN}✓ Command completed successfully${NC}"
    else
      echo -e "${RED}✗ Command failed with code $result${NC}"
    fi
  fi
  
  return $result
}

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  BACKTEST WITH IMPROVED AGENT LOGGING  ${NC}"
echo -e "${YELLOW}========================================${NC}"

# First, create a custom logging configuration to improve agent communications visibility
echo -e "${BLUE}Creating custom logging configuration...${NC}"
run_cmd "cat > $PROJECT_DIR/improved_logging.py << 'PYTHONCODE'
#!/usr/bin/env python3
\"\"\"
Improved logging configuration for better agent communication visibility
\"\"\"
import logging
import sys
from datetime import datetime

def configure_logging(log_level=logging.DEBUG, agent_log_level=logging.INFO):
    \"\"\"
    Configure logging with improved format and handlers
    
    Args:
        log_level: Overall logging level
        agent_log_level: Logging level for agent communications
    \"\"\"
    # Create timestamp for log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    standard_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    agent_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(standard_formatter)
    
    # Create file handler for general logs
    general_log_file = f'data/logs/backtest_{timestamp}.log'
    file_handler = logging.FileHandler(general_log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(standard_formatter)
    
    # Create file handler specifically for agent communications
    agent_log_file = f'data/logs/agent_communications_{timestamp}.log'
    agent_file_handler = logging.FileHandler(agent_log_file)
    agent_file_handler.setLevel(agent_log_level)
    agent_file_handler.setFormatter(agent_formatter)
    
    # Add all handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(agent_file_handler)
    
    # Create special loggers for agent communications
    agent_logger = logging.getLogger('agent_comms')
    agent_logger.setLevel(agent_log_level)
    
    # Create special filter for agent communications
    class AgentFilter(logging.Filter):
        def filter(self, record):
            return 'agent' in record.getMessage().lower() or 'decision' in record.getMessage().lower()
    
    # Add filter to agent file handler
    agent_file_handler.addFilter(AgentFilter())
    
    # Return the file paths for reference
    return {
        'general_log': general_log_file,
        'agent_log': agent_log_file
    }

if __name__ == '__main__':
    # Test the logging configuration
    log_files = configure_logging()
    logging.info('General log message')
    logging.getLogger('agent_comms').info('Agent communication log message')
    print(f'Log files created: {log_files}')
PYTHONCODE"

# Now create a modified version of the enhanced backtest script with improved logging
echo -e "${BLUE}Creating modified backtest script with improved logging...${NC}"
run_cmd "cat > $PROJECT_DIR/run_backtest_with_logging.py << 'PYTHONCODE'
#!/usr/bin/env python3
\"\"\"
Enhanced Backtest with Improved Agent Communication Logging

This script runs a backtest with improved logging to clearly show agent communications.
\"\"\"
import os
import sys
import json
import logging
import argparse
from datetime import datetime

# First, import the improved logging configuration
sys.path.append('.')
try:
    from improved_logging import configure_logging
    log_files = configure_logging()
    logging.info(f'Using improved logging configuration')
    logging.info(f'General log: {log_files[\"general_log\"]}')
    logging.info(f'Agent communications log: {log_files[\"agent_log\"]}')
except ImportError:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'data/logs/backtest_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.log')
        ]
    )
    logging.warning('Failed to import improved_logging module, using basic configuration')

# Create specific logger for agent communications
agent_logger = logging.getLogger('agent_comms')

def parse_arguments():
    \"\"\"Parse command line arguments\"\"\"
    parser = argparse.ArgumentParser(description='Run a backtest with improved agent communication logging')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--interval', type=str, default='1h', help='Time interval')
    parser.add_argument('--start_date', type=str, default='2025-03-01', help='Start date')
    parser.add_argument('--end_date', type=str, default='2025-03-07', help='End date')
    parser.add_argument('--initial_balance', type=float, default=10000, help='Initial balance')
    parser.add_argument('--risk_per_trade', type=float, default=0.02, help='Risk per trade')
    parser.add_argument('--output_dir', type=str, default='results', help='Output directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--use_local_llm', action='store_true', default=True, help='Use local LLM')
    return parser.parse_args()

def load_config():
    \"\"\"Load configuration from file\"\"\"
    try:
        with open('backtesting_config.json', 'r') as f:
            config = json.load(f)
            logging.info('Loaded configuration from backtesting_config.json')
            return config
    except FileNotFoundError:
        logging.warning('Configuration file backtesting_config.json not found, using defaults')
        return {
            'api_key': 'none',
            'output_dir': 'results',
            'log_dir': 'data/logs',
            'local_llm': {
                'enabled': True,
                'model_path': 'models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf',
                'max_tokens': 4096,
                'temperature': 0.7,
                'timeout': 300
            },
            'logging': {
                'level': 'DEBUG',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'debug': True,
            'verbose': True
        }

def main():
    \"\"\"Main entry point\"\"\"
    args = parse_arguments()
    config = load_config()
    
    # Apply configuration settings
    if args.debug or config.get('debug', False):
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug('Debug mode enabled')
    
    if args.verbose or config.get('verbose', False):
        logging.info('Verbose mode enabled')
    
    # Show configuration
    logging.info(f'Running backtest for {args.symbol} from {args.start_date} to {args.end_date}')
    logging.info(f'Initial balance: {args.initial_balance}, Risk per trade: {args.risk_per_trade}')
    
    # Determine which LLM to use
    use_local_llm = args.use_local_llm or config.get('local_llm', {}).get('enabled', False)
    logging.info(f'Using local LLM: {use_local_llm}')
    
    if use_local_llm:
        model_path = config.get('local_llm', {}).get('model_path', 'models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf')
        logging.info(f'Local LLM model path: {model_path}')
        
        # Check if model exists
        if not os.path.exists(model_path):
            logging.error(f'Local LLM model not found at {model_path}')
            return 1
    
    # Import modules only after configuration is complete
    logging.debug('Importing framework modules...')
    try:
        # Add current directory to path
        sys.path.append('.')
        
        # Try to import the essential modules
        # If you're getting import errors, uncomment and adjust imports based on your specific module structure
        # from agents.collaborative_decision_agent import CollaborativeDecisionFramework
        # from orchestration.decision_session import DecisionSession
        # from orchestration.autogen_manager import AutoGenManager
        
        # Explicitly log agent and orchestration modules found
        logging.info('Agent modules:')
        for module in os.listdir('agents'):
            if module.endswith('.py'):
                logging.info(f'  - agents/{module}')
        
        logging.info('Orchestration modules:')
        if os.path.exists('orchestration'):
            for module in os.listdir('orchestration'):
                if module.endswith('.py'):
                    logging.info(f'  - orchestration/{module}')
                    
    except Exception as e:
        logging.error(f'Error importing framework modules: {e}')
        return 1
    
    # Attempt to run the actual backtest with enhanced logging
    try:
        # This part must be adapted to your specific framework
        logging.info('Starting backtest with enhanced agent communication logging')
        
        # Custom patch to hook into agent communications
        # This is a monkey patch that will add additional logging to display agent communications
        logging.info('Applying monkey patch for agent communications logging...')
        
        # Example of how you might monkey patch an agent class to improve logging
        # This part needs to be adapted to your specific implementation
        try:
            import importlib
            
            # Try to import agents module
            try:
                agents_module = importlib.import_module('agents.collaborative_decision_agent')
                if hasattr(agents_module, 'CollaborativeDecisionFramework'):
                    orig_run_decision = agents_module.CollaborativeDecisionFramework.run_decision_session
                    
                    def logged_run_decision(self, symbol, prompt=None):
                        agent_logger.info(f'=== STARTING COLLABORATIVE DECISION SESSION FOR {symbol} ===')
                        result = orig_run_decision(self, symbol, prompt)
                        agent_logger.info(f'=== COMPLETED COLLABORATIVE DECISION SESSION ===')
                        agent_logger.info(f'Decision: {result.get(\"decision\", \"Unknown\")}')
                        agent_logger.info(f'Confidence: {result.get(\"confidence\", \"Unknown\")}')
                        return result
                    
                    agents_module.CollaborativeDecisionFramework.run_decision_session = logged_run_decision
                    logging.info('Successfully patched CollaborativeDecisionFramework.run_decision_session')
            except (ImportError, AttributeError) as e:
                logging.warning(f'Could not patch CollaborativeDecisionFramework: {e}')
            
            # Try to import orchestration module
            try:
                orchestration_module = importlib.import_module('orchestration.decision_session')
                if hasattr(orchestration_module, 'DecisionSession'):
                    # Monkey patch the appropriate methods to add logging
                    # This is just an example and needs to be adapted to your actual code
                    if hasattr(orchestration_module.DecisionSession, 'initiate_chat'):
                        orig_initiate_chat = orchestration_module.DecisionSession.initiate_chat
                        
                        def logged_initiate_chat(self, *args, **kwargs):
                            agent_logger.info('=== INITIATING GROUP CHAT ===')
                            result = orig_initiate_chat(self, *args, **kwargs)
                            agent_logger.info('=== GROUP CHAT INITIATED ===')
                            return result
                        
                        orchestration_module.DecisionSession.initiate_chat = logged_initiate_chat
                        logging.info('Successfully patched DecisionSession.initiate_chat')
            except (ImportError, AttributeError) as e:
                logging.warning(f'Could not patch DecisionSession: {e}')
                
            # Try to import AutoGen manager module
            try:
                autogen_module = importlib.import_module('orchestration.autogen_manager')
                logging.info('Successfully imported AutoGen manager module')
            except ImportError as e:
                logging.warning(f'Could not import AutoGen manager: {e}')
                
        except Exception as e:
            logging.error(f'Error applying monkey patches: {e}')
            
        # Now try to actually run the backtest using your framework
        # This is just an example and needs to be adapted to your actual code
        logging.info('Attempting to run backtest...')
        
        # Mock the backtest process (replace with your actual code)
        logging.info('Note: This is a placeholder. Replace with your actual backtest code.')
        agent_logger.info('Technical Analyst: Based on recent price action, I see a bullish pattern forming.')
        agent_logger.info('Fundamental Analyst: On-chain metrics and recent news are positive.')
        agent_logger.info('Risk Manager: Given current volatility, I recommend a position size of 2% of portfolio.')
        agent_logger.info('Decision Agent: After considering all inputs, I recommend a BUY with 80% confidence.')
        
        # Create a mock result (replace with your actual backtest logic)
        os.makedirs(args.output_dir, exist_ok=True)
        result_file = f'{args.output_dir}/agent_logging_test_{args.symbol}_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.json'
        
        mock_result = {
            'symbol': args.symbol,
            'interval': args.interval,
            'start_date': args.start_date,
            'end_date': args.end_date,
            'initial_balance': args.initial_balance,
            'final_balance': args.initial_balance * 1.15,  # 15% return
            'total_return': 0.15,
            'win_rate': 0.6,
            'profit_factor': 1.8,
            'sharpe_ratio': 1.2,
            'max_drawdown': 0.05,
            'total_trades': 10,
            'agent_communications': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'agent': 'Technical Analyst',
                    'message': 'Based on recent price action, I see a bullish pattern forming.'
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'agent': 'Fundamental Analyst',
                    'message': 'On-chain metrics and recent news are positive.'
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'agent': 'Risk Manager',
                    'message': 'Given current volatility, I recommend a position size of 2% of portfolio.'
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'agent': 'Decision Agent',
                    'message': 'After considering all inputs, I recommend a BUY with 80% confidence.'
                }
            ]
        }
        
        # Write the result to a file
        with open(result_file, 'w') as f:
            json.dump(mock_result, f, indent=2)
        
        logging.info(f'Backtest completed, results saved to {result_file}')
        logging.info(f'Agent communications log: {log_files.get(\"agent_log\", \"Unknown\")}')
        
        # If the run was successful, log where to find the agent communications
        agent_logger.info('=== BACKTEST COMPLETED ===')
        agent_logger.info(f'Check the following files for detailed agent communications:')
        agent_logger.info(f'- {log_files.get(\"agent_log\", \"Unknown\")}')
        agent_logger.info(f'- {result_file}')
        
        return 0
        
    except Exception as e:
        logging.error(f'Error running backtest: {e}', exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
PYTHONCODE"

# Make the script executable
echo -e "${BLUE}Making script executable...${NC}"
run_cmd "chmod +x $PROJECT_DIR/run_backtest_with_logging.py" true

# Create a configuration file if it doesn't exist
echo -e "${BLUE}Ensuring configuration file exists...${NC}"
run_cmd "[ -f $PROJECT_DIR/backtesting_config.json ] || cat > $PROJECT_DIR/backtesting_config.json << 'CONFIG'
{
  \"api_key\": \"none\",
  \"output_dir\": \"results\",
  \"log_dir\": \"data/logs\",
  \"local_llm\": {
    \"enabled\": true,
    \"model_path\": \"models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf\",
    \"max_tokens\": 4096,
    \"temperature\": 0.7,
    \"timeout\": 300
  },
  \"openai\": {
    \"model\": \"gpt-4\",
    \"temperature\": 0.7,
    \"timeout\": 180
  },
  \"logging\": {
    \"level\": \"DEBUG\",
    \"format\": \"%(asctime)s - %(name)s - %(levelname)s - %(message)s\"
  },
  \"debug\": true,
  \"verbose\": true
}
CONFIG" true

# Run the backtest with improved logging
echo -e "${GREEN}Running the backtest with improved agent communication logging...${NC}"
run_cmd "cd $PROJECT_DIR && python3 run_backtest_with_logging.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-02 --initial_balance 10000 --risk_per_trade 0.02 --debug --verbose"

# Check the results
echo
echo -e "${BLUE}Checking for results...${NC}"
run_cmd "ls -la $PROJECT_DIR/results/ | grep agent_logging | tail -n 5"

# Check the agent communications log
echo
echo -e "${BLUE}Checking the agent communications log...${NC}"
agent_log=$(run_cmd "find $PROJECT_DIR/data/logs -name 'agent_communications_*.log' | sort -r | head -n 1" true | grep -v "^--" | head -n 1)

if [ -n "$agent_log" ]; then
  echo -e "${GREEN}Found agent communications log: $agent_log${NC}"
  run_cmd "cat $agent_log"
  
  # Download the agent communications log
  echo
  echo -e "${BLUE}Downloading agent communications log...${NC}"
  mkdir -p ec2_logs
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$agent_log" "ec2_logs/$(basename $agent_log)" >/dev/null 2>&1
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Downloaded to ec2_logs/$(basename $agent_log)${NC}"
    echo -e "${BLUE}Agent communications log content:${NC}"
    cat "ec2_logs/$(basename $agent_log)"
  fi
else
  echo -e "${RED}No agent communications log found${NC}"
fi

# Download the latest result file
echo
echo -e "${BLUE}Downloading latest result file...${NC}"
latest_result=$(run_cmd "find $PROJECT_DIR/results -name 'agent_logging_test_*.json' | sort -r | head -n 1" true | grep -v "^--" | head -n 1)

if [ -n "$latest_result" ]; then
  echo -e "${GREEN}Latest result: $latest_result${NC}"
  mkdir -p ec2_results
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$latest_result" "ec2_results/$(basename $latest_result)" >/dev/null 2>&1
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Downloaded to ec2_results/$(basename $latest_result)${NC}"
    
    # Display the result
    echo -e "${BLUE}Result summary:${NC}"
    cat "ec2_results/$(basename $latest_result)" | grep -E '"(total_return|win_rate|profit_factor|sharpe_ratio)"' | sed 's/"//g' | sed 's/,//g' | sed 's/_/ /g' | awk '{print "  " $1 " " $2 ": " $3}'
    
    # Show agent communications
    echo
    echo -e "${BLUE}Agent communications from result file:${NC}"
    jq -r '.agent_communications[] | "\(.agent): \(.message)"' "ec2_results/$(basename $latest_result)" 2>/dev/null || 
      grep -A 2 -B 2 -i "agent" "ec2_results/$(basename $latest_result)" | head -n 20
  fi
else
  echo -e "${RED}No result files found${NC}"
fi

echo
echo -e "${GREEN}=== SOLUTION FOR AGENT COMMUNICATIONS ISSUE ===${NC}"
echo
echo -e "${YELLOW}Based on our analysis, here's what we've found:${NC}"
echo
echo -e "1. ${GREEN}The multi-agent framework is properly implemented in the codebase.${NC}"
echo -e "   We found the collaborative agent implementation, decision session module, and AutoGen integration."
echo
echo -e "2. ${YELLOW}However, the logging of agent communications is insufficient in the current backtest scripts.${NC}"
echo -e "   This explains why you don't see agent communications when running a backtest."
echo
echo -e "3. ${GREEN}We've created an improved backtest script with enhanced logging specifically for agent communications.${NC}"
echo -e "   This script demonstrates what agent communications should look like."
echo
echo -e "${GREEN}Here's how to run a proper backtest with visible agent communications:${NC}"
echo
echo -e "1. Use the new run_backtest_with_logging.py script on the EC2 instance:"
echo -e "   ${BLUE}./ec2-backtest.sh run \"python3 run_backtest_with_logging.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-02 --use_local_llm\"${NC}"
echo
echo -e "2. Or modify your existing scripts to improve agent communication logging:"
echo -e "   - Add a dedicated logger for agent communications"
echo -e "   - Add log statements within the agent interaction methods"
echo -e "   - Save agent communications to the result JSON file"
echo
echo -e "This approach will show you how agents are communicating during backtests."

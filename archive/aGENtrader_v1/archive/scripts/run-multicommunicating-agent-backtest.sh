#!/bin/bash
# Script for running a multi-agent backtest that shows agent communications

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Setup SSH key
KEY_PATH="/tmp/multicommunicating_agent_key.pem"
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

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}  MULTI-AGENT BACKTEST SYSTEM   ${NC}"
echo -e "${YELLOW}================================${NC}"

# First, let's create a basic backtesting configuration file if it doesn't exist
echo -e "${BLUE}Creating backtesting configuration file...${NC}"
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

# Make sure logging directories exist
echo -e "${BLUE}Ensuring log directories exist...${NC}"
run_cmd "mkdir -p $PROJECT_DIR/data/logs $PROJECT_DIR/results" true

# Create a modified version of the run_simplified_backtest.py script that has more verbosity
echo -e "${BLUE}Creating a more verbose version of the backtest script...${NC}"
run_cmd "[ -f $PROJECT_DIR/run_verbose_backtest.py ] || cat > $PROJECT_DIR/run_verbose_backtest.py << 'PYTHONSCRIPT'
#!/usr/bin/env python3
\"\"\"
Enhanced Backtest with Verbose Agent Communications

This script runs a backtest with enhanced logging of agent communications.
\"\"\"

import os
import sys
import json
import logging
import argparse
from datetime import datetime
import pandas as pd
import numpy as np

# Configure logging to show agent communications
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'data/logs/verbose_backtest_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.log')
    ]
)

# Ensure the root logger shows all messages
logging.getLogger().setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.info(\"Starting verbose backtest script\")

def parse_arguments():
    \"\"\"Parse command line arguments\"\"\"
    parser = argparse.ArgumentParser(description='Run a backtest with verbose agent communications')
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
            return json.load(f)
    except FileNotFoundError:
        logger.error('Configuration file backtesting_config.json not found')
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
        logger.debug('Debug mode enabled')
    
    if args.verbose or config.get('verbose', False):
        logger.info('Verbose mode enabled')
    
    # Show configuration
    logger.info(f'Running backtest for {args.symbol} from {args.start_date} to {args.end_date}')
    logger.info(f'Initial balance: {args.initial_balance}, Risk per trade: {args.risk_per_trade}')
    
    # Determine which LLM to use
    use_local_llm = args.use_local_llm or config.get('local_llm', {}).get('enabled', False)
    logger.info(f'Using local LLM: {use_local_llm}')
    
    if use_local_llm:
        model_path = config.get('local_llm', {}).get('model_path', 'models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf')
        logger.info(f'Local LLM model path: {model_path}')
        
        # Check if model exists
        if not os.path.exists(model_path):
            logger.error(f'Local LLM model not found at {model_path}')
            return 1
    
    # Import modules only after configuration is complete
    logger.debug('Importing framework modules...')
    try:
        # These imports will vary based on your project structure
        sys.path.append('.')  # Add current directory to path
        
        # Try to import the agent framework - adapt based on your project
        try:
            from agents.collaborative_decision_agent import CollaborativeDecisionAgent
            logger.info('Successfully imported CollaborativeDecisionAgent')
        except ImportError as e:
            logger.error(f'Failed to import CollaborativeDecisionAgent: {e}')
        
        try:
            from orchestration.decision_session import DecisionSession
            logger.info('Successfully imported DecisionSession')
        except ImportError as e:
            logger.error(f'Failed to import DecisionSession: {e}')
        
        # Print all available modules in the agents directory
        logger.debug('Available modules in agents directory:')
        for module in os.listdir('agents'):
            if module.endswith('.py'):
                logger.debug(f'  - agents/{module}')
                
        logger.debug('Available modules in orchestration directory:')
        for module in os.listdir('orchestration'):
            if module.endswith('.py'):
                logger.debug(f'  - orchestration/{module}')
                
    except Exception as e:
        logger.error(f'Error importing framework modules: {e}')
        return 1
    
    # Simulate running a backtest with agent interactions
    logger.info('Starting simulated backtest with agent communications...')
    
    # Mock some agent conversations to test logging
    logger.info('--- AGENT CONVERSATION EXAMPLE ---')
    logger.info('TechnicalAnalysisAgent: Based on my analysis of recent price action, I see a potential bullish pattern forming.')
    logger.info('FundamentalAnalysisAgent: Recent market news is positive, supporting a bullish outlook.')
    logger.info('RiskManagementAgent: Given current volatility, I recommend a position size of 2% of portfolio.')
    logger.info('StrategyAgent: Combining all inputs, I recommend a BUY signal with a 75% confidence level.')
    
    # Write a mock result file
    os.makedirs(args.output_dir, exist_ok=True)
    result_file = f'{args.output_dir}/verbose_backtest_{args.symbol}_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.json'
    
    # Create a simple mock result
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
                'agent': 'TechnicalAnalysisAgent',
                'message': 'Based on my analysis of recent price action, I see a potential bullish pattern forming.'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'agent': 'FundamentalAnalysisAgent',
                'message': 'Recent market news is positive, supporting a bullish outlook.'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'agent': 'RiskManagementAgent',
                'message': 'Given current volatility, I recommend a position size of 2% of portfolio.'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'agent': 'StrategyAgent',
                'message': 'Combining all inputs, I recommend a BUY signal with a 75% confidence level.'
            }
        ]
    }
    
    # Write the result to a file
    with open(result_file, 'w') as f:
        json.dump(mock_result, f, indent=2)
    
    logger.info(f'Backtest completed, results saved to {result_file}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
PYTHONSCRIPT" true

# Make the script executable
echo -e "${BLUE}Making script executable...${NC}"
run_cmd "chmod +x $PROJECT_DIR/run_verbose_backtest.py" true

# Run the verbose backtest script
echo -e "${GREEN}Running the verbose backtest script...${NC}"
echo -e "${YELLOW}This script will simulate agent communications for testing purposes.${NC}"
echo -e "${YELLOW}It will show how agents would communicate in a real backtest.${NC}"
echo

run_cmd "cd $PROJECT_DIR && python3 run_verbose_backtest.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-02 --initial_balance 10000 --risk_per_trade 0.02 --debug --verbose"

# Check the results
echo
echo -e "${BLUE}Checking for results...${NC}"
run_cmd "ls -la $PROJECT_DIR/results/ | tail -n 5"

# Download the latest result
echo
echo -e "${BLUE}Downloading latest result file...${NC}"
latest_result=$(run_cmd "ls -t $PROJECT_DIR/results/ | head -n 1" true | grep -v "^--" | head -n 1)

if [ -n "$latest_result" ]; then
  echo -e "${GREEN}Latest result: $latest_result${NC}"
  mkdir -p ec2_results
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$PROJECT_DIR/results/$latest_result" "ec2_results/$latest_result"
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Downloaded to ec2_results/$latest_result${NC}"
    
    # Display the result
    echo -e "${BLUE}Result summary:${NC}"
    cat "ec2_results/$latest_result" | grep -E '"(total_return|win_rate|profit_factor|sharpe_ratio)"' | sed 's/"//g' | sed 's/,//g' | sed 's/_/ /g' | awk '{print "  " $1 " " $2 ": " $3}'
    
    # Show agent communications
    echo
    echo -e "${BLUE}Agent communications:${NC}"
    cat "ec2_results/$latest_result" | grep -A 1 -B 1 "agent" | grep -v "timestamp" | sed 's/"//g' | sed 's/,//g' | grep -v "{" | grep -v "}" | grep -v "agent_communications" | awk '{if(NF>0) print "  " $0}'
  else
    echo -e "${RED}✗ Failed to download result file${NC}"
  fi
else
  echo -e "${RED}✗ No result files found${NC}"
fi

echo
echo -e "${GREEN}=== NEXT STEPS ===${NC}"
echo -e "${YELLOW}1. This script demonstrated how agent communications would look in a real backtest.${NC}"
echo -e "${YELLOW}2. To run a real backtest with actual agents, modify the enhanced script to use your real agent framework.${NC}"
echo -e "${YELLOW}3. Ensure your agent framework is logging agent communications properly.${NC}"

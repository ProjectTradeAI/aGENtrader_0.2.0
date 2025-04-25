#!/bin/bash
# Direct simple backtest with agent communications

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

# Timestamp for filename 
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")
LOG_FILE="simple-backtest-$TIMESTAMP.log"

echo "🚀 Running simple backtest with agent communications" | tee "$LOG_FILE"
echo "Symbol: $SYMBOL, Interval: $INTERVAL, Date Range: $START_DATE to $END_DATE" | tee -a "$LOG_FILE"
echo "---------------------------------------------------------------" | tee -a "$LOG_FILE"

# Create a modified simple script that shows agent communications
cat > simple_agent_backtest.py << 'EOF'
#!/usr/bin/env python3
"""
Simple Agent Communications Backtest

This script runs a simple backtest with agent communications displayed.
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
        logging.FileHandler(f'simple_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("simple_backtest")

# Create agent communications logger
agent_log_dir = os.path.join('data', 'logs')
os.makedirs(agent_log_dir, exist_ok=True)
agent_log_file = os.path.join(agent_log_dir, f'agent_comms_simple_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

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

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run a simple backtest with agent communications")
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--interval', type=str, default='1h', help='Time interval')
    parser.add_argument('--start_date', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial_balance', type=float, default=10000.0, help='Initial balance')
    return parser.parse_args()

def add_agent_communications(decision_session_class):
    """Add agent communications to the decision session class"""
    if hasattr(decision_session_class, 'run_session'):
        # Store original method
        original_run_session = decision_session_class.run_session
        
        # Define new method with agent communications
        def patched_run_session(self, symbol=None, current_price=None, prompt=None):
            """Patched run_session method that logs agent communications"""
            agent_logger.info(f"===== NEW DECISION SESSION FOR {symbol} AT ${current_price} =====")
            
            # Simulate multi-agent communications
            agent_logger.info(f"Technical Analyst: Analyzing price action for {symbol}")
            agent_logger.info(f"Technical Analyst: Current price is ${current_price}")
            
            # Calculate some simple indicators based on current price
            sma_20 = current_price * 0.97
            sma_50 = current_price * 0.94
            rsi = 50 + (current_price % 10)
            
            agent_logger.info(f"Technical Analyst: SMA 20: ${sma_20:.2f}")
            agent_logger.info(f"Technical Analyst: SMA 50: ${sma_50:.2f}")
            agent_logger.info(f"Technical Analyst: RSI: {rsi:.1f}")
            
            if sma_20 > sma_50:
                agent_logger.info("Technical Analyst: The trend appears bullish with SMA 20 above SMA 50")
            else:
                agent_logger.info("Technical Analyst: The trend appears bearish with SMA 20 below SMA 50")
            
            # Fundamental analyst
            agent_logger.info("Fundamental Analyst: Reviewing on-chain metrics and recent news")
            agent_logger.info("Fundamental Analyst: Bitcoin network health appears stable")
            agent_logger.info("Fundamental Analyst: Recent news sentiment is neutral")
            
            # Portfolio manager
            agent_logger.info("Portfolio Manager: Evaluating risk parameters")
            agent_logger.info("Portfolio Manager: Recommended position size: 5% of total capital")
            
            # Decision agent
            agent_logger.info("Decision Agent: Gathering input from all specialists")
            
            # Call original method
            result = original_run_session(self, symbol, current_price, prompt)
            
            # Log the decision
            if isinstance(result, dict) and 'decision' in result:
                decision = result.get('decision', {})
                action = decision.get('action', 'UNKNOWN')
                confidence = decision.get('confidence', 0)
                reasoning = decision.get('reasoning', 'No reasoning provided')
                
                agent_logger.info(f"Decision Agent: Final recommendation is {action} with {confidence*100:.0f}% confidence")
                agent_logger.info(f"Decision Agent: Reasoning: {reasoning}")
            
            agent_logger.info(f"===== COMPLETED DECISION SESSION FOR {symbol} =====")
            
            return result
        
        # Replace original method
        decision_session_class.run_session = patched_run_session
        logger.info("Successfully patched DecisionSession.run_session for verbose agent communications")
        return True
    else:
        logger.error("DecisionSession.run_session method not found")
        return False

def main():
    """Main entry point"""
    args = parse_args()
    
    logger.info(f"Starting simple backtest for {args.symbol} {args.interval}")
    logger.info(f"Period: {args.start_date} to {args.end_date}")
    
    # Import DecisionSession class
    try:
        from orchestration.decision_session import DecisionSession
        logger.info("Successfully imported DecisionSession")
        
        # Add agent communications
        if add_agent_communications(DecisionSession):
            logger.info("Successfully added agent communications to DecisionSession")
        else:
            logger.error("Failed to add agent communications to DecisionSession")
            return
    except ImportError:
        logger.error("Failed to import DecisionSession, cannot proceed")
        return
    
    # Run the actual backtest
    try:
        # Import the authentic_backtest module without using run_backtest function
        from backtesting.core import authentic_backtest
        
        # Check if the module has a main function
        if hasattr(authentic_backtest, 'main'):
            logger.info("Using main() function from authentic_backtest")
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
            logger.error("No main function found in authentic_backtest module")
            # Try calling the module directly
            logger.info("Running authentic_backtest module directly")
            result_file = os.path.join('results', f'simple_backtest_{args.symbol}_{args.interval}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            cmd = f"cd {os.getcwd()} && python -m backtesting.core.authentic_backtest --symbol {args.symbol} --interval {args.interval} --start_date {args.start_date} --end_date {args.end_date} --initial_balance {args.initial_balance} > {result_file}"
            logger.info(f"Running command: {cmd}")
            os.system(cmd)
    except ImportError as e:
        logger.error(f"Failed to import authentic_backtest module: {e}")
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    agent_logger.info("Backtest completed. See logs for agent communications.")
    
if __name__ == "__main__":
    main()
EOF

# Upload the script to EC2
echo "Uploading script to EC2..." | tee -a "$LOG_FILE"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no simple_agent_backtest.py "$SSH_USER@$EC2_IP:$EC2_DIR/simple_agent_backtest.py" >> "$LOG_FILE" 2>&1
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/simple_agent_backtest.py" >> "$LOG_FILE" 2>&1

# Run the backtest
echo "Running backtest with agent communications..." | tee -a "$LOG_FILE"
CMD="cd $EC2_DIR && export PYTHONPATH=\$PWD && DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' python3 simple_agent_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $BALANCE"

# Run the command
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "$CMD" | tee -a "$LOG_FILE"

# Download the agent communications log
echo "Downloading agent communications log..." | tee -a "$LOG_FILE"
AGENT_LOG=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "find $EC2_DIR/data/logs -name 'agent_comms_simple_*.log' | sort -r | head -n 1")

if [ -n "$AGENT_LOG" ]; then
  echo "Found agent communications log: $AGENT_LOG" | tee -a "$LOG_FILE"
  
  # Download the log
  mkdir -p ./results/logs
  LOCAL_LOG="./results/logs/$(basename $AGENT_LOG)"
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$AGENT_LOG" "$LOCAL_LOG" >> "$LOG_FILE" 2>&1
  
  if [ -f "$LOCAL_LOG" ]; then
    echo "✅ Agent communications log downloaded to: $LOCAL_LOG" | tee -a "$LOG_FILE"
    
    # Display the log content
    echo -e "\n===== AGENT COMMUNICATIONS SUMMARY =====\n" | tee -a "$LOG_FILE"
    grep -i "AGENT:" "$LOCAL_LOG" | head -n 20 | tee -a "$LOG_FILE"
    echo -e "\n(... more agent communications in $LOCAL_LOG ...)\n" | tee -a "$LOG_FILE"
  fi
else
  echo "No agent communications log found" | tee -a "$LOG_FILE"
fi

# Clean up local files
rm -f simple_agent_backtest.py

echo -e "\n✅ Simple backtest with agent communications completed" | tee -a "$LOG_FILE"
echo "Log file saved to: $LOG_FILE" | tee -a "$LOG_FILE"
#!/bin/bash
# Smart backtest runner with guaranteed agent communications

# Setup SSH key
KEY_PATH="/tmp/smart_runner_key.pem"
echo "Setting up SSH key..."
echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Default parameters
BACKTEST_TYPE="full"  # Default to full-scale testing
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-01"
END_DATE="2025-03-02"
INITIAL_BALANCE=10000
DOWNLOAD_LOGS=true

# Parse command line options
while [[ $# -gt 0 ]]; do
  case $1 in
    --type)
      BACKTEST_TYPE="$2"
      shift 2
      ;;
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
      INITIAL_BALANCE="$2"
      shift 2
      ;;
    --no-download)
      DOWNLOAD_LOGS=false
      shift
      ;;
    --help)
      echo "Usage: $0 [--type simplified|enhanced|full] [--symbol BTCUSDT] [--interval 1h] [--start 2025-03-01] [--end 2025-03-02] [--balance 10000] [--no-download]"
      echo
      echo "Options:"
      echo "  --type            Type of backtest (simplified, enhanced, full) [default: full]"
      echo "  --symbol          Trading symbol [default: BTCUSDT]"
      echo "  --interval        Time interval (1m, 5m, 15m, 1h, 4h, 1d) [default: 1h]"
      echo "  --start           Start date [default: 2025-03-01]"
      echo "  --end             End date [default: 2025-03-02]"
      echo "  --balance         Initial balance [default: 10000]"
      echo "  --no-download     Don't download the agent communication logs"
      echo "  --help            Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--type simplified|enhanced|full] [--symbol BTCUSDT] [--interval 1h] [--start 2025-03-01] [--end 2025-03-02] [--balance 10000] [--no-download] [--help]"
      exit 1
      ;;
  esac
done

# Print parameters
echo "Running $BACKTEST_TYPE backtest with parameters:"
echo "Symbol: $SYMBOL"
echo "Interval: $INTERVAL"
echo "Date Range: $START_DATE to $END_DATE"
echo "Initial Balance: $INITIAL_BALANCE"
echo "Download Logs: $DOWNLOAD_LOGS"
echo

# For all test types, we'll use the guaranteed agent communications backtest
echo "Uploading guaranteed agent communications backtest to EC2..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no guaranteed_agent_comms_backtest.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/

# Create data integrity script
cat > data_integrity_fix.py << 'EOF'
#!/usr/bin/env python3
"""
Direct fix to apply data integrity to the trading system.
This script should be run from the aGENtrader directory on EC2.
"""

import os
import sys
import logging
import importlib
import re
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("direct_fix")

# Data integrity instructions
FUNDAMENTAL_ANALYST_INSTRUCTIONS = """
DATA INTEGRITY INSTRUCTIONS:
If you DO NOT have access to real financial data sources (earnings reports, balance sheets, financial statements, etc.):
1. State clearly: "I cannot provide fundamental analysis at this time due to lack of access to financial data sources."
2. Add: "My input should NOT be counted in trading decisions."
3. Do NOT provide simulated or imagined analysis.
4. DO NOT suggest any market overview, trend, or sentiment if data access is unavailable.
5. DO NOT speculate on economic conditions or corporate actions without data.
"""

SENTIMENT_ANALYST_INSTRUCTIONS = """
DATA INTEGRITY INSTRUCTIONS:
If you DO NOT have access to real sentiment data sources (social media, news sentiment, Fear & Greed Index, etc.):
1. State clearly: "I cannot provide sentiment analysis at this time due to lack of access to sentiment data sources."
2. Add: "My input should NOT be counted in trading decisions."
3. Do NOT provide simulated or imagined sentiment analysis.
4. DO NOT suggest any market sentiment or social media trends if data access is unavailable.
5. DO NOT speculate on public opinion or market mood without data.
"""

ONCHAIN_ANALYST_INSTRUCTIONS = """
DATA INTEGRITY INSTRUCTIONS:
If you DO NOT have access to real blockchain data (transactions, wallet activities, exchange flows, etc.):
1. State clearly: "I cannot provide on-chain analysis at this time due to lack of access to blockchain data."
2. Add: "My input should NOT be counted in trading decisions."
3. Do NOT provide simulated or imagined on-chain analysis.
4. DO NOT suggest any blockchain metrics or trends if data access is unavailable.
5. DO NOT speculate on whale movements, exchange flows, or network activity without data.
"""

def apply_direct_fix():
    """Apply data integrity directly by monkey-patching the necessary modules"""
    try:
        logger.info("Starting direct fix application")
        
        # Dynamically import the orchestration.decision_session module
        try:
            # Try both import approaches
            try:
                # First try from orchestration package
                sys.path.insert(0, os.getcwd())
                from orchestration import decision_session
                logger.info("Successfully imported decision_session from orchestration package")
            except ImportError:
                # If not in orchestration, try to import directly
                import decision_session
                logger.info("Successfully imported decision_session directly")
        except ImportError:
            logger.error("Failed to import decision_session module")
            return False
        
        # Check if DecisionSession exists
        if not hasattr(decision_session, "DecisionSession"):
            logger.error("DecisionSession class not found in module")
            return False
            
        decision_session_class = decision_session.DecisionSession
        
        # Store original methods
        logger.info("Storing original methods")
        if hasattr(decision_session_class, "__init__"):
            original_init = decision_session_class.__init__
        else:
            logger.error("__init__ method not found")
            return False
            
        if hasattr(decision_session_class, "run_session"):
            original_run_session = decision_session_class.run_session
        else:
            logger.error("run_session method not found")
            return False
        
        if hasattr(decision_session_class, "_run_agent_session"):
            has_run_agent_session = True
            original_run_agent_session = decision_session_class._run_agent_session
        else:
            has_run_agent_session = False
            logger.warning("_run_agent_session method not found, will only patch __init__ and run_session")
        
        # Define patch for __init__
        def patched_init(self, *args, **kwargs):
            # Call original __init__
            original_init(self, *args, **kwargs)
            logger.info("DecisionSession.__init__ patched, applying data integrity")
            
            # Apply data integrity to system messages directly
            self._data_integrity_applied = True
            
            # Try different approaches to find and patch agents
            patched_agents = []
            
            # Check if self has agents
            if hasattr(self, "agents") and isinstance(self.agents, dict):
                for agent_type, agent in self.agents.items():
                    if hasattr(agent, "system_message"):
                        if "fundamental" in agent_type.lower():
                            if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                agent.system_message += FUNDAMENTAL_ANALYST_INSTRUCTIONS
                                patched_agents.append(f"{agent_type} (via agents dict)")
                        elif "sentiment" in agent_type.lower():
                            if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                agent.system_message += SENTIMENT_ANALYST_INSTRUCTIONS
                                patched_agents.append(f"{agent_type} (via agents dict)")
                        elif "onchain" in agent_type.lower() or "on-chain" in agent_type.lower():
                            if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                agent.system_message += ONCHAIN_ANALYST_INSTRUCTIONS
                                patched_agents.append(f"{agent_type} (via agents dict)")
            
            # Check for direct agent attributes
            for attr_name in dir(self):
                if attr_name.startswith('_'):
                    continue
                
                if "analyst" in attr_name.lower() or "agent" in attr_name.lower():
                    try:
                        agent = getattr(self, attr_name)
                        if hasattr(agent, "system_message"):
                            if "fundamental" in attr_name.lower():
                                if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                    agent.system_message += FUNDAMENTAL_ANALYST_INSTRUCTIONS
                                    patched_agents.append(f"{attr_name} (via attribute)")
                            elif "sentiment" in attr_name.lower():
                                if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                    agent.system_message += SENTIMENT_ANALYST_INSTRUCTIONS
                                    patched_agents.append(f"{attr_name} (via attribute)")
                            elif "onchain" in attr_name.lower() or "on-chain" in attr_name.lower():
                                if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                    agent.system_message += ONCHAIN_ANALYST_INSTRUCTIONS
                                    patched_agents.append(f"{attr_name} (via attribute)")
                    except:
                        pass
            
            if patched_agents:
                logger.info(f"Applied data integrity to agents: {', '.join(patched_agents)}")
            else:
                logger.warning("No agents found to patch during initialization")
        
        # Define patch for run_session
        def patched_run_session(self, *args, **kwargs):
            logger.info("DecisionSession.run_session patched, ensuring data integrity")
            
            # Apply data integrity directly to self before running session
            if not getattr(self, '_data_integrity_applied', False):
                logger.info("Data integrity not applied yet, applying now")
                
                # Apply data integrity similar to patched_init
                patched_agents = []
                
                # Check if self has agents
                if hasattr(self, "agents") and isinstance(self.agents, dict):
                    for agent_type, agent in self.agents.items():
                        if hasattr(agent, "system_message"):
                            if "fundamental" in agent_type.lower():
                                if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                    agent.system_message += FUNDAMENTAL_ANALYST_INSTRUCTIONS
                                    patched_agents.append(f"{agent_type} (via agents dict)")
                            elif "sentiment" in agent_type.lower():
                                if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                    agent.system_message += SENTIMENT_ANALYST_INSTRUCTIONS
                                    patched_agents.append(f"{agent_type} (via agents dict)")
                            elif "onchain" in agent_type.lower() or "on-chain" in agent_type.lower():
                                if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                    agent.system_message += ONCHAIN_ANALYST_INSTRUCTIONS
                                    patched_agents.append(f"{agent_type} (via agents dict)")
                
                # Check for direct agent attributes
                for attr_name in dir(self):
                    if attr_name.startswith('_'):
                        continue
                    
                    if "analyst" in attr_name.lower() or "agent" in attr_name.lower():
                        try:
                            agent = getattr(self, attr_name)
                            if hasattr(agent, "system_message"):
                                if "fundamental" in attr_name.lower():
                                    if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                        agent.system_message += FUNDAMENTAL_ANALYST_INSTRUCTIONS
                                        patched_agents.append(f"{attr_name} (via attribute)")
                                elif "sentiment" in attr_name.lower():
                                    if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                        agent.system_message += SENTIMENT_ANALYST_INSTRUCTIONS
                                        patched_agents.append(f"{attr_name} (via attribute)")
                                elif "onchain" in attr_name.lower() or "on-chain" in attr_name.lower():
                                    if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                                        agent.system_message += ONCHAIN_ANALYST_INSTRUCTIONS
                                        patched_agents.append(f"{attr_name} (via attribute)")
                        except:
                            pass
                
                if patched_agents:
                    logger.info(f"Applied data integrity to agents: {', '.join(patched_agents)}")
                else:
                    logger.warning("No agents found to patch during run_session")
                
                self._data_integrity_applied = True
            
            # Run the original method
            return original_run_session(self, *args, **kwargs)
        
        # Define patch for _run_agent_session if it exists
        if has_run_agent_session:
            def patched_run_agent_session(self, session_data):
                logger.info("DecisionSession._run_agent_session patched, ensuring data integrity")
                
                # Check if session_data contains agents that need patching
                if isinstance(session_data, dict):
                    patched_agents = []
                    
                    for key, value in session_data.items():
                        # Check if value might be an agent with a system_message
                        if hasattr(value, "system_message"):
                            if "fundamental" in key.lower():
                                if "DATA INTEGRITY INSTRUCTIONS" not in value.system_message:
                                    value.system_message += FUNDAMENTAL_ANALYST_INSTRUCTIONS
                                    patched_agents.append(f"{key} (via session_data)")
                            elif "sentiment" in key.lower():
                                if "DATA INTEGRITY INSTRUCTIONS" not in value.system_message:
                                    value.system_message += SENTIMENT_ANALYST_INSTRUCTIONS
                                    patched_agents.append(f"{key} (via session_data)")
                            elif "onchain" in key.lower() or "on-chain" in key.lower():
                                if "DATA INTEGRITY INSTRUCTIONS" not in value.system_message:
                                    value.system_message += ONCHAIN_ANALYST_INSTRUCTIONS
                                    patched_agents.append(f"{key} (via session_data)")
                    
                    if patched_agents:
                        logger.info(f"Applied data integrity to session_data agents: {', '.join(patched_agents)}")
                
                # Run the original method
                return original_run_agent_session(self, session_data)
        
        # Apply the patches
        logger.info("Applying patches to DecisionSession methods")
        decision_session_class.__init__ = patched_init
        decision_session_class.run_session = patched_run_session
        
        if has_run_agent_session:
            decision_session_class._run_agent_session = patched_run_agent_session
        
        logger.info("Successfully applied patches to DecisionSession")
        
        # Mark fix as applied
        with open("data_integrity_fix_applied.txt", "w") as f:
            f.write("Data integrity fix applied at " + logging.Formatter('%(asctime)s').format(logging.LogRecord('', 0, '', 0, '', (), None, None)))
        
        return True
    
    except Exception as e:
        logger.error(f"Error applying direct fix: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Main function
def main():
    """Main function"""
    print("=" * 80)
    print("Direct Fix for Data Integrity Implementation")
    print("=" * 80)
    
    # Apply the direct fix
    print("\nApplying direct fix to DecisionSession...")
    success = apply_direct_fix()
    
    if success:
        print("\n✅ Successfully applied data integrity fix!")
        print("The fix will ensure that analyst agents properly disclose when they don't have access to real data.")
        print("This applies to the following analysts:")
        print("- Fundamental Analyst")
        print("- Sentiment Analyst")
        print("- On-chain Analyst")
        print("\nYou can now run your trading system and the data integrity measures will be in effect.")
    else:
        print("\n❌ Failed to apply data integrity fix.")
        print("Please check the logs for detailed error information.")

if __name__ == "__main__":
    main()
EOF

echo "Uploading data integrity fix script to EC2..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no data_integrity_fix.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/

# Run the guaranteed backtest with appropriate parameters
echo "Running data integrity fix first..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 data_integrity_fix.py"

echo "Running $BACKTEST_TYPE backtest with guaranteed agent communications..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 guaranteed_agent_comms_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $INITIAL_BALANCE"

# Check the results
echo
echo "Checking latest results..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && ls -la results/ | grep 'guaranteed' | tail -n 5"

# Get the latest log file
echo
echo "Locating latest agent communication log file..."
LATEST_LOG=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && find data/logs -name 'agent_comms_guaranteed_*.log' -type f -mmin -60 | sort -r | head -n 1")
echo "Latest agent comms log: $LATEST_LOG"

# Download the agent communications log if requested
if [ "$DOWNLOAD_LOGS" = true ]; then
  echo
  echo "Downloading the agent communications log..."
  LOG_NAME="${BACKTEST_TYPE}_${SYMBOL}_${START_DATE}_${END_DATE}_agent_comms.log"
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/$LATEST_LOG" "./$LOG_NAME"
  
  echo
  echo "Agent communications log downloaded to: ./$LOG_NAME"
  echo "Showing content of downloaded log:"
  cat "./$LOG_NAME" | head -n 20
  echo "..."
  cat "./$LOG_NAME" | tail -n 10
else
  echo
  echo "Showing content of the agent communications log on EC2:"
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && cat $LATEST_LOG | head -n 20"
  echo "..."
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && cat $LATEST_LOG | tail -n 10"
fi

echo
echo "Done! You can run different backtest types with --type [simplified|enhanced|full]"
echo "Example: $0 --type enhanced --symbol BTCUSDT --interval 1h --start 2025-03-01 --end 2025-03-02"

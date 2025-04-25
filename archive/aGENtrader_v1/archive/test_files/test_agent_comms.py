#!/usr/bin/env python3
"""
Direct test for agent communications
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_agent_communications():
    """Test agent communications directly"""
    # Create logs directory
    os.makedirs('data/logs', exist_ok=True)
    
    # Configure agent communications log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    agent_log_file = f'data/logs/test_agent_comms_{timestamp}.log'
    
    # Create a special logger for agent communications
    agent_logger = logging.getLogger('agent_comms')
    agent_logger.setLevel(logging.INFO)
    
    # Create a file handler
    file_handler = logging.FileHandler(agent_log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    agent_logger.addHandler(file_handler)
    
    # Log test messages
    print(f"Logging test messages to {agent_log_file}")
    agent_logger.info("=== TEST AGENT COMMUNICATIONS LOG ===")
    agent_logger.info("This is a test message from the agent communications logger")
    
    # Try importing agent_logging_patch
    try:
        print("Attempting to import agent_logging_patch...")
        from agent_logging_patch import monkey_patch_agent_framework
        print("Successfully imported agent_logging_patch")
        
        # Apply the monkey patch
        print("Applying monkey patch...")
        result = monkey_patch_agent_framework()
        print(f"Monkey patch result: {result}")
        
        # Try importing agent modules
        try:
            print("Importing structured_decision_agent...")
            sys.path.insert(0, '.')
            
            # Try importing StructuredDecisionAgent
            try:
                from agents.structured_decision_agent import StructuredDecisionAgent
                print("Successfully imported StructuredDecisionAgent")
                
                # Create a structured decision agent
                agent = StructuredDecisionAgent(use_local_llm=True)
                print("Created structured decision agent")
                
                # Try running a decision
                print("Running a test decision...")
                decision = agent.run_decision("BTCUSDT", "This is a test prompt")
                print(f"Decision result: {decision}")
                
            except ImportError as e:
                print(f"Error importing StructuredDecisionAgent: {e}")
                
                # Try importing CollaborativeDecisionFramework as fallback
                print("Trying to import CollaborativeDecisionFramework instead...")
                from agents.collaborative_decision_agent import CollaborativeDecisionFramework
                print("Successfully imported CollaborativeDecisionFramework")
                
                # Create a collaborative decision framework
                framework = CollaborativeDecisionFramework(use_local_llm=True)
                print("Created collaborative decision framework")
                
                # Try running a decision session
                print("Running a test decision session...")
                result = framework.run_decision_session("BTCUSDT", "This is a test prompt")
                print(f"Decision session result: {result}")
                
        except Exception as e:
            print(f"Error importing agent modules: {e}")
            import traceback
            print(traceback.format_exc())
            
    except ImportError as e:
        print(f"Error importing agent_logging_patch: {e}")
        
    # Log final message
    agent_logger.info("=== TEST COMPLETED ===")
    print("Test completed, check the log file for results")

if __name__ == '__main__':
    test_agent_communications()

#!/usr/bin/env python3
"""
Direct test for collaborative decision agent
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

def test_collaborative_decision():
    """Test collaborative decision agent directly"""
    try:
        # Import the collaborative decision agent
        sys.path.insert(0, '.')
        from agents.collaborative_decision_agent import CollaborativeDecisionFramework
        
        print("Successfully imported CollaborativeDecisionFramework")
        
        # Create logs directory
        os.makedirs('data/logs', exist_ok=True)
        
        # Configure collaborative decision log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        collab_log_file = f'data/logs/collab_decision_test_{timestamp}.log'
        
        # Set up file handler for logging
        file_handler = logging.FileHandler(collab_log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create a formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.addHandler(file_handler)
        
        # Log start message
        logger.info("=== COLLABORATIVE DECISION TEST STARTED ===")
        print(f"Logging to {collab_log_file}")
        
        # Create a collaborative decision framework
        print("Creating collaborative decision framework...")
        framework = CollaborativeDecisionFramework(use_local_llm=True)
        print("Created collaborative decision framework")
        
        # Run a decision session
        print("Running a test decision session...")
        symbol = "BTCUSDT"
        prompt = "Analyze the current market conditions and provide a trading recommendation."
        
        logger.info(f"Running decision session for {symbol} with prompt: {prompt}")
        result = framework.run_decision_session(symbol, prompt)
        
        print(f"Decision session completed")
        logger.info(f"Decision session result: {result}")
        
        # Log completion message
        logger.info("=== COLLABORATIVE DECISION TEST COMPLETED ===")
        print("Test completed, check the log file for results")
        
    except Exception as e:
        print(f"Error running collaborative decision test: {e}")
        import traceback
        traceback_str = traceback.format_exc()
        print(traceback_str)
        logger.error(f"Error: {e}")
        logger.error(traceback_str)

if __name__ == '__main__':
    test_collaborative_decision()

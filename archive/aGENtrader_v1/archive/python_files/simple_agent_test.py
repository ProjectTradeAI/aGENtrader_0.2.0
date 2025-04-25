#!/usr/bin/env python3
"""
Simple test for agent communications with the actual agent implementation
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

def main():
    """Main function"""
    print("Simple Agent Test")
    print("================")
    
    # Create logs directory
    os.makedirs('data/logs', exist_ok=True)
    
    # Import and apply agent logging patch
    try:
        print("Importing agent_logging_patch...")
        from agent_logging_patch import monkey_patch_agent_framework
        print("Applying monkey patch for agent logging...")
        monkey_patch_agent_framework()
        print("Agent logging patch applied successfully")
    except Exception as e:
        print(f"Error with agent logging patch: {e}")
        import traceback
        print(traceback.format_exc())
    
    # Import the collaborative decision agent
    try:
        print("Importing collaborative_decision_agent...")
        sys.path.insert(0, '.')
        from agents.collaborative_decision_agent import CollaborativeDecisionFramework
        print("Successfully imported CollaborativeDecisionFramework")
        
        # Create a collaborative decision framework with correct parameters
        print("Creating collaborative decision framework...")
        framework = CollaborativeDecisionFramework(
            api_key=os.environ.get('OPENAI_API_KEY'),  # This will be None if not set
            llm_model="gpt-3.5-turbo",
            temperature=0.1,
            max_session_time=120
        )
        print("Created collaborative decision framework")
        
        # Run a simple decision session
        print("Running a decision session...")
        symbol = "BTCUSDT"
        prompt = "Analyze the current market conditions and provide a trading recommendation."
        result = framework.run_decision_session(symbol, prompt)
        print(f"Decision session completed with result: {result}")
        
    except Exception as e:
        print(f"Error with collaborative decision framework: {e}")
        import traceback
        print(traceback.format_exc())
    
    print("Test completed")

if __name__ == '__main__':
    main()

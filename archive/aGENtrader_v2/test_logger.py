"""
Test script for the centralized logging utility.

This script demonstrates the usage of the centralized logger across different modules.
"""

import time
from utils.logger import get_logger
from models.llm_client import LLMClient, MockLLMProvider
from data.database import DatabaseConnector

def test_logger_across_modules():
    """Test the centralized logger across different modules."""
    # Get logger for this test script
    logger = get_logger("test_logger")
    logger.info("Starting logger test across modules")
    
    try:
        # Create and use a mock LLM provider
        logger.info("Testing LLM module logging")
        mock_llm = MockLLMProvider()
        mock_llm.generate("Test prompt for logging")
        
        # Create and use a LLM client
        logger.info("Testing LLM client logging")
        llm_client = LLMClient(provider="mock")
        llm_client.generate("Another test prompt for logging")
        
        # Attempt to connect to database (will log even if connection fails)
        logger.info("Testing database module logging")
        db = DatabaseConnector(connection_string="sqlite:///:memory:")
        
        # Access the log file to verify content
        logger.info("Checking log file content")
        import os
        log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "aGENtrader_v2", "logs", "agent_output.log")
        
        if os.path.exists(log_file):
            logger.info(f"Log file exists at: {log_file}")
            with open(log_file, 'r') as f:
                last_lines = f.readlines()[-10:]  # Get the last 10 lines
                logger.info(f"Last few log entries: {len(last_lines)} lines")
        else:
            logger.warning(f"Log file not found at expected location: {log_file}")
        
        logger.info("Logger test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Logger test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing centralized logging utility...")
    success = test_logger_across_modules()
    print(f"Logger test {'succeeded' if success else 'failed'}")
    print("Check the logs directory for the complete log output.")
"""
Simple Test for Local LLM

This script performs a minimal test of the local LLM integration
by downloading the model and generating a simple response.
"""

import os
import sys
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_simple_llm")

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_simple_completion():
    """Runs a simple test of the local LLM"""
    try:
        # Import the local LLM module after setting up the path
        from utils.llm_integration import LocalChatCompletion
        
        # Start time
        start_time = time.time()
        
        # Simple message
        logger.info("Sending a simple message to the model...")
        result = LocalChatCompletion.create(
            messages=[
                {"role": "user", "content": "Hello, how are you?"}
            ],
            temperature=0.7,
            max_tokens=50,  # Short response for quick testing
            timeout=15  # Set a 15-second timeout
        )
        
        # End time
        end_time = time.time()
        
        # Log the result
        logger.info(f"Response time: {end_time - start_time:.2f} seconds")
        logger.info(f"Response content: {result['choices'][0]['message']['content']}")
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting simple test for local LLM...")
    success = test_simple_completion()
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed. Check logs for details.")
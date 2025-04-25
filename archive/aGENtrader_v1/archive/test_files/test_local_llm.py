"""
Test Local LLM Integration

This script tests the local LLM integration by running a simple chat completion request.
It validates that the local LLM can be loaded and used to generate completions.
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_local_llm")

# Add utils to path to allow direct imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import local modules
from utils.llm_integration import (
    LocalLLM, 
    LocalChatCompletion,
    local_llm_client,
    clear_model,
    LLMRouter,
    llm_router
)

def test_local_llm_direct():
    """
    Tests the LocalLLM class directly.
    """
    logger.info("Testing LocalLLM directly...")
    
    with LocalLLM() as llm:
        start_time = time.time()
        
        completion = llm.chat_completion_create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What's the current price of Bitcoin?"}
            ],
            temperature=0.7,
            max_tokens=256
        )
        
        end_time = time.time()
        
        logger.info(f"Completion generated in {end_time - start_time:.2f} seconds")
        logger.info(f"Output: {completion['choices'][0]['message']['content']}")
        
        return completion


def test_local_chat_completion():
    """
    Tests the LocalChatCompletion static class.
    """
    logger.info("Testing LocalChatCompletion static API...")
    
    start_time = time.time()
    
    completion = LocalChatCompletion.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is technical analysis in cryptocurrency trading?"}
        ],
        temperature=0.7,
        max_tokens=256
    )
    
    end_time = time.time()
    
    logger.info(f"Completion generated in {end_time - start_time:.2f} seconds")
    logger.info(f"Output: {completion['choices'][0]['message']['content']}")
    
    return completion


def test_llm_router():
    """
    Tests the LLM router with different agent types.
    """
    logger.info("Testing LLM router...")
    
    # Test with an analyst agent (should use local LLM)
    logger.info("Testing with an analyst agent (should use local LLM)...")
    completion_analyst = llm_router.chat_completion_create(
        messages=[
            {"role": "system", "content": "You are a market analyst."},
            {"role": "user", "content": "Analyze the current trend of Bitcoin."}
        ],
        agent_name="GlobalMarketAnalyst",
        temperature=0.7,
        max_tokens=256
    )
    
    logger.info(f"Analyst completion provider: {completion_analyst.get('model', 'unknown')}")
    logger.info(f"Analyst output: {completion_analyst['choices'][0]['message']['content']}")
    
    # Try with a decision agent (should use OpenAI if available)
    try:
        logger.info("Testing with a decision agent (should use OpenAI if available)...")
        completion_decision = llm_router.chat_completion_create(
            messages=[
                {"role": "system", "content": "You are a trading decision agent."},
                {"role": "user", "content": "Should I buy Bitcoin now?"}
            ],
            agent_name="TradingDecisionAgent",
            temperature=0.7,
            max_tokens=256
        )
        
        logger.info(f"Decision completion provider: {completion_decision.get('model', 'unknown')}")
        logger.info(f"Decision output: {completion_decision['choices'][0]['message']['content']}")
    except Exception as e:
        logger.warning(f"OpenAI test failed, but this is expected if API key isn't set: {str(e)}")
    
    return {
        "analyst": completion_analyst
    }


def main():
    """
    Main test function that runs all tests.
    """
    try:
        # Run tests
        direct_result = test_local_llm_direct()
        static_result = test_local_chat_completion()
        router_result = test_llm_router()
        
        # Clean up
        clear_model()
        llm_router.cleanup()
        
        logger.info("All tests completed successfully!")
        
        return {
            "direct": direct_result,
            "static": static_result,
            "router": router_result
        }
    
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test the LLM integration with TinyLlama
"""
import os
import sys
import logging
import argparse
from utils.llm_integration import LocalLLMAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_llm")

def test_llm_integration():
    """Test the LLM integration"""
    
    # Create LLM client
    logger.info("Creating LLM client")
    client = LocalLLMAPIClient()
    
    # Test basic completion
    prompt = "What is the price of Bitcoin in 2025?"
    
    logger.info(f"Testing completion with prompt: '{prompt}'")
    
    try:
        # Generate completion
        response = client.completion(
            model="local",
            prompt=prompt,
            temperature=0.7,
            max_tokens=100
        )
        
        # Extract and print response
        if response and "choices" in response:
            text = response["choices"][0].get("text", "")
            logger.info(f"Response: {text}")
            print("\nResponse:", text)
            return True
        else:
            logger.error(f"Invalid response: {response}")
            return False
            
    except Exception as e:
        logger.error(f"Error generating completion: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
def test_chat_completion():
    """Test the chat completion"""
    
    # Create LLM client
    logger.info("Creating LLM client for chat completion")
    client = LocalLLMAPIClient()
    
    # Test chat messages
    messages = [
        {"role": "system", "content": "You are a cryptocurrency trading assistant with expertise in Bitcoin."},
        {"role": "user", "content": "What's your prediction for Bitcoin's price in 2025?"}
    ]
    
    logger.info(f"Testing chat completion with messages: {messages}")
    
    try:
        # Generate chat completion
        response = client.chat_completion_create(
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        
        # Extract and print response
        if response and "choices" in response:
            content = response["choices"][0].get("message", {}).get("content", "")
            logger.info(f"Chat response: {content}")
            print("\nChat response:", content)
            return True
        else:
            logger.error(f"Invalid chat response: {response}")
            return False
            
    except Exception as e:
        logger.error(f"Error generating chat completion: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test LLM integration")
    parser.add_argument("--chat", action="store_true", help="Test chat completion instead of basic completion")
    
    args = parser.parse_args()
    
    if args.chat:
        logger.info("Testing chat completion")
        success = test_chat_completion()
    else:
        logger.info("Testing basic completion")
        success = test_llm_integration()
        
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
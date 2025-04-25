#!/usr/bin/env python3
"""
Special test to verify GroupChatManager configuration is fixed
"""

import os
import json
import logging
from datetime import datetime

try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent
except ImportError:
    print("AutoGen is not available. Please install it with 'pip install pyautogen'")
    exit(1)

# Import the specific function we fixed
from agents.autogen_db_integration import create_speaker_llm_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("group_chat_test")

def test_group_chat_config():
    """Test that the GroupChatManager configuration is correct"""
    logger.info("Testing GroupChatManager configuration")
    
    # Basic configuration with functions
    base_config = {
        "model": "gpt-3.5-turbo-0125",
        "temperature": 0.2,
        "config_list": [{"model": "gpt-3.5-turbo-0125", "api_key": os.environ.get("OPENAI_API_KEY")}],
        "functions": [
            {
                "name": "test_function",
                "description": "A test function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "A test parameter"}
                    },
                    "required": ["param1"]
                }
            }
        ]
    }
    
    # Create a clean config for GroupChatManager
    clean_config = create_speaker_llm_config(base_config)
    
    # Verify functions were removed
    has_functions = "functions" in clean_config
    
    logger.info(f"Original config has functions: {bool(base_config.get('functions'))}")
    logger.info(f"Clean config has functions: {has_functions}")
    
    # Print configs for comparison
    print("\nOriginal Config:")
    print(json.dumps(base_config, indent=2))
    
    print("\nClean Config for GroupChatManager:")
    print(json.dumps(clean_config, indent=2))
    
    # Test result
    if not has_functions:
        logger.info("✅ SUCCESS: create_speaker_llm_config correctly removes functions")
        return True
    else:
        logger.error("❌ FAILED: create_speaker_llm_config did not remove functions")
        return False

if __name__ == "__main__":
    test_group_chat_config()
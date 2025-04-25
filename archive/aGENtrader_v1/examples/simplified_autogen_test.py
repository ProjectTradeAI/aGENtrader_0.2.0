#!/usr/bin/env python3
"""
Simplified test for AutoGen with local LLM integration.
This example creates a simple assistant and user chat.
"""
import os
import sys
import logging

# Add project root to path for importing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("autogen_test")

# Try to import our LLM integration
try:
    from utils.llm_integration import AutoGenLLMConfig
    logger.info("LLM integration module imported successfully")
except ImportError:
    logger.error("Failed to import LLM integration module")
    sys.exit(1)

# Try to import AutoGen
try:
    import autogen
    logger.info("AutoGen imported successfully")
except ImportError:
    logger.error("Failed to import AutoGen")
    sys.exit(1)

def test_autogen_local_llm():
    """
    Test AutoGen with our local LLM integration
    """
    logger.info("Testing AutoGen with local LLM")
    
    # Patch AutoGen to use our local LLM
    AutoGenLLMConfig.patch_autogen()
    
    # Create LLM config for agents
    assistant_config = AutoGenLLMConfig.create_llm_config(
        agent_name="Assistant",
        temperature=0.7,
        use_local_llm=True
    )
    
    # Create assistant agent
    assistant = autogen.AssistantAgent(
        name="Assistant",
        system_message="You are a helpful assistant with expertise in cryptocurrency trading.",
        llm_config=assistant_config
    )
    
    # Create user proxy agent (this agent will get input from us)
    user_proxy = autogen.UserProxyAgent(
        name="User",
        human_input_mode="NEVER"  # Don't ask for human input
    )
    
    # Start conversation - assistant will use local LLM
    logger.info("Starting conversation")
    user_proxy.initiate_chat(
        assistant,
        message="What is the current trend for Bitcoin in 2025?"
    )
    
    logger.info("Conversation completed")
    
    # Print final conversation
    logger.info("-- Chat History --")
    for message in user_proxy.chat_messages[assistant]:
        sender = "User" if message["role"] == "user" else "Assistant"
        content = message["content"]
        logger.info(f"{sender}: {content}")
        
    return True

if __name__ == "__main__":
    test_autogen_local_llm()
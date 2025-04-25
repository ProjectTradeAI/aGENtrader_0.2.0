"""
Test AutoGen with Local LLM Integration

This script demonstrates how to use the local LLM integration with AutoGen
by creating a simple multi-agent conversation using the local LLM.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_autogen_local_llm")

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Check if AutoGen is installed
try:
    import autogen
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logger.error("AutoGen is not installed. Please install it with 'pip install pyautogen'")
    sys.exit(1)

# Import our local LLM integration
from utils.llm_integration import (
    AutoGenLLMConfig,
    LocalLLMAPIClient,
    clear_model
)


def setup_agents():
    """
    Sets up a simple conversation between an analyst agent and a decision agent.
    
    Returns:
        Tuple of (analyst_agent, decision_agent)
    """
    # Patch AutoGen to use our local LLM
    AutoGenLLMConfig.patch_autogen()
    
    # Create config for the analyst agent (uses local LLM)
    analyst_config = AutoGenLLMConfig.create_llm_config(
        agent_name="GlobalMarketAnalyst",
        temperature=0.7
    )
    
    # Create config for the decision agent (uses OpenAI if available)
    decision_config = AutoGenLLMConfig.create_llm_config(
        agent_name="TradingDecisionAgent",
        temperature=0.3
    )
    
    # Create the analyst agent
    analyst_agent = autogen.AssistantAgent(
        name="MarketAnalyst",
        system_message="You are a Market Analyst. You analyze cryptocurrency market trends and provide insights.",
        llm_config=analyst_config
    )
    
    # Create the decision agent
    decision_agent = autogen.AssistantAgent(
        name="DecisionAgent",
        system_message="You are a Trading Decision Agent. You make trading decisions based on market analysis.",
        llm_config=decision_config
    )
    
    # Create a user proxy agent
    user_proxy = autogen.UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        is_termination_msg=lambda x: "TERMINATE" in x.get("content", "")
    )
    
    return analyst_agent, decision_agent, user_proxy


def run_conversation():
    """
    Runs a simple conversation between the agents.
    """
    if not AUTOGEN_AVAILABLE:
        logger.error("AutoGen is not available")
        return
    
    # Setup agents
    analyst, decision_agent, user_proxy = setup_agents()
    
    # Start the conversation
    user_proxy.initiate_chat(
        analyst,
        message="Analyze the current trend of Bitcoin and provide key technical indicators."
    )
    
    # Get analysis from the analyst and pass to decision agent
    analysis = user_proxy.last_message()["content"]
    logger.info(f"Analyst response: {analysis}")
    
    # Ask decision agent for a decision
    user_proxy.initiate_chat(
        decision_agent,
        message=f"Based on this analysis from our market analyst, what trading decision would you make?\n\n{analysis}"
    )
    
    # Get decision
    decision = user_proxy.last_message()["content"]
    logger.info(f"Decision agent response: {decision}")
    
    # Clean up
    clear_model()
    
    return {
        "analysis": analysis,
        "decision": decision
    }


def main():
    """
    Main function.
    """
    try:
        logger.info("Testing AutoGen with local LLM integration...")
        results = run_conversation()
        logger.info("Test completed successfully")
        return results
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
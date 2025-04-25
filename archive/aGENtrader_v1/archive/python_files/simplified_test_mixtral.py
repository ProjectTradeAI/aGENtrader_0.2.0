"""
Simplified Test Script for Mixtral model integration with AutoGen
"""

import os
import json
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Import AutoGen
    import autogen
    
    # Try to import our custom autogen_integration
    from utils.llm_integration.autogen_integration import get_llm_config, create_local_llm_config
    
    # Print current time
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get and print the current LLM config
    llm_config = get_llm_config()
    print(f"Current LLM config: {json.dumps(llm_config, indent=2)}")
    
    # Create a basic agent config
    config_list = llm_config.get("config_list", [])
    if not config_list:
        print("ERROR: No config_list found in llm_config")
        sys.exit(1)
    
    print(f"Model being used: {config_list[0].get('model', 'unknown')}")
    
    # Create a basic agent to test the model
    assistant = autogen.AssistantAgent(
        name="assistant",
        llm_config=llm_config,
        system_message="You are a helpful assistant."
    )
    
    user = autogen.UserProxyAgent(
        name="user",
        human_input_mode="never",
        max_consecutive_auto_reply=0
    )
    
    # Test the model with a simple query
    print("\nTesting model response...")
    user.initiate_chat(
        assistant, 
        message="Analyze the following crypto market situation and provide your thoughts: Bitcoin just broke above its previous all-time high and volume is increasing."
    )
    
    print("\nMixtral model test completed successfully!")
    
except Exception as e:
    print(f"Error during testing: {str(e)}")
    import traceback
    traceback.print_exc()

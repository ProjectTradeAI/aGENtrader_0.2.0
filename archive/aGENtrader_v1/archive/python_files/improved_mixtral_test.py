"""
Improved Test Script for Mixtral model integration with AutoGen

This script includes error handling and package installation verification.
"""

import os
import json
import sys
import subprocess
from datetime import datetime

def ensure_package_installed(package_name):
    """Check if a package is installed and install it if not present"""
    print(f"Checking for {package_name}...")
    try:
        __import__(package_name)
        print(f"{package_name} is already installed.")
        return True
    except ImportError:
        print(f"{package_name} not found. Attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"Successfully installed {package_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package_name}: {e}")
            return False

def main():
    # Print current time
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Add parent directory to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Ensure required packages are installed
    if not ensure_package_installed("llama_cpp"):
        print("ERROR: Required package llama_cpp could not be installed. Test cannot proceed.")
        return 1
    
    try:
        # Import AutoGen
        import autogen
        
        # Try to import our custom autogen_integration
        from utils.llm_integration.autogen_integration import get_llm_config, create_local_llm_config
        
        # Get and print the current LLM config
        llm_config = get_llm_config()
        print(f"Current LLM config: {json.dumps(llm_config, indent=2)}")
        
        # Create a basic agent config
        config_list = llm_config.get("config_list", [])
        if not config_list:
            print("ERROR: No config_list found in llm_config")
            return 1
        
        # Check the model being used
        model_name = config_list[0].get('model', 'unknown')
        print(f"Model being used: {model_name}")
        
        # Check if we're using Mixtral
        if 'mixtral' not in model_name.lower():
            print(f"WARNING: Not using Mixtral model. Using {model_name} instead.")
        
        # Create a basic agent to test the model
        assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config=llm_config,
            system_message="You are a helpful assistant specialized in cryptocurrency market analysis."
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
        return 0
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
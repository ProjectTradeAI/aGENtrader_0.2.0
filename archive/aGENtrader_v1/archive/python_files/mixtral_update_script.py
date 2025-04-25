"""
Update AutoGen configuration for Mixtral 8x7B model integration

This script modifies the necessary configuration files to use the Mixtral model
instead of TinyLlama in the agent trading system.
"""

import os
from pathlib import Path
import re
import shutil
import sys


def update_local_llm_module():
    """
    Update the local_llm.py file to use Mixtral instead of TinyLlama
    """
    local_llm_path = Path("utils/llm_integration/local_llm.py")
    
    if not local_llm_path.exists():
        print(f"Error: {local_llm_path} not found")
        return False
    
    # Create a backup
    backup_path = local_llm_path.with_suffix(".py.bak")
    shutil.copyfile(local_llm_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    # Read the current content
    with open(local_llm_path, 'r') as f:
        content = f.read()
    
    # Update model repository
    content = re.sub(
        r'DEFAULT_MODEL_REPO = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"',
        'DEFAULT_MODEL_REPO = "TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF"',
        content
    )
    
    # Update model filename
    content = re.sub(
        r'DEFAULT_MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"',
        'DEFAULT_MODEL_FILE = "mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"',
        content
    )
    
    # Update model path
    content = re.sub(
        r'DEFAULT_MODEL_PATH = os\.path\.join\(.*?"../../models/llm_models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"\)',
        'DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '
        '"../../models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf")',
        content
    )
    
    # Update context length for Mixtral
    content = re.sub(
        r'DEFAULT_CONTEXT_LENGTH = 2048',
        'DEFAULT_CONTEXT_LENGTH = 4096',  # Mixtral supports longer context
        content
    )
    
    # Update model name in results
    content = re.sub(
        r'"model": "local-tinyllama-1.1b-chat"',
        '"model": "local-mixtral-8x7b-instruct"',
        content
    )
    
    # Write the updated content
    with open(local_llm_path, 'w') as f:
        f.write(content)
    
    print(f"Updated {local_llm_path}")
    return True


def update_autogen_integration():
    """
    Update autogen_integration.py to use Mixtral
    """
    autogen_path = Path("utils/llm_integration/autogen_integration.py")
    
    if not autogen_path.exists():
        print(f"Error: {autogen_path} not found")
        return False
    
    # Create a backup
    backup_path = autogen_path.with_suffix(".py.bak")
    shutil.copyfile(autogen_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    # Read the current content
    with open(autogen_path, 'r') as f:
        content = f.read()
    
    # Update model name
    content = re.sub(
        r'"model": "local-tinyllama-1.1b-chat"',
        '"model": "local-mixtral-8x7b-instruct"',
        content
    )
    
    # Write the updated content
    with open(autogen_path, 'w') as f:
        f.write(content)
    
    print(f"Updated {autogen_path}")
    return True


def create_mixtral_test_script():
    """
    Create a test script for the Mixtral model
    """
    test_script_path = Path("test_mixtral_integration.py")
    
    test_script = """
import os
import sys
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

try:
    # First check if the model file exists
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                            "models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf")
    
    if not os.path.exists(model_path):
        print(f"ERROR: Mixtral model file not found at {model_path}")
        sys.exit(1)
    else:
        print(f"Mixtral model file found: {model_path}")
        print(f"File size: {os.path.getsize(model_path) / (1024 * 1024 * 1024):.2f} GB")
    
    # Attempt to import dependencies
    try:
        from llama_cpp import Llama
        print("Successfully imported llama_cpp")
    except ImportError:
        print("llama_cpp not installed. The model will not work until this package is installed.")
        print("Run: pip install llama-cpp-python")
        sys.exit(1)
    
    # Import AutoGen and our custom integration
    import autogen
    from utils.llm_integration.autogen_integration import get_llm_config, AutoGenLLMConfig
    
    # Check the AutoGen integration configuration
    llm_config = get_llm_config()
    config_list = llm_config.get("config_list", [])
    
    if not config_list:
        print("ERROR: No config_list found in llm_config")
        sys.exit(1)
    
    model_name = config_list[0].get('model', 'unknown')
    print(f"Model being used: {model_name}")
    
    if 'mixtral' not in model_name.lower():
        print(f"WARNING: Not using Mixtral model. Using {model_name} instead.")
        print("The configuration may need to be updated.")
    else:
        print(f"SUCCESS: Configuration correctly set to use Mixtral model.")
    
    # Test loading the model (this may take some time)
    print(f"Attempting to load the model. This may take some time...")
    try:
        model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=2,  # Use fewer threads to avoid overwhelming the system
            n_gpu_layers=0  # No GPU in our environment
        )
        print("Model loaded successfully!")
        
        # Test a simple completion to verify the model works
        prompt = "[INST] What are three important factors when analyzing cryptocurrency markets? [/INST]"
        print("Generating response to prompt:", prompt)
        
        start_time = time.time()
        output = model.create_completion(
            prompt=prompt,
            max_tokens=128,
            temperature=0.7,
            echo=False
        )
        end_time = time.time()
        
        print(f"Response generated in {end_time - start_time:.2f} seconds")
        print("\\nResponse:")
        print(output['choices'][0]['text'])
        
        print("\\nMixtral model integration test completed successfully!")
    except Exception as e:
        print(f"Error loading or using the model: {str(e)}")
        print("This may be due to memory constraints or other environmental factors.")
        print("Even though the model file exists, additional setup may be needed.")
    
except Exception as e:
    print(f"Error during testing: {str(e)}")
    import traceback
    traceback.print_exc()
"""
    
    with open(test_script_path, 'w') as f:
        f.write(test_script)
    
    print(f"Created test script: {test_script_path}")
    return True


def main():
    """Main function to update configuration and create test script"""
    print("Updating AutoGen configuration for Mixtral 8x7B integration")
    
    success = True
    
    # Update local_llm.py
    if not update_local_llm_module():
        success = False
    
    # Update autogen_integration.py
    if not update_autogen_integration():
        success = False
    
    # Create test script
    if not create_mixtral_test_script():
        success = False
    
    if success:
        print("\nSuccessfully updated configuration for Mixtral 8x7B integration")
        print("To complete the integration:")
        print("1. Ensure llama-cpp-python is installed: pip install llama-cpp-python")
        print("2. Verify the Mixtral model file exists in models/llm_models/")
        print("3. Run the test script: python test_mixtral_integration.py")
    else:
        print("\nEncountered errors during configuration update")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
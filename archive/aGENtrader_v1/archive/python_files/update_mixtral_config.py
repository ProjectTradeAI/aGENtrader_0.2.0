"""
Update AutoGen Configuration for Mixtral

This script updates the AutoGen configuration to use the Mixtral model
"""

import os
import sys
import re
from pathlib import Path

def main():
    # Add parent directory to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Define the file to update
    integration_file = Path("utils/llm_integration/autogen_integration.py")
    local_llm_file = Path("utils/llm_integration/local_llm.py")
    
    if not integration_file.exists():
        print(f"Error: {integration_file} not found")
        return 1
    
    if not local_llm_file.exists():
        print(f"Error: {local_llm_file} not found")
        return 1
    
    # Read the current content
    with open(integration_file, 'r') as f:
        integration_content = f.read()
    
    with open(local_llm_file, 'r') as f:
        local_llm_content = f.read()
    
    # Update AutoGen integration file
    updated_integration = re.sub(
        r'"model": "local-tinyllama-1.1b-chat"',
        '"model": "local-mixtral-8x7b-instruct"',
        integration_content
    )
    
    # Update model creation in local_llm file
    updated_local_llm = re.sub(
        r'DEFAULT_MODEL_REPO = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"',
        'DEFAULT_MODEL_REPO = "TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF"',
        local_llm_content
    )
    
    updated_local_llm = re.sub(
        r'DEFAULT_MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"',
        'DEFAULT_MODEL_FILE = "mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"',
        updated_local_llm
    )
    
    # Update model path and name
    updated_local_llm = re.sub(
        r'DEFAULT_MODEL_PATH = os\.path\.join\(.*?tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"\)',
        'DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '
        '"../../models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf")',
        updated_local_llm
    )
    
    # Update model context length for Mixtral
    updated_local_llm = re.sub(
        r'DEFAULT_CONTEXT_LENGTH = 2048',
        'DEFAULT_CONTEXT_LENGTH = 4096',  # Mixtral supports longer context
        updated_local_llm
    )
    
    # Update model name in the results
    updated_local_llm = re.sub(
        r'"model": "local-tinyllama-1.1b-chat"',
        '"model": "local-mixtral-8x7b-instruct"',
        updated_local_llm
    )
    
    # Write the updated content
    with open(integration_file, 'w') as f:
        f.write(updated_integration)
    
    with open(local_llm_file, 'w') as f:
        f.write(updated_local_llm)
    
    print(f"Updated {integration_file} and {local_llm_file} to use Mixtral model")
    return 0

if __name__ == "__main__":
    sys.exit(main())
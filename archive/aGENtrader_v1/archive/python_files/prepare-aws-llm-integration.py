#!/usr/bin/env python3
"""
AWS LLM Integration Preparation Script

This script updates the local_llm.py file to better support AWS deployment
by adding the necessary modifications to handle larger models and adapt to
more powerful EC2 hardware.
"""

import os
import sys
import re
import shutil
from datetime import datetime

# Path to the local_llm.py file
LOCAL_LLM_PATH = "utils/llm_integration/local_llm.py"

# Backup the original file
def backup_file(file_path):
    """Create a backup of the original file"""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist!")
        return False
    
    backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")
    return True

# Create AWS config file if it doesn't exist
def create_aws_config():
    """Create the AWS config file if it doesn't exist"""
    config_path = "utils/llm_integration/aws_config.py"
    
    if os.path.exists(config_path):
        print(f"AWS config file already exists at {config_path}")
        return
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        f.write("""\"\"\"AWS-specific configuration for LLM integration\"\"\"

# AWS instance-specific settings
AWS_DEPLOYMENT = True

# Model configuration
DEFAULT_MODEL_PATH = "models/llm_models/llama-2-7b-chat.Q4_K_M.gguf"
DEFAULT_MODEL_REPO = "TheBloke/Llama-2-7B-Chat-GGUF"
DEFAULT_MODEL_FILE = "llama-2-7b-chat.Q4_K_M.gguf"

# Performance settings for EC2
import multiprocessing
DEFAULT_CONTEXT_LENGTH = 4096
NUM_THREADS = multiprocessing.cpu_count()  # Use all available CPU cores
N_GPU_LAYERS = 0  # Set to 0 if no GPU, or higher for GPU instances

# Advanced performance settings
BATCH_SIZE = 512  # Higher values may be faster but use more memory
OFFLOAD_KV = True  # Set to True to offload KV cache to CPU when possible
ROPE_SCALING_TYPE = "yarn"  # Better for longer contexts

# Timeout settings (in seconds)
DEFAULT_TIMEOUT = 60
ANALYST_TIMEOUT = 90
DECISION_TIMEOUT = 120
""")
    
    print(f"Created AWS config file at {config_path}")

# Modify the local_llm.py file to support AWS configuration
def update_local_llm():
    """Update the local_llm.py file with AWS support"""
    if not os.path.exists(LOCAL_LLM_PATH):
        print(f"Error: {LOCAL_LLM_PATH} not found!")
        return False
    
    with open(LOCAL_LLM_PATH, 'r') as f:
        content = f.read()
    
    # Add AWS config import
    aws_import = """
# Check if AWS configuration exists
try:
    from .aws_config import (
        AWS_DEPLOYMENT,
        DEFAULT_MODEL_PATH as AWS_MODEL_PATH,
        DEFAULT_MODEL_REPO as AWS_MODEL_REPO,
        DEFAULT_MODEL_FILE as AWS_MODEL_FILE,
        DEFAULT_CONTEXT_LENGTH as AWS_CONTEXT_LENGTH,
        NUM_THREADS as AWS_NUM_THREADS,
        N_GPU_LAYERS as AWS_N_GPU_LAYERS,
        BATCH_SIZE as AWS_BATCH_SIZE,
        OFFLOAD_KV as AWS_OFFLOAD_KV,
        ROPE_SCALING_TYPE as AWS_ROPE_SCALING_TYPE,
    )
    USE_AWS_CONFIG = AWS_DEPLOYMENT
except (ImportError, AttributeError):
    USE_AWS_CONFIG = False
"""
    
    # Find the position to insert AWS import (after normal imports, before constants)
    import_match = re.search(r'import .*?\n\n', content, re.DOTALL)
    if import_match:
        insert_pos = import_match.end()
        content = content[:insert_pos] + aws_import + content[insert_pos:]
    else:
        print("Warning: Could not find appropriate location for AWS import, appending to top")
        content = aws_import + content
    
    # Update constants section
    constants_pattern = r'# Constants.*?DEFAULT_N_GPU_LAYERS\s*=\s*\d+'
    aws_constants = """# Constants
if USE_AWS_CONFIG:
    DEFAULT_MODEL_PATH = AWS_MODEL_PATH
    DEFAULT_MODEL_REPO = AWS_MODEL_REPO
    DEFAULT_MODEL_FILE = AWS_MODEL_FILE
    DEFAULT_CONTEXT_LENGTH = AWS_CONTEXT_LENGTH
    DEFAULT_NUM_THREADS = AWS_NUM_THREADS
    DEFAULT_N_GPU_LAYERS = AWS_N_GPU_LAYERS
    DEFAULT_BATCH_SIZE = AWS_BATCH_SIZE
    DEFAULT_OFFLOAD_KV = AWS_OFFLOAD_KV
    DEFAULT_ROPE_SCALING = AWS_ROPE_SCALING_TYPE
else:
    DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "../../models/llm_models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
    DEFAULT_MODEL_REPO = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
    DEFAULT_MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    DEFAULT_CONTEXT_LENGTH = 2048
    DEFAULT_NUM_THREADS = 2
    DEFAULT_N_GPU_LAYERS = 0
    DEFAULT_BATCH_SIZE = 512
    DEFAULT_OFFLOAD_KV = False
    DEFAULT_ROPE_SCALING = None"""
    
    # Replace constants section
    content = re.sub(constants_pattern, aws_constants, content, flags=re.DOTALL)
    
    # Update get_model function to use the new parameters
    model_init_pattern = r'_thread_local\.model\s*=\s*Llama\(.*?\)'
    new_model_init = """_thread_local.model = Llama(
                model_path=model_path,
                n_ctx=DEFAULT_CONTEXT_LENGTH,
                n_threads=DEFAULT_NUM_THREADS,
                n_gpu_layers=DEFAULT_N_GPU_LAYERS,
                n_batch=DEFAULT_BATCH_SIZE,
                offload_kqv=DEFAULT_OFFLOAD_KV,
                rope_scaling_type=DEFAULT_ROPE_SCALING,
                verbose=False
            )"""
    
    # Replace model initialization
    content = re.sub(model_init_pattern, new_model_init, content, flags=re.DOTALL)
    
    # Add improved memory management function
    clear_model_pattern = r'def clear_model\(\):.*?_thread_local\.model = None'
    new_clear_model = """def clear_model():
    \"\"\"
    Clears the model from thread local storage and runs garbage collection.
    This is useful for managing memory usage in long-running processes.
    \"\"\"
    if hasattr(_thread_local, "model") and _thread_local.model is not None:
        del _thread_local.model
        _thread_local.model = None
        
        # Explicitly run garbage collection
        import gc
        gc.collect()
        
        logger.info("Model cleared from memory and garbage collection run")"""
    
    # Replace clear_model function
    content = re.sub(clear_model_pattern, new_clear_model, content, flags=re.DOTALL)
    
    # Write the updated content
    with open(LOCAL_LLM_PATH, 'w') as f:
        f.write(content)
    
    print(f"Updated {LOCAL_LLM_PATH} with AWS support")
    return True

# Update the autogen_integration.py file to handle AWS settings
def update_autogen_integration():
    """Update the autogen_integration.py file with AWS support"""
    autogen_path = "utils/llm_integration/autogen_integration.py"
    
    if not os.path.exists(autogen_path):
        print(f"Warning: {autogen_path} not found, skipping update")
        return False
    
    with open(autogen_path, 'r') as f:
        content = f.read()
    
    # Add timeout handling from AWS config
    aws_import = """
# Import AWS config if available
try:
    from .aws_config import (
        AWS_DEPLOYMENT,
        DEFAULT_TIMEOUT as AWS_DEFAULT_TIMEOUT,
        ANALYST_TIMEOUT as AWS_ANALYST_TIMEOUT,
        DECISION_TIMEOUT as AWS_DECISION_TIMEOUT
    )
    USE_AWS_CONFIG = AWS_DEPLOYMENT
except (ImportError, AttributeError):
    USE_AWS_CONFIG = False
"""
    
    # Find the position to insert AWS import
    import_match = re.search(r'import .*?\n\n', content, re.DOTALL)
    if import_match:
        insert_pos = import_match.end()
        content = content[:insert_pos] + aws_import + content[insert_pos:]
    else:
        content = aws_import + content
    
    # Update timeout handling
    timeout_pattern = r'DEFAULT_TIMEOUT\s*=\s*\d+'
    aws_timeout = """DEFAULT_TIMEOUT = AWS_DEFAULT_TIMEOUT if USE_AWS_CONFIG else 60
ANALYST_TIMEOUT = AWS_ANALYST_TIMEOUT if USE_AWS_CONFIG else 60
DECISION_TIMEOUT = AWS_DECISION_TIMEOUT if USE_AWS_CONFIG else 90"""
    
    content = re.sub(timeout_pattern, aws_timeout, content)
    
    # Write the updated content
    with open(autogen_path, 'w') as f:
        f.write(content)
    
    print(f"Updated {autogen_path} with AWS timeout settings")
    return True

# Main function
def main():
    """Main function"""
    print("AWS LLM Integration Preparation Script")
    print("======================================")
    
    # Backup local_llm.py
    if not backup_file(LOCAL_LLM_PATH):
        print("Exiting due to backup failure")
        sys.exit(1)
    
    # Create AWS config file
    create_aws_config()
    
    # Update local_llm.py
    update_local_llm()
    
    # Update autogen_integration.py if it exists
    update_autogen_integration()
    
    print("\nAWS LLM integration preparation completed successfully!")
    print("\nNext steps:")
    print("1. Review the changes made to ensure they match your environment")
    print("2. Update aws_config.py with settings specific to your EC2 instance")
    print("3. Deploy to AWS EC2 using the deploy-ec2.sh script")

if __name__ == "__main__":
    main()
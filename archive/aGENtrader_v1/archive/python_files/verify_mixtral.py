
import os
import sys
from pathlib import Path

# Define expected model path
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                        "models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf")

print(f"Checking for Mixtral model at: {model_path}")

if os.path.exists(model_path):
    print(f"SUCCESS: Mixtral model file found!")
    print(f"File size: {os.path.getsize(model_path) / (1024 * 1024 * 1024):.2f} GB")
    
    # Check utils/llm_integration/local_llm.py for references to Mixtral
    local_llm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "utils/llm_integration/local_llm.py")
    
    if os.path.exists(local_llm_path):
        with open(local_llm_path, 'r') as f:
            content = f.read()
            if "mixtral-8x7b" in content.lower():
                print("local_llm.py contains references to Mixtral")
            else:
                print("local_llm.py does NOT contain references to Mixtral")
    
    # Check utils/llm_integration/autogen_integration.py for references to Mixtral
    autogen_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "utils/llm_integration/autogen_integration.py")
    
    if os.path.exists(autogen_path):
        with open(autogen_path, 'r') as f:
            content = f.read()
            if "mixtral-8x7b" in content.lower() or "local-mixtral" in content.lower():
                print("autogen_integration.py contains references to Mixtral")
            else:
                print("autogen_integration.py does NOT contain references to Mixtral")
else:
    print(f"ERROR: Mixtral model file not found at {model_path}")
    
    # Check if models directory exists
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models/llm_models")
    if os.path.exists(models_dir):
        print(f"The models directory exists at {models_dir}")
        print("Contents of models directory:")
        for item in os.listdir(models_dir):
            item_path = os.path.join(models_dir, item)
            size = os.path.getsize(item_path) / (1024 * 1024)  # Size in MB
            print(f"  - {item} ({size:.2f} MB)")
    else:
        print(f"The models directory does not exist at {models_dir}")

"""
Simple test script for Mixtral model

This script creates a Python file to test the Mixtral model integration
and then transfers it to the EC2 instance for execution.
"""
import sys
import os
from pathlib import Path

if __name__ == "__main__":
    # Create the test script content
    test_script = """
import os
import sys
import time
from datetime import datetime

print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

try:
    # Import the Llama model
    try:
        from llama_cpp import Llama
        print("Successfully imported llama_cpp")
    except ImportError:
        print("llama_cpp not installed. Attempting to install...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "llama-cpp-python"])
        from llama_cpp import Llama
        print("Successfully installed and imported llama_cpp")
    
    # Define model path
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                             "models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf")
    
    if not os.path.exists(model_path):
        print(f"ERROR: Model file not found at {model_path}")
        sys.exit(1)
    
    print(f"Loading model from {model_path}...")
    
    # Load the model
    model = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=4,
        n_gpu_layers=0
    )
    
    print("Model loaded successfully!")
    
    # Test a simple prompt
    prompt = "[INST] What are the key factors to consider when analyzing cryptocurrency markets? [/INST]"
    
    print("Generating response...")
    start_time = time.time()
    
    output = model.create_completion(
        prompt=prompt,
        max_tokens=256,
        temperature=0.7,
        echo=False
    )
    
    end_time = time.time()
    print(f"Response generated in {end_time - start_time:.2f} seconds")
    
    print("\\nPrompt:")
    print(prompt)
    print("\\nResponse:")
    print(output['choices'][0]['text'])
    
    print("\\nTest completed successfully!")
    
except Exception as e:
    print(f"Error during testing: {str(e)}")
    import traceback
    traceback.print_exc()
"""

    # Write the test script
    with open("remote_mixtral_test.py", "w") as f:
        f.write(test_script)
    
    print("Created test script: remote_mixtral_test.py")

#!/usr/bin/env python3
"""
Download Mixtral 8x7B GGUF Model

This script downloads the Mixtral 8x7B Instruct model from HuggingFace
and configures the system to use it with AutoGen.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_step(message):
    print(f"\033[0;32m[STEP]\033[0m {message}")

def print_warning(message):
    print(f"\033[0;33m[WARNING]\033[0m {message}")

def print_error(message):
    print(f"\033[0;31m[ERROR]\033[0m {message}")

def install_package(package):
    try:
        print_step(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package])
        return True
    except subprocess.CalledProcessError:
        print_error(f"Failed to install {package}")
        return False

def download_model():
    print_step("Downloading Mixtral 8x7B GGUF model...")
    
    # Configuration
    model_repo = "TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF"
    model_file = "mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"
    models_dir = Path.home() / "aGENtrader" / "models" / "llm_models"
    
    # Create directory if it doesn't exist
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if the model already exists
    model_path = models_dir / model_file
    if model_path.exists():
        print_step(f"Model already exists at {model_path}")
        return True
    
    # Install huggingface_hub if not already installed
    try:
        import huggingface_hub
    except ImportError:
        if not install_package("huggingface_hub"):
            return False
        import huggingface_hub
    
    # Download the model
    try:
        print_step(f"Downloading from {model_repo}...")
        downloaded_path = huggingface_hub.hf_hub_download(
            repo_id=model_repo,
            filename=model_file,
            local_dir=str(models_dir),
            local_dir_use_symlinks=False
        )
        print_step(f"Model downloaded to: {downloaded_path}")
        return True
    except Exception as e:
        print_error(f"Failed to download model: {e}")
        
        # Try using wget as a fallback
        print_warning("Trying wget as a fallback...")
        try:
            wget_url = f"https://huggingface.co/{model_repo}/resolve/main/{model_file}"
            wget_command = ["wget", "-q", "--show-progress", wget_url, "-O", str(model_path)]
            
            subprocess.check_call(wget_command)
            
            if model_path.exists():
                print_step(f"Model downloaded to: {model_path}")
                return True
            else:
                print_error("Download completed but file not found")
                return False
        except Exception as e:
            print_error(f"Wget download failed: {e}")
            return False

def update_autogen_config():
    print_step("Updating AutoGen configuration to use Mixtral model...")
    
    autogen_config_path = Path.home() / "aGENtrader" / "utils" / "llm_integration" / "autogen_integration.py"
    
    if not autogen_config_path.exists():
        print_warning(f"AutoGen configuration file not found at {autogen_config_path}")
        return False
    
    # Create a backup of the original file
    backup_path = autogen_config_path.with_suffix(".py.bak")
    try:
        with open(autogen_config_path, 'r') as f:
            original_content = f.read()
        
        with open(backup_path, 'w') as f:
            f.write(original_content)
        
        # Update the model name in the content
        updated_content = original_content.replace(
            '"model": "local-tinyllama-1.1b-chat"',
            '"model": "local-mixtral-8x7b-instruct"'
        )
        
        # Write the updated content back to the file
        with open(autogen_config_path, 'w') as f:
            f.write(updated_content)
        
        print_step(f"Updated configuration in {autogen_config_path}")
        return True
    except Exception as e:
        print_error(f"Failed to update AutoGen configuration: {e}")
        return False

def main():
    print_step("Starting Mixtral 8x7B setup...")
    
    # Ensure we have necessary packages
    required_packages = ["huggingface_hub", "filelock", "requests", "tqdm"]
    for package in required_packages:
        install_package(package)
    
    # Download the model
    if not download_model():
        print_error("Failed to download Mixtral model")
        return 1
    
    # Update AutoGen configuration
    if not update_autogen_config():
        print_warning("Failed to update AutoGen configuration")
    
    print_step("Mixtral 8x7B setup complete!")
    print("The system is now configured to use Mixtral 8x7B for AutoGen agents.")
    print("You can run backtests with the new model using the ec2-multi-agent-backtest.sh script.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

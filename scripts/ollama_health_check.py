#!/usr/bin/env python3
"""
aGENtrader v2 Ollama Health Check

This script checks if Ollama is running and available, and can optionally
start the service if it's not running. It's designed to work in both local
and EC2 environments.

Usage:
  python3 ollama_health_check.py [--start] [--check-models] [--ec2]

Options:
  --start        Start Ollama if it's not running
  --check-models Check if required models are available
  --ec2          Use EC2-specific commands
"""

import argparse
import os
import subprocess
import sys
import time
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ollama_health_check')

# Required models that should be available
REQUIRED_MODELS = ['mistral', 'mistral:latest']

def check_ollama_installed() -> bool:
    """Check if ollama is installed."""
    try:
        result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking if Ollama is installed: {e}")
        return False

def is_running_in_ec2() -> bool:
    """Detect if running in an EC2 environment."""
    try:
        # Method 1: Check for EC2 metadata service
        response = requests.get('http://169.254.169.254/latest/meta-data/instance-id', timeout=0.1)
        return response.status_code == 200
    except:
        # Method 2: Check for EC2 system indicators
        if os.path.exists('/sys/hypervisor/uuid'):
            with open('/sys/hypervisor/uuid', 'r') as f:
                uuid = f.read().strip()
                if uuid.startswith('ec2'):
                    return True
        
        # Method 3: Check environment variable
        deploy_env = os.environ.get('DEPLOY_ENV', '').lower()
        return deploy_env == 'ec2'

def check_ollama_running(endpoints: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Check if Ollama API is accessible.
    
    Args:
        endpoints: List of endpoints to try
        
    Returns:
        Tuple of (is_running, working_endpoint)
    """
    if endpoints is None:
        endpoints = [
            'http://localhost:11434',
            'http://127.0.0.1:11434',
            'http://0.0.0.0:11434'
        ]
        
        # Add EC2 internal IPs if in EC2 environment
        if is_running_in_ec2():
            # Try to get internal IP
            try:
                metadata_ip = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4', timeout=0.1)
                if metadata_ip.status_code == 200:
                    endpoints.append(f"http://{metadata_ip.text.strip()}:11434")
            except:
                # Use some common EC2 private IPs
                endpoints.append('http://172.31.16.22:11434')
    
    logger.info(f"Checking Ollama on endpoints: {', '.join(endpoints)}")
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 200:
                logger.info(f"Ollama is running at {endpoint}")
                return True, endpoint
        except requests.RequestException as e:
            logger.debug(f"Ollama not available at {endpoint}: {e}")
    
    logger.warning("Ollama is not running on any endpoint")
    return False, None

def check_models_available(endpoint: Optional[str]) -> Dict[str, bool]:
    """
    Check if required models are available in Ollama.
    
    Args:
        endpoint: Working Ollama endpoint
        
    Returns:
        Dictionary with model availability status
    """
    if endpoint is None:
        logger.error("No endpoint provided to check models")
        return {model: False for model in REQUIRED_MODELS}
    model_status = {model: False for model in REQUIRED_MODELS}
    
    try:
        response = requests.get(f"{endpoint}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            available_models = [model.get('name', '') for model in data.get('models', [])]
            
            # Check if each required model is available
            for model in REQUIRED_MODELS:
                if model in available_models:
                    model_status[model] = True
                    logger.info(f"Model {model} is available")
                else:
                    logger.warning(f"Model {model} is not available")
            
            # Log other available models
            other_models = [m for m in available_models if m not in REQUIRED_MODELS]
            if other_models:
                logger.info(f"Other available models: {', '.join(other_models)}")
    except Exception as e:
        logger.error(f"Error checking available models: {e}")
    
    return model_status

def check_ollama_listening_only_on_localhost() -> bool:
    """
    Check if Ollama is running but only listening on localhost/127.0.0.1.
    This happens when Ollama is configured to only bind to localhost.
    
    Returns:
        True if Ollama is running but only on localhost, False otherwise
    """
    try:
        # First check if Ollama is running at localhost or 127.0.0.1
        response_local = False
        try:
            response = requests.get('http://127.0.0.1:11434', timeout=2)
            response_local = response.status_code == 200
        except:
            pass
            
        if not response_local:
            try:
                response = requests.get('http://localhost:11434', timeout=2)
                response_local = response.status_code == 200
            except:
                pass
        
        # If it's running on localhost, check if it's NOT running on 0.0.0.0
        if response_local:
            try:
                response = requests.get('http://0.0.0.0:11434', timeout=2)
                # If we can access it on 0.0.0.0, it's not localhost-only
                if response.status_code == 200:
                    return False
            except:
                # If we can't access it on 0.0.0.0, check netstat to confirm
                try:
                    result = subprocess.run(['sudo', 'netstat', '-tulpn', '|', 'grep', 'ollama'],
                                         shell=True, capture_output=True, text=True)
                    if '127.0.0.1:11434' in result.stdout and '0.0.0.0:11434' not in result.stdout:
                        logger.warning("Ollama detected as running but only on localhost (127.0.0.1)")
                        return True
                except:
                    pass
        
        return False
    except Exception as e:
        logger.error(f"Error checking Ollama localhost binding: {e}")
        return False

def fix_ollama_config_for_all_interfaces(is_ec2: bool = False) -> bool:
    """
    Fix Ollama configuration to listen on all interfaces (0.0.0.0).
    
    Args:
        is_ec2: Whether running in EC2 environment
        
    Returns:
        True if successfully fixed, False otherwise
    """
    logger.info("Fixing Ollama configuration to listen on all interfaces...")
    
    if not is_ec2:
        logger.warning("This fix should only be used in EC2 environment")
        return False
    
    try:
        # Stop Ollama service
        logger.info("Stopping Ollama service...")
        subprocess.run(['sudo', 'systemctl', 'stop', 'ollama'], check=True)
        
        # Create config directory if it doesn't exist
        logger.info("Creating Ollama config directory...")
        subprocess.run(['sudo', 'mkdir', '-p', '/etc/ollama'], check=True)
        
        # Create config file with proper binding
        logger.info("Creating Ollama config to bind to all interfaces...")
        cmd = ['sudo', 'bash', '-c', 'echo "host = \\"0.0.0.0\\"" > /etc/ollama/config']
        subprocess.run(cmd, check=True)
        
        # Start Ollama service
        logger.info("Starting Ollama service with new configuration...")
        subprocess.run(['sudo', 'systemctl', 'start', 'ollama'], check=True)
        
        # Wait for service to start
        time.sleep(5)
        
        # Verify it's running and listening on all interfaces
        try:
            response = requests.get('http://0.0.0.0:11434', timeout=5)
            if response.status_code == 200:
                logger.info("Ollama successfully reconfigured to listen on all interfaces")
                return True
            else:
                logger.warning("Ollama started but not listening on all interfaces")
                return False
        except:
            logger.warning("Could not connect to Ollama on all interfaces after reconfiguration")
            return False
    except Exception as e:
        logger.error(f"Error fixing Ollama configuration: {e}")
        return False

def start_ollama(is_ec2: bool = False) -> bool:
    """
    Start the Ollama server.
    
    Args:
        is_ec2: Whether running in EC2 environment
        
    Returns:
        True if successfully started, False otherwise
    """
    logger.info("Attempting to start Ollama service...")
    
    # First check if Ollama is running but only on localhost
    if is_ec2 and check_ollama_listening_only_on_localhost():
        logger.warning("Ollama is running but only listening on localhost (127.0.0.1)")
        logger.info("Will attempt to fix configuration and restart service")
        if fix_ollama_config_for_all_interfaces(is_ec2=True):
            return True
    
    if is_ec2:
        # Try to start with systemctl first
        try:
            logger.info("Trying to start Ollama with systemctl...")
            result = subprocess.run(['sudo', 'systemctl', 'start', 'ollama'], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Successfully started Ollama with systemctl")
                time.sleep(5)  # Wait for service to initialize
                return True
            else:
                logger.warning(f"Failed to start with systemctl: {result.stderr}")
        except Exception as e:
            logger.warning(f"Error using systemctl: {e}")
        
        # If systemctl fails, try the direct method
        try:
            logger.info("Trying direct method to start Ollama...")
            # Start in background with nohup
            subprocess.Popen(['nohup', 'ollama', 'serve', '>', '/tmp/ollama.log', '2>&1', '&'], 
                            start_new_session=True)
            logger.info("Ollama start command issued, waiting for startup...")
            time.sleep(5)  # Wait for service to initialize
            
            # Check if it's now running
            running, _ = check_ollama_running()
            if running:
                logger.info("Successfully started Ollama with direct method")
                return True
            else:
                logger.warning("Ollama failed to start with direct method")
                return False
        except Exception as e:
            logger.error(f"Error starting Ollama directly: {e}")
            return False
    else:
        # For local environments
        try:
            logger.info("Starting Ollama locally...")
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL, 
                           start_new_session=True)
            
            logger.info("Waiting for Ollama to start...")
            time.sleep(5)  # Wait for service to initialize
            
            # Check if it's now running
            running, _ = check_ollama_running()
            return running
        except Exception as e:
            logger.error(f"Error starting Ollama locally: {e}")
            return False

def pull_required_models(endpoint: Optional[str]) -> bool:
    """
    Pull required models if they're not available.
    
    Args:
        endpoint: Working Ollama endpoint
        
    Returns:
        True if all models are available/pulled, False otherwise
    """
    if endpoint is None:
        logger.error("No endpoint provided to pull models")
        return False
    model_status = check_models_available(endpoint)
    all_available = True
    
    for model in REQUIRED_MODELS:
        if not model_status.get(model, False):
            # Model isn't available, try to pull it
            logger.info(f"Pulling model {model}...")
            try:
                result = subprocess.run(['ollama', 'pull', model], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"Successfully pulled model {model}")
                else:
                    logger.error(f"Failed to pull model {model}: {result.stderr}")
                    all_available = False
            except Exception as e:
                logger.error(f"Error pulling model {model}: {e}")
                all_available = False
    
    return all_available

def get_detailed_status() -> Dict[str, Any]:
    """
    Get detailed status information about Ollama.
    
    Returns:
        Dictionary with status information
    """
    status = {
        "installed": False,
        "running": False,
        "endpoint": None,
        "models": {},
        "environment": "unknown",
        "errors": []
    }
    
    # Detect environment
    if is_running_in_ec2():
        status["environment"] = "ec2"
    else:
        status["environment"] = "local"
    
    # Check if Ollama is installed
    status["installed"] = check_ollama_installed()
    if not status["installed"]:
        status["errors"].append("Ollama is not installed")
        return status
    
    # Check if Ollama is running
    running, endpoint = check_ollama_running()
    status["running"] = running
    status["endpoint"] = endpoint
    
    if not running:
        status["errors"].append("Ollama server is not running")
        return status
    
    # Check models
    model_status = check_models_available(endpoint)
    status["models"] = model_status
    
    missing_models = [model for model, available in model_status.items() if not available]
    if missing_models:
        status["errors"].append(f"Missing required models: {', '.join(missing_models)}")
    
    return status

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Check and manage Ollama health')
    parser.add_argument('--start', action='store_true', help='Start Ollama if not running')
    parser.add_argument('--check-models', action='store_true', help='Check if required models are available')
    parser.add_argument('--ec2', action='store_true', help='Use EC2-specific commands')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    args = parser.parse_args()
    
    # Detect EC2 environment if not specified
    is_ec2 = args.ec2 or is_running_in_ec2()
    if is_ec2:
        logger.info("Running in EC2 environment")
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        logger.error("Ollama is not installed. Please install it first.")
        if args.json:
            print(json.dumps({"status": "error", "message": "Ollama not installed"}))
        sys.exit(1)
    
    # Check if Ollama is running
    running, endpoint = check_ollama_running()
    
    # Start Ollama if it's not running and --start is specified
    if not running and args.start:
        logger.info("Attempting to start Ollama...")
        started = start_ollama(is_ec2)
        if started:
            logger.info("Successfully started Ollama")
            running, endpoint = check_ollama_running()
        else:
            logger.error("Failed to start Ollama")
            if args.json:
                print(json.dumps({"status": "error", "message": "Failed to start Ollama"}))
            sys.exit(1)
    
    # If Ollama is running and we want to check models
    if running and args.check_models:
        model_status = check_models_available(endpoint)
        missing_models = [model for model, available in model_status.items() if not available]
        
        if missing_models:
            logger.warning(f"Missing models: {', '.join(missing_models)}")
            if args.start and endpoint is not None:
                logger.info("Attempting to pull missing models...")
                success = pull_required_models(endpoint)
                if success:
                    logger.info("All required models are now available")
                else:
                    logger.warning("Failed to pull all required models")
                    if args.json:
                        print(json.dumps({
                            "status": "warning", 
                            "message": "Some models are missing",
                            "models": model_status
                        }))
                    sys.exit(1)
        else:
            logger.info("All required models are available")
    
    # Output status
    if args.json:
        status = get_detailed_status()
        print(json.dumps(status))
    
    # Final result
    if running:
        logger.info(f"Ollama health check passed. Endpoint: {endpoint}")
        sys.exit(0)
    else:
        logger.error("Ollama health check failed: service not running")
        sys.exit(1)

if __name__ == "__main__":
    main()
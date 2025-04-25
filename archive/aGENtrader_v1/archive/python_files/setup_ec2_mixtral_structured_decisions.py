"""
Setup Script for EC2 Mixtral Integration with Structured Decision Making

This script prepares an EC2 instance with both Mixtral model integration
and the structured decision making framework for advanced trading analysis.
"""

import argparse
import os
import sys
import subprocess
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            f"data/logs/ec2_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
        logging.StreamHandler()
    ]
)

# Constants
SSH_KEY_PATH = "ec2_ssh_key.pem"
EC2_USER = "ec2-user"
REPO_DIR = "/home/ec2-user/aGENtrader"


def run_local_command(command: str) -> Tuple[bool, str]:
    """
    Run a command on the local machine.
    
    Args:
        command: Command to run
        
    Returns:
        Tuple of (success, output)
    """
    try:
        logging.info(f"Running local command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            logging.error(f"Command failed with exit code {result.returncode}")
            logging.error(f"Error output: {result.stderr.strip()}")
            return False, result.stderr.strip()
    
    except Exception as e:
        logging.error(f"Error running command: {str(e)}")
        return False, str(e)


def run_ssh_command(ec2_public_ip: str, command: str, timeout: int = 60) -> Tuple[bool, str]:
    """
    Run a command on the EC2 instance via SSH.
    
    Args:
        ec2_public_ip: Public IP of the EC2 instance
        command: Command to run on the EC2 instance
        timeout: Command timeout in seconds
        
    Returns:
        Tuple of (success, output)
    """
    ssh_command = (f"ssh -i {SSH_KEY_PATH} -o StrictHostKeyChecking=no "
                  f"-o ConnectTimeout=10 {EC2_USER}@{ec2_public_ip} "
                  f"'cd {REPO_DIR} && {command}'")
    
    return run_local_command(ssh_command)


def check_ec2_connectivity(ec2_public_ip: str) -> bool:
    """
    Check if the EC2 instance is reachable.
    
    Args:
        ec2_public_ip: Public IP of the EC2 instance
        
    Returns:
        True if reachable, False otherwise
    """
    logging.info(f"Checking connectivity to EC2 instance at {ec2_public_ip}")
    
    success, output = run_ssh_command(ec2_public_ip, "echo 'Connection successful'")
    
    if success:
        logging.info("EC2 instance is reachable")
        return True
    else:
        logging.error(f"Failed to connect to EC2 instance: {output}")
        return False


def copy_files_to_ec2(ec2_public_ip: str, local_files: List[str], remote_dir: str) -> bool:
    """
    Copy files to the EC2 instance via SCP.
    
    Args:
        ec2_public_ip: Public IP of the EC2 instance
        local_files: List of local files to copy
        remote_dir: Remote directory to copy files to
        
    Returns:
        True if successful, False otherwise
    """
    logging.info(f"Copying files to EC2 instance: {', '.join(local_files)}")
    
    # Create remote directory if it doesn't exist
    run_ssh_command(ec2_public_ip, f"mkdir -p {remote_dir}")
    
    # Prepare SCP command
    files_str = " ".join(local_files)
    scp_command = (f"scp -i {SSH_KEY_PATH} -o StrictHostKeyChecking=no "
                  f"{files_str} {EC2_USER}@{ec2_public_ip}:{remote_dir}")
    
    success, output = run_local_command(scp_command)
    
    if success:
        logging.info("Files copied successfully")
        return True
    else:
        logging.error(f"Failed to copy files: {output}")
        return False


def check_mixtral_model(ec2_public_ip: str) -> bool:
    """
    Check if the Mixtral model file exists on the EC2 instance.
    
    Args:
        ec2_public_ip: Public IP of the EC2 instance
        
    Returns:
        True if model exists, False otherwise
    """
    logging.info("Checking if Mixtral model file exists on EC2 instance")
    
    model_path = "models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"
    success, output = run_ssh_command(
        ec2_public_ip, 
        f"if [ -f '{model_path}' ]; then echo 'Model exists'; ls -lh '{model_path}'; else echo 'Model not found'; fi"
    )
    
    if success and "Model exists" in output:
        logging.info(f"Mixtral model found: {output}")
        return True
    else:
        logging.warning(f"Mixtral model not found: {output}")
        return False


def install_llama_cpp_python(ec2_public_ip: str) -> bool:
    """
    Install llama-cpp-python on the EC2 instance.
    
    Args:
        ec2_public_ip: Public IP of the EC2 instance
        
    Returns:
        True if successful, False otherwise
    """
    logging.info("Installing llama-cpp-python on EC2 instance")
    
    # Check if already installed
    success, output = run_ssh_command(ec2_public_ip, "pip list | grep llama-cpp-python")
    
    if success and "llama-cpp-python" in output:
        logging.info("llama-cpp-python is already installed")
        return True
    
    # Install llama-cpp-python
    logging.info("Installing llama-cpp-python (this may take some time)...")
    
    # Install with simple options first (no optimizations)
    success, output = run_ssh_command(
        ec2_public_ip,
        "pip install llama-cpp-python --no-cache-dir",
        timeout=300  # Longer timeout for installation
    )
    
    if success:
        logging.info("Successfully installed llama-cpp-python")
        return True
    else:
        logging.error(f"Failed to install llama-cpp-python: {output}")
        return False


def update_configuration_files(ec2_public_ip: str) -> bool:
    """
    Update configuration files on the EC2 instance.
    
    Args:
        ec2_public_ip: Public IP of the EC2 instance
        
    Returns:
        True if successful, False otherwise
    """
    logging.info("Updating configuration files for Mixtral integration")
    
    # Copy the update script to EC2
    if not copy_files_to_ec2(
        ec2_public_ip,
        ["mixtral_update_script.py", "ADVANCED_MIXTRAL_IMPLEMENTATION.md"],
        REPO_DIR
    ):
        return False
    
    # Run the update script
    success, output = run_ssh_command(ec2_public_ip, "python3 mixtral_update_script.py")
    
    if success:
        logging.info("Successfully updated configuration files")
        return True
    else:
        logging.error(f"Failed to update configuration files: {output}")
        return False


def setup_structured_decision_making(ec2_public_ip: str) -> bool:
    """
    Set up structured decision making on the EC2 instance.
    
    Args:
        ec2_public_ip: Public IP of the EC2 instance
        
    Returns:
        True if successful, False otherwise
    """
    logging.info("Setting up structured decision making framework")
    
    # Create required directories
    run_ssh_command(ec2_public_ip, "mkdir -p agents")
    
    # Copy structured decision making files to EC2
    files_to_copy = [
        "agents/structured_decision_extractor.py",
        "agents/collaborative_trading_framework.py",
        "test_structured_decision_making.py",
        "STRUCTURED_AGENT_DECISIONS.md",
        "DATABASE_AUTOGEN_INTEGRATION.md"
    ]
    
    if not copy_files_to_ec2(ec2_public_ip, files_to_copy, REPO_DIR):
        return False
    
    # Run test script to verify framework
    logging.info("Testing structured decision making framework (extractor only)")
    success, output = run_ssh_command(
        ec2_public_ip, 
        "python3 test_structured_decision_making.py --test_type extractor"
    )
    
    if success:
        logging.info("Structured decision making framework set up successfully")
        return True
    else:
        logging.error(f"Failed to verify structured decision making framework: {output}")
        return False


def free_disk_space(ec2_public_ip: str) -> bool:
    """
    Free up disk space on the EC2 instance.
    
    Args:
        ec2_public_ip: Public IP of the EC2 instance
        
    Returns:
        True if successful, False otherwise
    """
    logging.info("Freeing up disk space on EC2 instance")
    
    # Create cleanup script
    cleanup_script = """#!/bin/bash
# Script to clean up disk space

echo "Cleaning up disk space..."

# Remove old log files
find data/logs -type f -name "*.log" -mtime +7 -delete
echo "Removed old log files"

# Remove old JSON output files
find data/outputs -type f -name "*.json" -mtime +7 -delete
echo "Removed old JSON output files"

# Clear pip cache
pip cache purge
echo "Cleared pip cache"

# Remove downloaded package files
sudo yum clean all
echo "Cleaned yum cache"

# Remove temporary files
find /tmp -type f -atime +2 -delete 2>/dev/null
echo "Removed temporary files"

# Show current disk usage
df -h /
"""
    
    # Create cleanup script file
    with open("cleanup_disk_space.sh", "w") as f:
        f.write(cleanup_script)
    
    # Copy cleanup script to EC2
    if not copy_files_to_ec2(ec2_public_ip, ["cleanup_disk_space.sh"], REPO_DIR):
        return False
    
    # Make script executable and run it
    run_ssh_command(ec2_public_ip, "chmod +x cleanup_disk_space.sh")
    success, output = run_ssh_command(ec2_public_ip, "./cleanup_disk_space.sh")
    
    if success:
        logging.info(f"Successfully freed up disk space: {output}")
        return True
    else:
        logging.error(f"Failed to free up disk space: {output}")
        return False


def test_mixtral_integration(ec2_public_ip: str) -> bool:
    """
    Test Mixtral integration on the EC2 instance.
    
    Args:
        ec2_public_ip: Public IP of the EC2 instance
        
    Returns:
        True if successful, False otherwise
    """
    logging.info("Testing Mixtral integration (simple test)")
    
    test_script = """
import os

model_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"
)

print(f"Checking Mixtral model file...")
if os.path.exists(model_path):
    print(f"  ✓ Model exists at: {model_path}")
    print(f"  ✓ File size: {os.path.getsize(model_path) / (1024 * 1024 * 1024):.2f} GB")
else:
    print(f"  ✗ Model file not found at: {model_path}")
    exit(1)

print("Checking for llama-cpp-python...")
try:
    import llama_cpp
    print(f"  ✓ llama-cpp-python installed: {llama_cpp.__version__}")
except ImportError:
    print("  ✗ llama-cpp-python not installed")
    exit(1)

print("Checking local_llm.py configuration...")
try:
    with open("utils/llm_integration/local_llm.py", "r") as f:
        content = f.read()
        if "mixtral-8x7b-instruct" in content.lower():
            print("  ✓ local_llm.py configured for Mixtral")
        else:
            print("  ✗ local_llm.py not configured for Mixtral")
            exit(1)
except Exception as e:
    print(f"  ✗ Error checking local_llm.py: {str(e)}")
    exit(1)

print("All checks passed!")
"""
    
    # Write test script to file
    with open("test_mixtral_setup.py", "w") as f:
        f.write(test_script)
    
    # Copy test script to EC2
    if not copy_files_to_ec2(ec2_public_ip, ["test_mixtral_setup.py"], REPO_DIR):
        return False
    
    # Run test script
    success, output = run_ssh_command(ec2_public_ip, "python3 test_mixtral_setup.py")
    
    if success and "All checks passed" in output:
        logging.info("Mixtral integration test passed")
        logging.info(output)
        return True
    else:
        logging.error(f"Mixtral integration test failed: {output}")
        return False


def main():
    """Main function to run the setup"""
    parser = argparse.ArgumentParser(description="Setup EC2 with Mixtral and Structured Decision Making")
    parser.add_argument("--ip", type=str, help="EC2 public IP address (optional, will use EC2_PUBLIC_IP environment variable if not provided)")
    parser.add_argument("--key", type=str, help="SSH key file path (optional, default is ec2_ssh_key.pem)")
    parser.add_argument("--skip-llama-cpp", action="store_true", help="Skip llama-cpp-python installation")
    parser.add_argument("--cleanup-only", action="store_true", help="Only run disk cleanup")
    args = parser.parse_args()
    
    # Get EC2 public IP
    ec2_public_ip = args.ip or os.environ.get("EC2_PUBLIC_IP")
    if not ec2_public_ip:
        logging.error("EC2 public IP not provided. Use --ip or set EC2_PUBLIC_IP environment variable.")
        return 1
    
    # Use custom SSH key if provided
    global SSH_KEY_PATH
    if args.key:
        SSH_KEY_PATH = args.key
    
    # Create logs directory
    os.makedirs("data/logs", exist_ok=True)
    
    logging.info(f"Starting EC2 setup with IP: {ec2_public_ip}")
    
    # Check EC2 connectivity
    if not check_ec2_connectivity(ec2_public_ip):
        logging.error("Failed to connect to EC2 instance. Exiting.")
        return 1
    
    # If cleanup only, just run disk space cleanup and exit
    if args.cleanup_only:
        free_disk_space(ec2_public_ip)
        return 0
    
    # Free up disk space
    free_disk_space(ec2_public_ip)
    
    # Check if Mixtral model exists
    check_mixtral_model(ec2_public_ip)
    
    # Install llama-cpp-python if not skipped
    if not args.skip_llama_cpp:
        if not install_llama_cpp_python(ec2_public_ip):
            logging.error("Failed to install llama-cpp-python. Continuing anyway...")
    
    # Update configuration files
    if not update_configuration_files(ec2_public_ip):
        logging.error("Failed to update configuration files. Exiting.")
        return 1
    
    # Set up structured decision making
    if not setup_structured_decision_making(ec2_public_ip):
        logging.error("Failed to set up structured decision making. Exiting.")
        return 1
    
    # Test Mixtral integration
    test_mixtral_integration(ec2_public_ip)
    
    logging.info("EC2 setup completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
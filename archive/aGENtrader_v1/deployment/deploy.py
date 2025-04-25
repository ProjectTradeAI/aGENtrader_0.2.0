
#!/usr/bin/env python3
"""
EC2 Deployment Script for Trading Bot

This script automates deploying the trading bot from Replit to EC2
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime

def log(message):
    """Log a message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_command(command, check=True):
    """Run a shell command"""
    log(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
    if result.returncode != 0:
        log(f"Command failed with exit code {result.returncode}")
        log(f"Error: {result.stderr}")
        if check:
            sys.exit(1)
    return result

def load_config():
    """Load deployment configuration"""
    try:
        with open("config/ec2_config.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        log("Deployment config not found. Create config/ec2_config.json with required fields.")
        sys.exit(1)

def check_prerequisites():
    """Check if all prerequisites are met"""
    log("Checking prerequisites...")
    
    # Check if SSH key exists
    if not os.path.exists(config["ssh_key_path"]):
        log(f"SSH key not found at {config['ssh_key_path']}")
        sys.exit(1)
    
    # Check if instance is reachable
    ping_result = run_command(f"ping -c 1 {config['instance_ip']}", check=False)
    if ping_result.returncode != 0:
        log(f"EC2 instance at {config['instance_ip']} is not reachable")
        sys.exit(1)
        
    log("Prerequisites check passed")

def build_project():
    """Build the project for deployment"""
    log("Building project for deployment...")
    
    # Create build directory
    run_command("rm -rf build && mkdir -p build")
    
    # Copy required files
    log("Copying files to build directory...")
    run_command("cp -r agents assistants orchestration data config build/")
    run_command("cp main.py config/settings.json requirements.txt build/")
    
    # Create package if needed
    log("Creating deployment package...")
    run_command("cd build && tar -czf ../deployment.tar.gz .")
    
    log("Build completed successfully")
    
def deploy_to_ec2():
    """Deploy the built package to EC2"""
    log(f"Deploying to EC2 instance {config['instance_ip']}...")
    
    ssh_cmd = f"ssh -i {config['ssh_key_path']} -o StrictHostKeyChecking=no {config['ec2_user']}@{config['instance_ip']}"
    
    # Check if trading-bot directory exists on EC2
    check_dir = run_command(f"{ssh_cmd} '[ -d ~/trading-bot ] && echo \"exists\" || echo \"not exists\"'")
    
    if "not exists" in check_dir.stdout:
        log("Trading bot directory doesn't exist on EC2, creating it...")
        run_command(f"{ssh_cmd} 'mkdir -p ~/trading-bot'")
    
    # Copy deployment package to EC2
    log("Copying deployment package to EC2...")
    run_command(f"scp -i {config['ssh_key_path']} deployment.tar.gz {config['ec2_user']}@{config['instance_ip']}:~/trading-bot/")
    
    # Extract and set up on EC2
    log("Extracting deployment package on EC2...")
    run_command(f"{ssh_cmd} 'cd ~/trading-bot && tar -xzf deployment.tar.gz'")
    
    # Install dependencies
    log("Installing dependencies on EC2...")
    run_command(f"{ssh_cmd} 'cd ~/trading-bot && pip3 install --user -r requirements.txt'")
    
    # Setup PM2 if needed
    log("Setting up PM2 configuration...")
    run_command(f"{ssh_cmd} 'cd ~/trading-bot && [ -f ecosystem.config.js ] || cp /home/ec2-user/trading-bot/config/ecosystem.config.js .'")
    
    log("Deployment completed successfully")

def restart_service():
    """Restart the trading bot service on EC2"""
    log("Restarting trading bot service...")
    
    ssh_cmd = f"ssh -i {config['ssh_key_path']} {config['ec2_user']}@{config['instance_ip']}"
    
    # Stop any running instance
    run_command(f"{ssh_cmd} 'cd ~/trading-bot && pm2 delete trading-bot || true'")
    
    # Start with PM2
    run_command(f"{ssh_cmd} 'cd ~/trading-bot && pm2 start ecosystem.config.js && pm2 save'")
    
    # Check if service started correctly
    time.sleep(5)  # Wait for service to start
    check_result = run_command(f"{ssh_cmd} 'pm2 list | grep trading-bot'")
    
    if "online" in check_result.stdout:
        log("Trading bot service started successfully")
    else:
        log("Warning: Trading bot service may not have started correctly")
    
def verify_deployment():
    """Verify the deployment was successful"""
    log("Verifying deployment...")
    
    ssh_cmd = f"ssh -i {config['ssh_key_path']} {config['ec2_user']}@{config['instance_ip']}"
    
    # Check service logs for errors
    log_result = run_command(f"{ssh_cmd} 'cd ~/trading-bot && tail -n 20 logs/out.log'", check=False)
    
    if log_result.returncode == 0:
        log("Deployment verification completed")
        log("Recent logs from the trading bot:")
        print("\n" + "=" * 80)
        print(log_result.stdout)
        print("=" * 80 + "\n")
    else:
        log("Could not verify deployment by checking logs")

def cleanup():
    """Clean up temporary deployment files"""
    log("Cleaning up deployment files...")
    run_command("rm -rf build deployment.tar.gz")
    log("Cleanup completed")

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description='Deploy Trading Bot to EC2')
    parser.add_argument('--skip-build', action='store_true', help='Skip building the project')
    parser.add_argument('--skip-restart', action='store_true', help='Skip restarting the service')
    args = parser.parse_args()
    
    log("Starting deployment process")
    
    global config
    config = load_config()
    
    check_prerequisites()
    
    if not args.skip_build:
        build_project()
    else:
        log("Skipping build step")
    
    deploy_to_ec2()
    
    if not args.skip_restart:
        restart_service()
    else:
        log("Skipping service restart")
    
    verify_deployment()
    cleanup()
    
    log("Deployment completed successfully")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"Deployment failed: {str(e)}")
        sys.exit(1)

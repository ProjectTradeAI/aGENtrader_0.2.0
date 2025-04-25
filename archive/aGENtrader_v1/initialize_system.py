"""
System Initialization Script

This script initializes the trading system and verifies that all components
are properly configured and working.
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/initialization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

def check_environment():
    """Check if environment variables are set"""
    required_vars = ["OPENAI_API_KEY", "ALPACA_API_KEY", "ALPACA_API_SECRET"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logging.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file")
        return False
    
    logging.info("Environment variables check passed")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import pandas
        import numpy
        import sqlalchemy
        import requests
        logging.info("All required packages are installed")
        return True
    except ImportError as e:
        logging.error(f"Missing dependency: {str(e)}")
        print(f"Error: Missing dependency - {str(e)}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_directory_structure():
    """Check if the directory structure is correct"""
    required_dirs = [
        "agents/technical", "agents/fundamental", "agents/portfolio",
        "data/sources", "data/storage",
        "orchestration",
        "backtesting/core", "backtesting/scripts"
    ]
    
    missing_dirs = [d for d in required_dirs if not os.path.isdir(d)]
    
    if missing_dirs:
        logging.warning(f"Missing directories: {', '.join(missing_dirs)}")
        print(f"Warning: Missing directories: {', '.join(missing_dirs)}")
        return False
    
    logging.info("Directory structure check passed")
    return True

def main():
    """Main initialization function"""
    print("Starting system initialization...")
    logging.info("Starting system initialization")
    
    # Create required directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("results/backtests", exist_ok=True)
    
    # Check environment and dependencies
    env_check = check_environment()
    dep_check = check_dependencies()
    dir_check = check_directory_structure()
    
    if env_check and dep_check and dir_check:
        print("\n✅ System initialization successful!")
        logging.info("System initialization successful")
        return 0
    else:
        print("\n⚠️ System initialization completed with warnings.")
        logging.warning("System initialization completed with warnings")
        return 1

if __name__ == "__main__":
    sys.exit(main())

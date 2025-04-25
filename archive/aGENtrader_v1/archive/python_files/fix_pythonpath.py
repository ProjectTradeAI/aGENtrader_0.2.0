#!/usr/bin/env python3
"""
Fix Python Path for EC2 Backtesting
This script creates necessary Python module paths and __init__.py files.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pythonpath_fix")

def create_directory_structure():
    """Create required directories with __init__.py files"""
    dirs_to_create = [
        "orchestration",
        "utils",
        "agents",
        "utils/test_logging",
        "utils/decision_tracker",
        "agents/database_retrieval_tool"
    ]
    
    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)
        init_file = os.path.join(d, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f'"""\n{d} package\n"""\n')
            logger.info(f"Created {init_file}")
    
    logger.info("Directory structure created successfully")
    return True

def main():
    """Main entry point"""
    logger.info("Starting Python path fix")
    create_directory_structure()
    
    # Print the current directory structure
    logger.info("Current directory structure:")
    os.system("find . -type d | sort")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

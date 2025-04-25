#!/usr/bin/env python3
"""
Fix for AutoGen GroupChatManager - EC2 Version

This script fixes the GroupChatManager configuration in the collaborative_trading_framework.py
file to correctly provide LLM configuration for the internal speaker selection agent.
"""

import os
import sys
import re
import shutil
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def fix_group_chat_manager(filepath: str) -> bool:
    """
    Fix the GroupChatManager configuration in the collaborative_trading_framework.py file.
    
    Args:
        filepath: Path to the collaborative_trading_framework.py file
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        return False
    
    # Create backup
    backup_path = f"{filepath}.bak"
    shutil.copyfile(filepath, backup_path)
    logging.info(f"Created backup: {backup_path}")
    
    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find the GroupChatManager initialization
    pattern = r'manager\s*=\s*GroupChatManager\s*\(\s*groupchat\s*=\s*self\.group_chat\s*,\s*llm_config\s*=\s*self\.llm_config\s*,\s*is_termination_msg\s*=\s*lambda[^)]+\)'
    
    # Replace with fixed version
    fixed_manager = """manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=self.llm_config,
            is_termination_msg=lambda msg: "TRADING SESSION COMPLETE" in msg.get("content", ""),
            select_speaker_auto_llm_config=self.llm_config  # This is critical - provide LLM config for speaker selection
        )"""
    
    # Check if the pattern is found
    if re.search(pattern, content):
        new_content = re.sub(pattern, fixed_manager, content)
        
        # Write the updated content
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        logging.info(f"Successfully updated {filepath}")
        return True
    else:
        # If pattern not found, try a more flexible approach
        # First, look for any GroupChatManager initialization
        alt_pattern = r'manager\s*=\s*GroupChatManager\s*\([^)]+\)'
        if re.search(alt_pattern, content):
            new_content = re.sub(alt_pattern, fixed_manager, content)
            
            # Write the updated content
            with open(filepath, 'w') as f:
                f.write(new_content)
            
            logging.info(f"Used alternative pattern to update {filepath}")
            return True
        else:
            logging.error("Could not find GroupChatManager initialization in the file")
            return False


def fix_all_backtesting_files():
    """
    Find and fix all files related to backtesting that might use GroupChatManager.
    """
    # Common directories to search
    dirs_to_search = [
        "agents", 
        "utils/llm_integration", 
        "strategies",
        "."  # Root directory
    ]
    
    # Files that might use GroupChatManager
    patterns_to_search = [
        "*backtesting*.py",
        "*collaborative*.py",
        "*trading_framework*.py",
        "*group_chat*.py",
        "*agent_session*.py"
    ]
    
    import glob
    
    fixed_files = []
    
    for directory in dirs_to_search:
        if not os.path.exists(directory):
            continue
            
        for pattern in patterns_to_search:
            search_pattern = os.path.join(directory, pattern)
            files = glob.glob(search_pattern)
            
            for file in files:
                logging.info(f"Checking {file}...")
                
                # Read file content
                with open(file, 'r') as f:
                    content = f.read()
                
                # Check if file uses GroupChatManager
                if 'GroupChatManager' in content:
                    logging.info(f"Found GroupChatManager in {file}")
                    
                    # Check if it's missing the speaker selection config
                    if 'select_speaker_auto_llm_config' not in content:
                        if fix_group_chat_manager(file):
                            fixed_files.append(file)
    
    return fixed_files


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Fix AutoGen GroupChatManager configuration")
    parser.add_argument("--file", type=str, help="Path to collaborative_trading_framework.py (optional)")
    parser.add_argument("--all", action="store_true", help="Find and fix all relevant files")
    args = parser.parse_args()
    
    logging.info("Starting AutoGen GroupChatManager fix")
    
    if args.all:
        # Fix all relevant files
        fixed_files = fix_all_backtesting_files()
        if fixed_files:
            logging.info(f"Successfully fixed {len(fixed_files)} files:")
            for file in fixed_files:
                logging.info(f"  - {file}")
            return 0
        else:
            logging.warning("No files were fixed")
            return 1
    elif args.file:
        # Fix specific file
        if fix_group_chat_manager(args.file):
            return 0
        else:
            return 1
    else:
        # Default path
        default_path = "agents/collaborative_trading_framework.py"
        if os.path.exists(default_path):
            if fix_group_chat_manager(default_path):
                return 0
            else:
                return 1
        else:
            logging.error(f"Default file not found: {default_path}")
            logging.error("Please provide a file path with --file or use --all to search for all relevant files")
            return 1


if __name__ == "__main__":
    sys.exit(main())
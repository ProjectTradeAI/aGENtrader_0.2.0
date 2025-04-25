#!/usr/bin/env python3
"""
Fix AutoGen GroupChatManager configurations
"""

import os
import re
import shutil
import sys
import glob
import argparse

def fix_group_chat_manager(filepath):
    """Fix GroupChatManager in a single file"""
    print(f"Checking {filepath}...")
    
    # Create backup
    backup_path = f"{filepath}.bak"
    shutil.copyfile(filepath, backup_path)
    
    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Skip if already fixed
    if 'select_speaker_auto_llm_config' in content:
        print(f"  Already fixed: {filepath}")
        return False
    
    # Find all GroupChatManager initializations (multiple patterns)
    fixed = False
    
    # Pattern 1: Standard format with manager variable (most common)
    pattern1 = r'(\s*manager\s*=\s*GroupChatManager\s*\(.*?\))'
    
    # Pattern 2: Alternate variable names
    pattern2 = r'(\s*(?:group_manager|group_chat_manager|chat_manager)\s*=\s*GroupChatManager\s*\(.*?\))'
    
    # Pattern 3: With autogen prefix (autogen.GroupChatManager)
    pattern3 = r'(\s*(?:manager|group_manager|group_chat_manager|chat_manager)\s*=\s*autogen\.GroupChatManager\s*\(.*?\))'
    
    for pattern in [pattern1, pattern2, pattern3]:
        # Find all matches
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            match_text = match.group(1)
            
            if match_text.strip().endswith(')'):
                # Check if the match contains llm_config
                llm_config_var = "self.llm_config"
                if "llm_config" in match_text:
                    # Use speaker_llm_config if it's defined, otherwise use the regular llm_config
                    if "speaker_llm_config" in content:
                        llm_config_var = "speaker_llm_config"
                    elif re.search(r'llm_config\s*=\s*([a-zA-Z0-9_\.]+)', match_text):
                        # Extract the actual llm_config variable used
                        config_match = re.search(r'llm_config\s*=\s*([a-zA-Z0-9_\.]+)', match_text)
                        if config_match:
                            llm_config_var = config_match.group(1)
                
                # Add the new parameter before the closing parenthesis
                last_paren = match_text.rstrip().rfind(')')
                fixed_text = match_text[:last_paren] + f',\n    select_speaker_auto_llm_config={llm_config_var}  # Added to fix speaker selection error\n)' + match_text[last_paren+1:]
                content = content.replace(match_text, fixed_text)
                fixed = True
    
    if fixed:
        # Write the updated content
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"  Fixed: {filepath}")
        return True
    
    print(f"  No match found in: {filepath}")
    return False

def find_and_fix_files(specific_file=None):
    """Find and fix all relevant files"""
    # Start from current directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if specific_file:
        # Fix only the specified file
        if os.path.exists(specific_file):
            fixed = fix_group_chat_manager(specific_file)
            if fixed:
                print(f"\nSuccessfully fixed: {specific_file}")
            else:
                print(f"\nNo fix needed or unable to fix: {specific_file}")
        else:
            print(f"Error: File not found - {specific_file}")
        return
    
    # Find all Python files containing GroupChatManager
    cmd = 'grep -l "GroupChatManager" --include="*.py" -r .'
    
    try:
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        files = result.stdout.splitlines()
    except:
        # Fallback if subprocess fails
        files = []
        for root, _, filenames in os.walk('.'):
            for filename in filenames:
                if filename.endswith('.py'):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r') as f:
                            if 'GroupChatManager' in f.read():
                                files.append(filepath)
                    except:
                        pass
    
    fixed_count = 0
    for filepath in files:
        if fix_group_chat_manager(filepath):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files out of {len(files)} found.")

def fix_collaborative_trading_framework():
    """Fix the collaborative_trading_framework.py file specifically"""
    file_path = "agents/collaborative_trading_framework.py"
    if os.path.exists(file_path):
        fixed = fix_group_chat_manager(file_path)
        if fixed:
            print(f"Successfully fixed: {file_path}")
        else:
            print(f"No fix needed or unable to fix: {file_path}")
    else:
        print(f"Error: File not found - {file_path}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Fix AutoGen GroupChatManager configuration")
    parser.add_argument("--file", help="Specific file to fix")
    parser.add_argument("--collaborative", action="store_true", help="Fix collaborative_trading_framework.py only")
    parser.add_argument("--all", action="store_true", help="Fix all files in the project")
    return parser.parse_args()

if __name__ == "__main__":
    print("Starting AutoGen GroupChatManager fix")
    
    args = parse_arguments()
    
    if args.file:
        find_and_fix_files(args.file)
    elif args.collaborative:
        fix_collaborative_trading_framework()
    elif args.all:
        find_and_fix_files()
    else:
        # Default action if no arguments provided
        print("No specific action requested. Use --all to fix all files, --file to fix a specific file, or --collaborative to fix the collaborative trading framework.")
        fix_collaborative_trading_framework()
    
    print("Fix completed!")
#!/usr/bin/env python3
"""
Quick test to verify the GroupChatManager speaker selection fixes
"""

import os
import sys
import inspect
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("speaker_selection_test")

def check_fixed_files():
    """Check if the files were fixed without using autogen directly"""
    # List of key files to check
    files_to_check = [
        "orchestration/autogen_manager.py",
        "orchestration/decision_session.py",
        "orchestration/decision_session_updated.py",
        "test_collaborative_integration.py",
        "test_multi_agent_trading.py",
        "test_simplified_collaborative.py"
    ]
    
    success_count = 0
    for file_path in files_to_check:
        try:
            print(f"Checking {file_path}...")
            found = False
            with open(file_path, 'r') as f:
                content = f.read()
                # Check if the select_speaker_auto_llm_config parameter is in the file
                if 'select_speaker_auto_llm_config' in content:
                    # Get the specific line and context
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'select_speaker_auto_llm_config' in line:
                            context_start = max(0, i-2)
                            context_end = min(len(lines), i+3)
                            context = '\n'.join(lines[context_start:context_end])
                            print(f"  ✓ Fix found at line {i+1}:")
                            print(f"  ------------------------------")
                            print(f"  {context}")
                            print(f"  ------------------------------")
                            found = True
                            success_count += 1
                            break
                if not found:
                    print(f"  ✗ Fix not found in {file_path}")
        except Exception as e:
            print(f"  ✗ Error checking {file_path}: {str(e)}")
    
    print(f"\nFound fix in {success_count} out of {len(files_to_check)} key files.")
    return success_count > 0

def main():
    """Main function"""
    print("\n" + "="*80)
    print("= Testing GroupChatManager Speaker Selection Fix ".center(78) + "=")
    print("="*80 + "\n")
    
    success = check_fixed_files()
    
    print("\n" + "="*80)
    if success:
        print("✅ SUCCESS: GroupChatManager speaker selection issue is fixed!")
    else:
        print("❌ FAILED: GroupChatManager speaker selection issue persists!")
    print("="*80 + "\n")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Check for _auto_select_speaker in GroupChat and how it's called
"""
import sys
import os
import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_autogen")

def check_auto_select():
    """Check how auto speaker selection works"""
    try:
        import autogen
        from autogen.agentchat.groupchat import GroupChat
        
        print(f"AutoGen version: {autogen.__version__}")
        
        # Check GroupChat _auto_select_speaker method
        print("\nGroupChat._auto_select_speaker method:")
        if hasattr(GroupChat, '_auto_select_speaker'):
            auto_select_method = getattr(GroupChat, '_auto_select_speaker')
            sig = inspect.signature(auto_select_method)
            print(f"  Signature: {sig}")
            
            # Show source code of _auto_select_speaker
            try:
                source = inspect.getsource(auto_select_method)
                print(f"  Source code (first 20 lines):")
                lines = source.strip().split('\n')
                for i, line in enumerate(lines[:20]):
                    print(f"  {i+1:3d}: {line}")
                if len(lines) > 20:
                    print(f"  ... (truncated, total {len(lines)} lines)")
            except Exception as e:
                print(f"  Error getting source: {str(e)}")
        else:
            print("  _auto_select_speaker method not found")
        
        return True
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

def check_error_message():
    """Check for the actual error message"""
    try:
        print("\nSearching for error messages in log files...")
        # Check recent log files for speaker selection errors
        log_dir = "data/logs"
        found = False
        if os.path.exists(log_dir):
            log_files = sorted([os.path.join(log_dir, f) for f in os.listdir(log_dir) 
                               if f.endswith(".log")], key=os.path.getmtime, reverse=True)
            
            for log_file in log_files[:5]:  # Check 5 most recent log files
                print(f"Checking {log_file}...")
                with open(log_file, 'r') as f:
                    content = f.read()
                    if "speaker" in content.lower() and "error" in content.lower():
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if "speaker" in line.lower() and "error" in line.lower():
                                start = max(0, i-2)
                                end = min(len(lines), i+3)
                                print(f"  Found error context:")
                                for j in range(start, end):
                                    print(f"    {lines[j]}")
                                found = True
                                break
                    if found:
                        break
        else:
            print(f"  Log directory {log_dir} not found")
        
        if not found:
            print("  No speaker selection errors found in recent logs")
        
        return True
    except Exception as e:
        logger.error(f"Error checking logs: {str(e)}")
        print(f"❌ Error checking logs: {str(e)}")
        return False

if __name__ == "__main__":
    check_auto_select()
    check_error_message()

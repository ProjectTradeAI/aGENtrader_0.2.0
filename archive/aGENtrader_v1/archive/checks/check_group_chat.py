#!/usr/bin/env python3
"""
Check GroupChat class for speaker selection
"""
import sys
import os
import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_autogen")

def check_groupchat():
    """Check the GroupChat class and its select_speaker method"""
    try:
        import autogen
        from autogen.agentchat.groupchat import GroupChat
        
        print(f"AutoGen version: {autogen.__version__}")
        
        # Check GroupChat select_speaker method
        print("\nGroupChat.select_speaker method:")
        if hasattr(GroupChat, 'select_speaker'):
            select_speaker_method = getattr(GroupChat, 'select_speaker')
            sig = inspect.signature(select_speaker_method)
            print(f"  Signature: {sig}")
            
            # Show source code of select_speaker
            try:
                source = inspect.getsource(select_speaker_method)
                print(f"  Source code:")
                print("  " + "\n  ".join(source.strip().split('\n')))
            except Exception as e:
                print(f"  Error getting source: {str(e)}")
        else:
            print("  select_speaker method not found")
        
        # Check if there's any method in GroupChat related to speaker selection with LLM
        source = inspect.getsource(GroupChat)
        print("\nSearching for LLM-related speaker selection in GroupChat:")
        llm_terms = ["llm", "config", "speaker", "select", "auto"]
        relevant_lines = []
        for line in source.split("\n"):
            if any(term in line.lower() for term in llm_terms) and "def " not in line and "#" not in line:
                relevant_lines.append(line.strip())
        
        if relevant_lines:
            for line in relevant_lines:
                print(f"  Found: {line}")
        else:
            print("  No LLM-related speaker selection found")
        
        return True
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    check_groupchat()

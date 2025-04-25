#!/usr/bin/env python3
"""
Check available parameters in AutoGen GroupChatManager
"""
import sys
import os
import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_autogen")

def check_autogen_version():
    """Check the installed AutoGen version and its capabilities"""
    try:
        import autogen
        from autogen.agentchat.groupchat import GroupChatManager
        
        print(f"AutoGen version: {autogen.__version__}")
        
        # Check GroupChatManager constructor parameters
        print("\nGroupChatManager constructor parameters:")
        sig = inspect.signature(GroupChatManager.__init__)
        for param_name, param in sig.parameters.items():
            if param_name != 'self':
                print(f"  - {param_name}: {param.annotation}")
                if param.default != inspect.Parameter.empty:
                    print(f"      default: {param.default}")
        
        # Check if there might be a different parameter for speaker selection
        source = inspect.getsource(GroupChatManager)
        print("\nSearching for speaker or selection-related terms in source:")
        speaker_terms = ["speaker", "select", "_select_", "selection", "auto_select"]
        for term in speaker_terms:
            for line in source.split("\n"):
                if term in line.lower() and "def " not in line and "#" not in line:
                    print(f"  Found: {line.strip()}")
        
        # Check if there's a _select_speaker method
        methods = [m for m in dir(GroupChatManager) if not m.startswith("__") and m.endswith("__")]
        print("\nRelevant methods in GroupChatManager:")
        for method in methods:
            if "select" in method.lower() or "speaker" in method.lower():
                print(f"  - {method}")
        
        # See if llm_config is used for speaker selection internally
        if "llm_config" in source and ("speaker" in source.lower() or "select" in source.lower()):
            print("\nllm_config might be used for speaker selection internally.")

        return True
    except Exception as e:
        logger.error(f"Error checking AutoGen: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    check_autogen_version()

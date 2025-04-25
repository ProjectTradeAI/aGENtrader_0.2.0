#!/usr/bin/env python3
"""
Simple script to verify the speaker selection fix was properly applied
"""
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_fix")

def verify_fix():
    """Verify that the fix was properly applied"""
    try:
        import autogen
        from autogen.agentchat.groupchat import GroupChatManager
        
        # Check if the parameter is in the class signature
        param_names = GroupChatManager.__init__.__code__.co_varnames
        logger.info(f"GroupChatManager parameters: {param_names}")
        
        if 'select_speaker_auto_llm_config' in param_names:
            print("✅ GroupChatManager class has the select_speaker_auto_llm_config parameter")
            return True
        else:
            print("❌ GroupChatManager class does NOT have the select_speaker_auto_llm_config parameter")
            return False
    except Exception as e:
        logger.error(f"Error verifying fix: {str(e)}")
        return False

if __name__ == "__main__":
    sys.exit(0 if verify_fix() else 1)

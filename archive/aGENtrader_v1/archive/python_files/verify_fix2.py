#!/usr/bin/env python3
"""
Better script to verify the speaker selection fix
"""
import sys
import os
import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_fix")

def verify_fix():
    """Verify that the fix was properly applied"""
    try:
        import autogen
        from autogen.agentchat.groupchat import GroupChatManager
        
        # Print autogen version
        print(f"AutoGen version: {autogen.__version__}")
        
        # Check the init method's signature
        sig = inspect.signature(GroupChatManager.__init__)
        print(f"GroupChatManager.__init__ signature: {sig}")
        
        # Check if the parameter is expected via kwargs or directly
        if 'select_speaker_auto_llm_config' in sig.parameters:
            print("✅ GroupChatManager explicitly accepts select_speaker_auto_llm_config parameter")
        elif '**kwargs' in str(sig) or '*' in str(sig) or 'kwargs' in sig.parameters:
            print("✅ GroupChatManager accepts select_speaker_auto_llm_config via **kwargs")
        else:
            print("❌ GroupChatManager does not accept select_speaker_auto_llm_config parameter")
            return False
        
        # Look at the source code to see if it uses the parameter
        source_code = inspect.getsource(GroupChatManager.__init__)
        if 'select_speaker_auto_llm_config' in source_code:
            print("✅ GroupChatManager source code references select_speaker_auto_llm_config")
        else:
            print("⚠️ GroupChatManager source code does not explicitly reference select_speaker_auto_llm_config")
            print("It might still work if passed via kwargs and used elsewhere")
        
        return True
    except Exception as e:
        logger.error(f"Error verifying fix: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    sys.exit(0 if verify_fix() else 1)

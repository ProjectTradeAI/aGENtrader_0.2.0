#!/usr/bin/env python3
"""
Deeper analysis of GroupChatManager and its parent classes
"""
import sys
import os
import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_fix")

def analyze_class_hierarchy(cls, depth=0):
    """Analyze a class and its parent classes for the parameter"""
    indent = "  " * depth
    print(f"{indent}Analyzing {cls.__name__}:")
    
    try:
        # Check the init method's signature
        if hasattr(cls, '__init__'):
            sig = inspect.signature(cls.__init__)
            print(f"{indent}  {cls.__name__}.__init__ signature: {sig}")
            
            # Check if the parameter is expected via kwargs or directly
            if 'select_speaker_auto_llm_config' in sig.parameters:
                print(f"{indent}  ✅ {cls.__name__} explicitly accepts select_speaker_auto_llm_config parameter")
            elif '**kwargs' in str(sig) or '*' in str(sig) or 'kwargs' in sig.parameters:
                print(f"{indent}  ⚠️ {cls.__name__} may accept select_speaker_auto_llm_config via **kwargs")
        
        # Look at the source code to see if it uses the parameter
        try:
            source_code = inspect.getsource(cls)
            if 'select_speaker_auto_llm_config' in source_code:
                print(f"{indent}  ✅ {cls.__name__} source code references select_speaker_auto_llm_config")
                # Try to find where it's used
                for line in source_code.split('\n'):
                    if 'select_speaker_auto_llm_config' in line:
                        print(f"{indent}    Found: {line.strip()}")
            else:
                print(f"{indent}  ❌ {cls.__name__} source code does not reference select_speaker_auto_llm_config")
        except Exception as e:
            print(f"{indent}  ⚠️ Couldn't get source code: {str(e)}")
    
        # Check parent classes recursively
        for base in cls.__bases__:
            if base.__name__ != 'object':
                analyze_class_hierarchy(base, depth + 1)
    except Exception as e:
        print(f"{indent}  ❌ Error analyzing {cls.__name__}: {str(e)}")

def verify_fix():
    """Verify that the fix was properly applied"""
    try:
        import autogen
        from autogen.agentchat.groupchat import GroupChatManager
        
        # Print autogen version
        print(f"AutoGen version: {autogen.__version__}")
        
        # Analyze GroupChatManager hierarchy
        print("\nClass hierarchy analysis:")
        analyze_class_hierarchy(GroupChatManager)
        
        # Check if we can create a GroupChatManager with the parameter
        groupchat = autogen.GroupChat(agents=[], messages=[])
        try:
            print("\nCreating GroupChatManager with select_speaker_auto_llm_config parameter...")
            manager = GroupChatManager(
                groupchat=groupchat,
                select_speaker_auto_llm_config={"config_list": []}
            )
            print("✅ Created GroupChatManager with select_speaker_auto_llm_config successfully!")
            print(f"Manager parameters: {manager.__dict__.keys()}")
            return True
        except Exception as e:
            print(f"❌ Error creating GroupChatManager: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error verifying fix: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    sys.exit(0 if verify_fix() else 1)

#!/usr/bin/env python3
"""
Quick Debug Script for DecisionSession

This script quickly checks why the DecisionSession is using a simplified framework.
"""
import os
import sys
import inspect
import traceback

def main():
    """Main function"""
    print("Starting quick debug of DecisionSession class")
    
    # Print Python version
    print(f"Python version: {sys.version}")
    
    # Print PYTHONPATH
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"Current directory: {os.getcwd()}")
    
    # Try to import DecisionSession
    try:
        print("Attempting to import DecisionSession...")
        from orchestration.decision_session import DecisionSession
        print("✅ Successfully imported DecisionSession")
        
        # Check if class has simplified agent framework
        if hasattr(DecisionSession, 'run_session'):
            print("✅ DecisionSession has run_session method")
            
            try:
                # Get the source code
                source = inspect.getsource(DecisionSession.run_session)
                
                # Check for simplified framework
                if "simplified agent framework" in source:
                    print("❌ Method contains 'simplified agent framework' text!")
                    
                    # Find the context around the simplified text
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if "simplified agent framework" in line:
                            context_start = max(0, i - 3)
                            context_end = min(len(lines), i + 4)
                            print("\nContext around simplified framework reference:")
                            for j in range(context_start, context_end):
                                prefix = ">" if j == i else " "
                                print(f"{prefix} {lines[j]}")
                            break
                
                # Check for AutoGen
                if "import autogen" in source or "autogen." in source:
                    print("✅ Method uses AutoGen")
                else:
                    print("❌ Method does not appear to use AutoGen")
                
                # Check for simplification switch logic
                if "if" in source and "else" in source and "simplif" in source.lower():
                    print("⚠️ Method has conditional simplified logic")
                
                # See if there's a "USE_FULL_FRAMEWORK" flag or similar
                if "USE_FULL" in source or "SIMPLIFIED" in source:
                    print("⚠️ Method may have a flag to toggle simplified mode")
            except Exception as e:
                print(f"⚠️ Could not get source code: {e}")
                print(traceback.format_exc())
        else:
            print("❌ DecisionSession does not have run_session method")
        
        # Create instance and check attributes
        print("\nCreating DecisionSession instance to check attributes...")
        session = DecisionSession()
        
        # Check for configuration attributes
        attributes = []
        for attr in dir(session):
            if not attr.startswith('__'):
                try:
                    value = getattr(session, attr)
                    if attr in ['use_autogen', 'use_simplified', 'simplified_mode', 'agents', 
                               'llm_config', 'technical_analyst', 'fundamental_analyst']:
                        attributes.append((attr, str(value)))
                except:
                    pass
        
        if attributes:
            print("Found relevant configuration attributes:")
            for attr, value in attributes:
                print(f"  {attr}: {value}")
        else:
            print("No relevant configuration attributes found")
        
        # Try to run a simple decision
        print("\nAttempting to run a test decision...")
        try:
            result = session.run_session("BTCUSDT", 50000)
            print(f"Decision output: {result}")
            
            # Check if result explicitly mentions simplified
            if isinstance(result, dict) and 'decision' in result:
                decision = result['decision']
                if isinstance(decision, dict) and 'reasoning' in decision:
                    reasoning = decision['reasoning']
                    if "simplified" in reasoning.lower():
                        print("❌ Decision reasoning contains 'simplified'")
                    else:
                        print("✅ Decision reasoning does not contain 'simplified'")
        except Exception as e:
            print(f"⚠️ Error running decision: {e}")
    
    except ImportError as e:
        print(f"❌ Failed to import DecisionSession: {e}")
        print(traceback.format_exc())
        
        # Check if file exists manually
        decision_session_path = os.path.join(os.getcwd(), 'orchestration', 'decision_session.py')
        if os.path.exists(decision_session_path):
            print(f"✓ Found decision_session.py at: {decision_session_path}")
            
            # Try to read the file directly
            try:
                with open(decision_session_path, 'r') as f:
                    content = f.read()
                    print(f"File size: {len(content)} bytes")
                    
                    # Check for simplified agent framework
                    if "simplified agent framework" in content:
                        print("❌ File contains 'simplified agent framework' text")
                    
                    # Check for AutoGen imports
                    if "import autogen" in content:
                        print("✅ File imports AutoGen")
                    else:
                        print("❌ File does not import AutoGen")
            except Exception as e:
                print(f"⚠️ Could not read file: {e}")
        else:
            print(f"❌ Could not find decision_session.py at: {decision_session_path}")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(traceback.format_exc())
    
    # Check for autogen
    try:
        print("\nChecking AutoGen availability...")
        import autogen
        print(f"✅ AutoGen is available (version: {getattr(autogen, '__version__', 'Unknown')})")
        
        # Check key components
        components = [
            "AssistantAgent", 
            "UserProxyAgent", 
            "GroupChat", 
            "GroupChatManager"
        ]
        
        for component in components:
            if hasattr(autogen, component):
                print(f"✅ autogen.{component} is available")
            else:
                print(f"❌ autogen.{component} is not available")
    except ImportError:
        print("❌ AutoGen is not available")
    
    # Check for flaml with automl
    try:
        print("\nChecking FLAML availability...")
        import flaml
        print(f"✅ FLAML is available (version: {getattr(flaml, '__version__', 'Unknown')})")
        
        # Check for automl
        try:
            import flaml.automl
            print("✅ flaml.automl is available")
        except ImportError:
            print("❌ flaml.automl is not available")
    except ImportError:
        print("❌ FLAML is not available")
    
    # Check OpenAI API key
    print("\nChecking environment variables...")
    if "OPENAI_API_KEY" in os.environ:
        api_key = os.environ["OPENAI_API_KEY"]
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        print(f"✅ OPENAI_API_KEY is set: {masked_key}")
    else:
        print("❌ OPENAI_API_KEY is not set")
    
    print("\nQuick debug completed")

if __name__ == "__main__":
    main()
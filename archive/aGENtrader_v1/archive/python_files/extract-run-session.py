#!/usr/bin/env python3
"""
Extract Run Session Method from DecisionSession

This script extracts and displays the run_session method from the DecisionSession class.
"""
import os
import sys
import inspect

def main():
    """Main function"""
    print("Extracting run_session method from DecisionSession...")
    
    # Set Python path to include current directory
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    
    try:
        # Import the DecisionSession class
        from orchestration.decision_session import DecisionSession
        print("Successfully imported DecisionSession class")
        
        # Check if run_session exists
        if hasattr(DecisionSession, 'run_session'):
            print("Found run_session method in DecisionSession class")
            
            # Get the source code
            source = inspect.getsource(DecisionSession.run_session)
            
            # Print the source code
            print("\n=== START OF run_session METHOD ===\n")
            print(source)
            print("\n=== END OF run_session METHOD ===")
            
            # Save to file
            with open("run_session_method.txt", "w") as f:
                f.write(source)
            print(f"Saved source code to run_session_method.txt")
            
            # Check for simplified framework
            if "simplified agent framework" in source:
                print("\n⚠️ Method contains 'simplified agent framework' text!")
                
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
            else:
                print("\n✅ Method does not contain 'simplified agent framework' text")
        else:
            print("❌ run_session method not found in DecisionSession class")
            
            # List available methods
            methods = [name for name in dir(DecisionSession) if callable(getattr(DecisionSession, name)) and not name.startswith('__')]
            print(f"Available methods: {', '.join(methods)}")
    
    except ImportError as e:
        print(f"❌ Failed to import DecisionSession: {e}")
        
        # Check if file exists manually
        decision_session_path = os.path.join(os.getcwd(), 'orchestration', 'decision_session.py')
        if os.path.exists(decision_session_path):
            print(f"Found decision_session.py at: {decision_session_path}")
            
            try:
                # Read the file and look for run_session method
                with open(decision_session_path, 'r') as f:
                    content = f.read()
                
                # Simple (but not perfect) way to extract the method
                if "def run_session" in content:
                    start_index = content.find("def run_session")
                    if start_index != -1:
                        # Find the next method definition or end of class
                        next_def = content.find("def ", start_index + 1)
                        if next_def != -1:
                            method_code = content[start_index:next_def]
                        else:
                            # Try to find end of class
                            end_index = content.find("class ", start_index + 1)
                            if end_index != -1:
                                method_code = content[start_index:end_index]
                            else:
                                method_code = content[start_index:]
                        
                        print("\n=== START OF run_session METHOD (extracted from file) ===\n")
                        print(method_code)
                        print("\n=== END OF run_session METHOD ===")
                        
                        # Save to file
                        with open("run_session_method.txt", "w") as f:
                            f.write(method_code)
                        print(f"Saved source code to run_session_method.txt")
                        
                        # Check for simplified framework
                        if "simplified agent framework" in method_code:
                            print("\n⚠️ Method contains 'simplified agent framework' text!")
                    else:
                        print("❌ Could not find run_session method in file")
                else:
                    print("❌ run_session method not found in file")
            except Exception as e:
                print(f"❌ Error reading file: {e}")
        else:
            print(f"❌ decision_session.py not found at: {decision_session_path}")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
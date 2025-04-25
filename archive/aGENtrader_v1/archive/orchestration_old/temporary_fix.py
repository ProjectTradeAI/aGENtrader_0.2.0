"""
Temporary Fix Script

This script applies a fix to the decision_session_fixed.py file
to correct indentation errors causing the Python interpreter to fail.
"""

import os
import re
import sys

def fix_indentation_issue():
    """Fix indentation issues in decision_session_fixed.py"""
    file_path = "orchestration/decision_session_fixed.py"
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return False
    
    # Read the file
    with open(file_path, "r") as f:
        content = f.read()
    
    # Fix the indentation issue for the _extract_decision method
    pattern = r'(\s+)def _format_market_summary.*?\n(\s+)return ".*?"\n\n(\s+)def _extract_decision'
    replacement = r'\1def _format_market_summary\2return "\3\1def _extract_decision'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Check if any changes were made
    if new_content == content:
        print("No changes needed or pattern not found.")
        
        # Alternative approach: look for the specific unindented method
        unindented_pattern = r'(\s+)return ".*?"\n\n(\s+)def _extract_decision'
        if re.search(unindented_pattern, content, flags=re.DOTALL):
            print("Found unindented method, applying manual fix")
            
            # Split the file at the method definition
            parts = content.split("    def _extract_decision")
            if len(parts) == 2:
                # Rejoin with proper indentation
                new_content = parts[0] + "    def _extract_decision" + parts[1]
                
                # Ensure the docstring is properly indented
                docstring_pattern = r'def _extract_decision.*?\n(\s+)"""'
                docstring_replacement = r'def _extract_decision\1    """'
                new_content = re.sub(docstring_pattern, docstring_replacement, new_content, flags=re.DOTALL)
            else:
                print("Error: Could not apply manual fix")
                return False
    
    # Save the fixed file
    backup_path = file_path + ".bak"
    try:
        # Create backup
        with open(backup_path, "w") as f:
            f.write(content)
        print(f"Created backup at {backup_path}")
        
        # Write fixed file
        with open(file_path, "w") as f:
            f.write(new_content)
        print(f"Successfully applied fix to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return False

def fix_method_definition():
    """Alternative approach using line-by-line processing"""
    file_path = "orchestration/decision_session_fixed.py"
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return False
    
    # Read the file line by line
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    # Find the problematic line and fix its indentation
    for i in range(len(lines)):
        if "def _extract_decision" in lines[i] and lines[i].startswith("        def"):
            # Fix indentation of method definition and docstring
            print(f"Found method definition at line {i+1}, fixing indentation")
            lines[i] = "    def _extract_decision" + lines[i][14:]
            
            # Fix indentation of docstring if it exists
            if i+1 < len(lines) and '"""' in lines[i+1]:
                if not lines[i+1].startswith("        "):
                    lines[i+1] = "        " + lines[i+1].lstrip()
            
            # Ensure all the method body lines are properly indented
            j = i + 1
            while j < len(lines) and (lines[j].strip() == "" or lines[j].startswith("            ")):
                j += 1
            
            # If we found a line that's part of the method but with wrong indentation,
            # add indentation to all subsequent lines until the next method
            if j < len(lines) and not lines[j].startswith("    def ") and lines[j].strip() != "":
                print(f"Found possible method body with wrong indentation at line {j+1}")
                while j < len(lines) and not lines[j].startswith("    def "):
                    if lines[j].strip() != "":
                        if not lines[j].startswith("        "):
                            lines[j] = "        " + lines[j].lstrip()
                    j += 1
            
            break
    
    # Save the fixed file
    backup_path = file_path + ".bak"
    try:
        # Create backup
        with open(backup_path, "w") as f:
            f.writelines(lines)
        print(f"Created backup at {backup_path}")
        
        # Write fixed file
        with open(file_path, "w") as f:
            f.writelines(lines)
        print(f"Successfully applied fix to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return False

if __name__ == "__main__":
    print("Running temporary fix for decision_session_fixed.py")
    
    # Try the first approach
    if fix_indentation_issue():
        print("Fix applied successfully with pattern matching approach")
    # If that doesn't work, try the second approach
    elif fix_method_definition():
        print("Fix applied successfully with line-by-line approach")
    else:
        print("Failed to apply fix")
        sys.exit(1)
    
    print("Fix complete, testing file")
    try:
        # Try to import the module to verify the fix
        import importlib.util
        spec = importlib.util.spec_from_file_location("decision_session_fixed", "orchestration/decision_session_fixed.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print("Successfully imported fixed module")
    except Exception as e:
        print(f"Error importing fixed module: {str(e)}")
        sys.exit(1)
    
    print("Temporary fix applied successfully")
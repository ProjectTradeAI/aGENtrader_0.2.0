"""
Fix Indentation Script

Direct fix for the indentation issue in decision_session_fixed.py
"""

def fix_file():
    # Read the file
    with open("orchestration/decision_session_fixed.py", "r") as f:
        lines = f.readlines()
    
    # Make backup
    with open("orchestration/decision_session_fixed.py.backup", "w") as f:
        f.writelines(lines)
    
    # Find where the indentation is wrong
    extract_decision_line = None
    for i, line in enumerate(lines):
        if 'def _extract_decision' in line:
            extract_decision_line = i
            break
    
    if extract_decision_line is None:
        print("Could not find the _extract_decision method")
        return
    
    print(f"Found _extract_decision at line {extract_decision_line + 1}")
    
    # Fix the method definition line
    if lines[extract_decision_line].startswith('        def'):
        lines[extract_decision_line] = '    ' + lines[extract_decision_line][8:]
        print(f"Fixed indentation for method definition")
    
    # Fix the docstring
    if extract_decision_line + 1 < len(lines) and '"""' in lines[extract_decision_line + 1]:
        if not lines[extract_decision_line + 1].startswith('        '):
            lines[extract_decision_line + 1] = '        ' + lines[extract_decision_line + 1].lstrip()
            print(f"Fixed indentation for docstring start")
    
    # Continue fixing indentation for the entire method
    current_line = extract_decision_line + 2
    while current_line < len(lines):
        # If we've reached another method definition, we're done
        if lines[current_line].startswith('    def '):
            break
        
        # If it's not a blank line and doesn't have proper indentation
        if lines[current_line].strip() and not lines[current_line].startswith('        '):
            # Make sure we don't add indentation to next method declaration
            if 'def ' in lines[current_line] and (
                lines[current_line].startswith('def ') or 
                lines[current_line].startswith('    def ')
            ):
                break
            
            lines[current_line] = '        ' + lines[current_line].lstrip()
            print(f"Fixed indentation for line {current_line + 1}")
        
        current_line += 1
    
    # Write the fixed file
    with open("orchestration/decision_session_fixed.py", "w") as f:
        f.writelines(lines)
    
    print("Applied indentation fix")

if __name__ == "__main__":
    print("Applying direct indentation fix to decision_session_fixed.py")
    fix_file()
    print("Fix complete")
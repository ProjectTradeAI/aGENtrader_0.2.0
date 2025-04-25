#!/bin/bash
# Script to apply indentation fix for the decision_session_fixed.py file on EC2

# Source the SSH key setup script if it exists
if [ -f "fix-ssh-key.sh" ]; then
    source fix-ssh-key.sh
fi

# Set variables
SSH_KEY_PATH="ec2_ssh_key.pem"
SSH_USER="ec2-user"
EC2_IP="${EC2_PUBLIC_IP}"

echo "Creating and applying indentation fix on EC2 instance..."

# Create a temporary Python fix script
cat > temp_fix.py << 'EOL'
"""
Fix Indentation Script

Direct fix for the indentation issue in decision_session_fixed.py
"""

import os

def fix_file():
    file_path = "/home/ec2-user/aGENtrader/orchestration/decision_session_fixed.py"
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return False
    
    # Read the file
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    # Make backup
    backup_path = file_path + ".bak"
    with open(backup_path, "w") as f:
        f.writelines(lines)
    print(f"Created backup at {backup_path}")
    
    # Find where the indentation is wrong
    extract_decision_line = None
    for i, line in enumerate(lines):
        if 'def _extract_decision' in line:
            extract_decision_line = i
            break
    
    if extract_decision_line is None:
        print("Could not find the _extract_decision method")
        return False
    
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
    with open(file_path, "w") as f:
        f.writelines(lines)
    
    print("Applied indentation fix")
    return True

# Test the fix by importing the module
def test_fix():
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location(
            "decision_session_fixed", 
            "/home/ec2-user/aGENtrader/orchestration/decision_session_fixed.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print("Successfully imported fixed module")
        return True
    except Exception as e:
        print(f"Error importing fixed module: {str(e)}")
        return False

if __name__ == "__main__":
    print("Applying direct indentation fix to decision_session_fixed.py")
    if fix_file():
        print("Fix applied successfully. Testing import...")
        if test_fix():
            print("Fix verified successfully.")
        else:
            print("Fix applied but verification failed.")
    else:
        print("Failed to apply fix.")
EOL

# Transfer the fix script to EC2
scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no temp_fix.py "${SSH_USER}@${EC2_IP}:~/temp_fix.py"

# Execute the fix script on EC2
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "${SSH_USER}@${EC2_IP}" "cd ~ && python3 temp_fix.py"

# Clean up
rm temp_fix.py

echo "Fix applied on EC2 instance."

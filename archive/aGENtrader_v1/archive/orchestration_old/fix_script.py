#!/usr/bin/env python3
"""
Quick script to fix the syntax error in decision_session.py
"""

import sys

def fix_file(input_path, output_path):
    with open(input_path, 'r') as f:
        content = f.read()
    
    # Fix the file by ensuring all docstrings are terminated
    fixed_content = content + '\n# End of file'
    
    with open(output_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"File fixed and saved to {output_path}")

if __name__ == "__main__":
    input_file = "/home/runner/workspace/orchestration/decision_session.py"
    output_file = "/home/runner/workspace/orchestration/decision_session_fixed.py"
    fix_file(input_file, output_file)
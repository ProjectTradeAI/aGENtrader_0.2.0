# AutoGen GroupChatManager Fix for EC2

## Problem

The error you're seeing in the backtesting process is related to the AutoGen GroupChatManager component, which is missing a required LLM configuration for its internal speaker selection agent:

```
2025-04-08 19:40:52,272 - decision_session - ERROR - Error in agent session: The group chat's internal speaker selection agent does not have an LLM configuration. Please provide a valid LLM config to the group chat's GroupChatManager or set it with the select_speaker_auto_llm_config parameter.
```

## Solution

You need to update any files that use the `GroupChatManager` to include the `select_speaker_auto_llm_config` parameter. Follow these steps to fix the issue on your EC2 instance:

### Step 1: Find Files That Use GroupChatManager

Run the following command to find all Python files that use the `GroupChatManager` class:

```bash
cd /home/ec2-user/aGENtrader
grep -r "GroupChatManager" --include="*.py" .
```

### Step 2: Edit Each File

For each file that uses `GroupChatManager`, you need to modify how it's initialized.

Look for code that looks similar to this:

```python
manager = GroupChatManager(
    groupchat=self.group_chat,
    llm_config=self.llm_config,
    is_termination_msg=lambda msg: "TRADING SESSION COMPLETE" in msg.get("content", "")
)
```

And update it to include the `select_speaker_auto_llm_config` parameter:

```python
manager = GroupChatManager(
    groupchat=self.group_chat,
    llm_config=self.llm_config,
    is_termination_msg=lambda msg: "TRADING SESSION COMPLETE" in msg.get("content", ""),
    select_speaker_auto_llm_config=self.llm_config  # Add this line to fix the error
)
```

### Step 3: Test the Fix

After updating the files, run a basic test to verify the fix:

```bash
cd /home/ec2-user/aGENtrader
python3 test_structured_decision_making.py --test_type extractor
```

## Alternative: Manual Python Fix Script

If you prefer, you can create a Python script that automatically applies the fix. Here's how to do it:

1. Create a new file named `fix_autogen_group_chat.py`:

```bash
cd /home/ec2-user/aGENtrader
nano fix_autogen_group_chat.py
```

2. Paste the following code:

```python
#!/usr/bin/env python3
"""
Fix AutoGen GroupChatManager configurations
"""

import os
import re
import shutil
import sys
import glob

def fix_group_chat_manager(filepath):
    """Fix GroupChatManager in a single file"""
    print(f"Checking {filepath}...")
    
    # Create backup
    backup_path = f"{filepath}.bak"
    shutil.copyfile(filepath, backup_path)
    
    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Skip if already fixed
    if 'select_speaker_auto_llm_config' in content:
        print(f"  Already fixed: {filepath}")
        return False
    
    # Find GroupChatManager initializations
    pattern = r'(\s*manager\s*=\s*GroupChatManager\s*\(\s*groupchat\s*=\s*[^,]+,\s*llm_config\s*=\s*[^,]+,\s*is_termination_msg\s*=[^)]+\))'
    
    # If not found, try a more general pattern
    if not re.search(pattern, content):
        pattern = r'(\s*manager\s*=\s*GroupChatManager\s*\(.*?\))'
    
    if re.search(pattern, content):
        # Check if the match ends with a parenthesis
        match = re.search(pattern, content)
        match_text = match.group(1)
        
        if match_text.strip().endswith(')'):
            # Add the new parameter before the closing parenthesis
            fixed_text = match_text.rstrip(')') + ',\n    select_speaker_auto_llm_config=self.llm_config  # Added to fix speaker selection error\n)'
            new_content = content.replace(match_text, fixed_text)
            
            # Write the updated content
            with open(filepath, 'w') as f:
                f.write(new_content)
            
            print(f"  Fixed: {filepath}")
            return True
    
    print(f"  No match found in: {filepath}")
    return False

def find_and_fix_files():
    """Find and fix all relevant files"""
    # Start from current directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Find all Python files containing GroupChatManager
    cmd = 'grep -l "GroupChatManager" --include="*.py" -r .'
    
    try:
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        files = result.stdout.splitlines()
    except:
        # Fallback if subprocess fails
        files = []
        for root, _, filenames in os.walk('.'):
            for filename in filenames:
                if filename.endswith('.py'):
                    filepath = os.path.join(root, filename)
                    with open(filepath, 'r') as f:
                        if 'GroupChatManager' in f.read():
                            files.append(filepath)
    
    fixed_count = 0
    for filepath in files:
        if fix_group_chat_manager(filepath):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files out of {len(files)} found.")

if __name__ == "__main__":
    print("Starting AutoGen GroupChatManager fix")
    find_and_fix_files()
    print("Fix completed!")
```

3. Make the script executable and run it:

```bash
chmod +x fix_autogen_group_chat.py
python3 fix_autogen_group_chat.py
```

## Key Files to Check

Based on your project structure, these files are most likely to need fixing:

1. `agents/collaborative_trading_framework.py`
2. Any backtesting scripts in the root directory
3. Any agent session handlers in the `agents` directory

## Verification

After applying the fix, re-run your backtesting script. The error about the GroupChatManager's internal speaker selection agent should be resolved.

If you still encounter issues, please check the exact file that's generating the error by looking at the traceback, and ensure that specific file has been properly updated.
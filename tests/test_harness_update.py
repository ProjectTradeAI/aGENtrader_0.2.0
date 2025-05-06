#!/usr/bin/env python3
"""
aGENtrader v2 Test Harness Utility

This utility allows testing individual analyst agents with controlled inputs
and parameters for debugging and development.
"""

import re
import sys
import os

def find_and_replace_agent_init():
    """Find and replace all agent initialization patterns in test_harness.py"""
    with open('test_harness.py', 'r') as file:
        content = file.read()
    
    # Replace agent initialization pattern
    pattern = r"""agent = agent_class\(\s+
                            data_provider=self\.data_provider,\s+
                            symbol=self\.symbol,\s+
                            interval=self\.interval,\s+
                            use_cache=False\s+
                        \)"""
                            
    replacement = """agent = agent_class(
                            data_fetcher=self.data_provider,
                            config={
                                "symbol": self.symbol,
                                "interval": self.interval,
                                "use_cache": False
                            }
                        )"""
    
    # Use regex with re.VERBOSE to handle whitespace in pattern
    new_content = re.sub(pattern, replacement, content, flags=re.VERBOSE)
    
    # Write updated content
    with open('test_harness.py', 'w') as file:
        file.write(new_content)
    
    print("Updated agent initialization patterns in test_harness.py")

if __name__ == "__main__":
    find_and_replace_agent_init()

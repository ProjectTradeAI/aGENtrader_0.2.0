#!/usr/bin/env python3
"""
Quick script to fix the register_function calls in the test file.
"""

def main():
    file_path = "test_autogen_db_integration.py"
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Remove the description parameter from register_function calls
    fixed_content = content.replace(
        'user_proxy.register_function(\n                function_map=({func_name: func}),\n                description=f"Function for {func_name}"\n            )',
        'user_proxy.register_function(\n                function_map=({func_name: func})\n            )'
    )
    
    with open(file_path, 'w') as file:
        file.write(fixed_content)
    
    print(f"File {file_path} updated successfully.")

if __name__ == "__main__":
    main()
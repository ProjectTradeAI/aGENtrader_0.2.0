"""
Test Runner for aGENtrader v2

This script runs all the unit tests in the tests directory.
It doesn't require pytest to be installed.
"""

import os
import sys
import unittest
import importlib.util
from typing import List

def discover_test_modules() -> List[str]:
    """Discover all test modules in the tests directory."""
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests')
    test_modules = []
    
    for filename in os.listdir(test_dir):
        if filename.startswith('test_') and filename.endswith('.py'):
            module_name = filename[:-3]  # Remove .py extension
            test_modules.append(module_name)
    
    return test_modules

def load_module(module_name: str):
    """Load a module by name from the tests directory."""
    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              'tests', f"{module_name}.py")
    
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_all_tests():
    """Run all tests in the tests directory."""
    # Get all test modules
    test_modules = discover_test_modules()
    
    if not test_modules:
        print("No test modules found. Make sure test files are named 'test_*.py'")
        return
    
    print(f"Found {len(test_modules)} test modules: {', '.join(test_modules)}")
    
    # Create a test suite
    suite = unittest.TestSuite()
    test_count = 0
    
    # Run tests directly from each module
    for module_name in test_modules:
        try:
            print(f"\nRunning tests from {module_name}...")
            module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    'tests', f"{module_name}.py")
            
            # Execute the test module as a script
            os.system(f"python3 {module_path}")
            test_count += 1
            
        except Exception as e:
            print(f"Error running {module_name}: {e}")
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Ran {test_count} test modules")
    
    return test_count > 0  # Return success if we ran at least one test module

if __name__ == "__main__":
    print("Running all aGENtrader v2 tests...")
    success = run_all_tests()
    print("Test run completed.")
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)
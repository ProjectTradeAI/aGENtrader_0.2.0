#!/usr/bin/env python
"""
Test runner for aGENtrader v2

This script provides a standardized way to run the unit tests in the aGENtrader v2 system.
It automatically handles the Python path setup so imports work correctly.
"""

import os
import sys
import unittest
import argparse

def main():
    """Run the test suite"""
    parser = argparse.ArgumentParser(description="Run aGENtrader v2 tests")
    parser.add_argument("--pattern", default="test_*.py", help="Pattern for test files")
    parser.add_argument("--start-dir", default="aGENtrader_v2/tests", help="Directory to start discovery")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Add the project root to the Python path to ensure imports work correctly
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Configure the test loading
    test_loader = unittest.defaultTestLoader
    test_loader.testMethodPrefix = "test"
    
    # Discover and run tests
    test_suite = test_loader.discover(
        start_dir=args.start_dir,
        pattern=args.pattern
    )
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
    result = test_runner.run(test_suite)
    
    # Return exit code based on test result
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())
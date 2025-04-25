# aGENtrader v2 Testing Framework

This directory contains unit tests for the various components of aGENtrader v2.

## Overview

The testing framework is designed to be lightweight and work without requiring external testing libraries like pytest. It uses Python's built-in `unittest` framework to create and run tests.

## Running Tests

There are multiple ways to run the tests:

1. Run all tests:
   ```
   python run_tests.py
   ```

2. Run a specific test file:
   ```
   python tests/test_liquidity_analyst_agent.py
   ```

## Creating New Tests

To create a new test:

1. Create a new Python file in the `tests` directory named `test_<component_name>.py`
2. Import the necessary modules:
   ```python
   import os
   import sys
   import unittest
   from unittest.mock import MagicMock, patch
   
   # Add parent directory to path to allow importing from the main package
   script_dir = os.path.dirname(os.path.abspath(__file__))
   parent_dir = os.path.dirname(script_dir)
   sys.path.append(parent_dir)
   
   # Import the module you want to test
   from module.to.test import ClassToTest
   ```

3. Create a test class that inherits from `unittest.TestCase`:
   ```python
   class TestYourComponent(unittest.TestCase):
       def setUp(self):
           # Set up test fixtures
           pass
           
       def test_some_function(self):
           # Test case
           result = some_function()
           self.assertEqual(result, expected_value)
   ```

4. Add a `run_tests` function to your test file:
   ```python
   def run_tests():
       unittest.main(argv=['first-arg-is-ignored'], exit=False)
   
   if __name__ == "__main__":
       print("Running your component tests...")
       run_tests()
       print("Tests completed.")
   ```

## Best Practices

1. **Mock External Dependencies**: Use `unittest.mock` to mock external dependencies like database connections and API calls.

2. **Isolate Tests**: Each test should be independent and not rely on the state from other tests.

3. **Test Edge Cases**: Include tests for edge cases and error handling.

4. **JSON Serialization**: When working with data structures that contain numpy or pandas types, use the `json_serializable` function from `tests.test_liquidity_analyst_agent` to handle serialization.

5. **Modular Testing**: Break down complex components into smaller, testable units.

## Current Test Coverage

- `test_liquidity_analyst_agent.py`: Tests for the LiquidityAnalystAgent class
  - Tests basic functionality
  - Tests handling of empty/missing data
  - Tests database connection failures

- `test_technical_analyst_agent.py`: Tests for the TechnicalAnalystAgent class
  - Tests basic functionality
  - Tests handling of empty/missing data
  - Tests database connection failures
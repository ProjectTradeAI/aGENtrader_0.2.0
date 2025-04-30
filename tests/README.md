# aGENtrader Test Suite

A comprehensive testing framework for the aGENtrader trading system.

## Overview

This test suite provides a structured and maintainable way to test the different components of the aGENtrader system, from individual agents to full integration tests.

## Directory Structure

```
tests/
├── agents/              # Tests for individual agent components
│   ├── test_technical_analyst.py
│   ├── test_liquidity_analyst.py
│   ├── test_sentiment_aggregator.py
│   └── ...
├── core/                # Tests for core system functions
│   ├── test_decision_logger.py
│   └── ...
├── integration/         # Tests for system integration points
│   ├── test_decision_pipeline.py
│   └── ...
├── helpers/             # Testing utilities and helpers
│   ├── test_utils.py
│   └── ...
└── README.md            # This file
```

## Running Tests

You can run tests using the `scripts/test_suite.sh` script:

```bash
# Run all tests
./scripts/test_suite.sh

# Run only agent tests
./scripts/test_suite.sh agents

# Run a specific test module
./scripts/test_suite.sh technical
```

### Test Suite Options

The test suite provides the following options:

- `./scripts/test_suite.sh all`: Run all tests
- `./scripts/test_suite.sh agents`: Run only agent tests
- `./scripts/test_suite.sh core`: Run only core tests
- `./scripts/test_suite.sh integration`: Run only integration tests
- `./scripts/test_suite.sh help`: Show help message
- `./scripts/test_suite.sh <pattern>`: Run tests matching the pattern

### Cleaning Deprecated Tests

You can list and clean deprecated tests using the `scripts/clean_tests.sh` script:

```bash
# List deprecated tests
./scripts/clean_tests.sh

# Remove deprecated tests
./scripts/clean_tests.sh --remove

# Archive deprecated tests
./scripts/clean_tests.sh --archive
```

## Writing Tests

### Test Requirements

All test modules should:

1. Return `0` on success, non-zero on failure
2. Include a descriptive header comment with a `Description:` field
3. Use the `unittest` framework
4. Include a `main()` function that runs the tests

### Example Test Structure

```python
#!/usr/bin/env python3
# Description: Tests for XYZ component

import sys
import os
import unittest

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from path.to.module import ComponentToTest

class TestComponent(unittest.TestCase):
    """Test suite for ComponentToTest."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.component = ComponentToTest()
        
    def test_feature_x(self):
        """Test feature X of the component."""
        result = self.component.feature_x()
        self.assertTrue(result)
        
    # More test methods...

def main():
    """Run the test suite."""
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestComponent))
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Return 0 for success, 1 for failure
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())
```

### Marking Tests as Deprecated

To mark a test as deprecated, add a comment at the top of the file:

```python
#!/usr/bin/env python3
# @deprecated: replaced by test_new_component.py with improved test cases
```

## Test Utilities

The `tests/helpers/test_utils.py` module provides utilities for writing tests:

- `TestCase`: Enhanced unittest.TestCase with additional assertion methods
- `MockPriceDataGenerator`: Generate mock price data for testing
- `DecisionLoggerExtensions`: Extensions for the DecisionLogger class

## Test Logs

Test logs are stored in the `logs/` directory with timestamps:

- `logs/test_results_YYYYMMDD_HHMMSS.log`: Detailed test results
- `logs/test_report_YYYYMMDD_HHMMSS.txt`: Summary report
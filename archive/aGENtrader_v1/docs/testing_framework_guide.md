# Trading System Testing Framework Guide

This guide explains the comprehensive testing system developed for the AutoGen-based trading platform. The framework provides multiple testing methods optimized for different environments and use cases.

## Overview

The testing framework includes:

1. **Comprehensive Tests**: Complete system tests that validate all components
2. **Replit-Optimized Tests**: Streamlined tests designed to work efficiently in Replit's environment
3. **Offline Tests**: Tests that don't require API connectivity to validate framework components
4. **Utilities**: Tools for viewing and analyzing test results

## Testing Scripts

### For Full Testing

- `run_tests.sh`: Main test runner supporting all test types
  - Single agent tests
  - Simplified collaborative tests
  - Decision session tests
  - Full collaborative tests

### For Replit Environment

- `run_replit_tests.sh`: Optimized for Replit with reduced API usage
  - Faster execution times
  - Reduced API costs
  - Streamlined test components

### For Debugging & Framework Validation

- `run_offline_test.py`: Test the logging and reporting system without API calls
- `check_test_progress.py`: Monitor running tests and view real-time results
- `view_test_results.py`: Examine completed test results in detail

## Running Tests

### Basic Usage

```bash
# Run a single agent test (fastest)
./run_tests.sh -t single

# Run a simplified collaborative test
./run_tests.sh -t simplified

# Run a decision session test
./run_tests.sh -t decision

# Run all tests
./run_tests.sh -t all
```

### Replit-Optimized Tests

```bash
# Run a quick single agent test
./run_replit_tests.sh

# Run a simplified collaborative test with minimal API usage
./run_replit_tests.sh -t simplified -m 2
```

### Offline Tests

```bash
# Run an offline test that doesn't require API calls
./run_offline_test.py
```

## Viewing Test Results

### Check Results During Test Execution

```bash
# Monitor test progress with auto-refresh
./check_test_progress.py --watch

# View only the latest test logs
./check_test_progress.py --show-logs

# View only the latest test results
./check_test_progress.py --show-results
```

### View Completed Test Results

```bash
# List all test results
./view_test_results.py --list-only

# View details for a specific test session
./view_test_results.py --session-id <session_id>

# View the latest test result
./view_test_results.py --latest
```

## Test Types Explained

### Single Agent Test

Tests the Market Analyst agent in isolation, focusing on its ability to retrieve market data and provide accurate analysis. This is the fastest test and useful for validating basic agent functionality.

### Simplified Collaborative Test

Tests a minimal collaborative setup between a few specialized agents: Analyst, Strategist, and Manager. This test validates the multi-agent communication framework without the full complexity of the complete system.

### Decision Session Test

Tests the structured decision-making framework that coordinates the trading decision process. This validates the orchestration layer that manages agent interactions and consolidates results into formalized trading decisions.

### Collaborative Test

Tests the full collaborative agent system with all specialized roles, including the complete workflow from data retrieval to final trading decisions. This is the most comprehensive test but takes the longest to run.

## Test Output

All tests produce structured output files:

1. **Log Files**: Detailed execution logs with timestamps
2. **Chat History**: Complete agent conversations in JSON format
3. **Session Data**: Full test results including decisions and analysis
4. **Summary Files**: Overview of test execution results

The outputs are organized by test type in the following directory structure:

```
data/logs/
├── comprehensive_tests/
│   ├── single_agent/
│   ├── simplified_collaborative/
│   ├── decision_session/
│   └── collaborative/
├── replit_tests/
│   ├── single_agent/
│   └── simplified_collaborative/
└── offline_tests/
    ├── chat_logs/
    └── results/
```

## Troubleshooting

### Common Issues

1. **Timeouts**: Tests may time out if they involve complex API interactions. Try reducing `max_turns` or use Replit-optimized tests.

2. **API Errors**: Ensure the OPENAI_API_KEY environment variable is set correctly. The testing framework will prompt for it if missing.

3. **Missing Data**: If database retrieval fails, ensure the database is properly initialized and contains market data.

### Best Practices

1. Start with offline tests to validate the logging framework.
2. Progress to single agent tests to validate basic agent functionality.
3. Use simplified collaborative tests to validate multi-agent communication.
4. Only run full collaborative tests when simpler tests pass.

## Extending the Framework

The testing framework is designed to be extensible. To add new test types:

1. Create a test function in `run_comprehensive_tests.py` or a specialized test script.
2. Update the appropriate bash scripts to include the new test type.
3. Ensure proper logging is implemented using the TestLogger class.
4. Update this documentation to reflect the new test type.

## Conclusion

This testing framework provides comprehensive validation of the AutoGen trading system, with options optimized for different environments and use cases. By using these tools effectively, you can ensure the reliability and accuracy of the trading system.
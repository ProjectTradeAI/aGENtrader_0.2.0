# Trading System Test Suite

This directory contains the test files for the AutoGen-based trading system. The tests are organized to validate different components and integration points of the system.

## Quick Start

```bash
# Run the most basic test
./run_offline_test.py

# Run a simple test optimized for Replit
./run_replit_tests.sh -t single

# View test results
./view_test_results.py --latest
```

For a comprehensive guide to the testing framework, see [Testing Framework Guide](../docs/testing_framework_guide.md).

## Available Test Files

### Agent Tests

- `test_single_agent.py`: Tests market analyst agent in isolation
- `test_simplified_collaborative.py`: Tests streamlined collaborative decision-making
- `test_collaborative_decision.py`: Tests full collaborative agent system
- `test_trading_decision.py`: Tests structured decision sessions

### Database Integration Tests

- `test_database_retrieval_tool.py`: Tests the database retrieval tool
- `test_autogen_db_integration.py`: Tests AutoGen integration with the database
- `test_serialization.py`: Tests proper serialization of database results

### AI Model Integration Tests

- `test_autogen_market_analysis.py`: Tests market analysis with AutoGen
- `test_autogen_integration.py`: Tests general AutoGen functionality
- `test_deepsek_connection.py`: Tests connection to Deepseek API

### Comprehensive Test Runners

- `run_comprehensive_tests.py`: Runs a series of tests with detailed logging
- `run_replit_tests.py`: Runs optimized tests for the Replit environment
- `run_offline_test.py`: Runs tests without requiring API calls

## Test Configuration

Tests use the following configuration files:

- `config/agent_config.json`: Configures agent settings
- `config/decision_session.json`: Configures decision session parameters

## Test Results

Test results are stored in structured directories:

```
data/logs/
├── comprehensive_tests/    # Results from full test suite
├── replit_tests/           # Results from Replit-optimized tests
└── offline_tests/          # Results from offline tests
```

Use the included tools to view and analyze test results:

- `view_test_results.py`: Browse and view test results
- `check_test_progress.py`: Monitor running tests

## Notes for Test Development

When writing tests for this system, follow these guidelines:

1. Always use the TestLogger class for consistent logging and result storage
2. Keep API usage minimal during development by using low max_turns values
3. Add test cases to the appropriate category
4. Update the test runners when adding new test types
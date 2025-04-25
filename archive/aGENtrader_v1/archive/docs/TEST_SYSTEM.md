# Trading System Test Framework

This directory contains a comprehensive test framework for evaluating the multi-agent trading system with AutoGen integration. The framework enables testing different aspects of the system, from individual agent functionality to collaborative decision-making.

## Test Organization

Tests are organized into the following categories:

1. **Single Agent Tests** - Tests for individual agent functionality
2. **Collaborative Analysis Tests** - Tests for collaborative market analysis
3. **Trading Decision Tests** - Tests for the trading decision process
4. **Integration Tests** - Tests for database and agent integration
5. **Comprehensive Tests** - End-to-end tests of the complete system

## Directory Structure

```
data/
  ├── logs/
  │   ├── current_tests/       - Latest test results
  │   ├── decisions/           - Trading decision test results
  │   ├── integration_tests/   - Integration test results
  │   ├── structured_decisions/ - Structured decision test results
  │   ├── db_tests/            - Database retrieval test results
  │   └── comprehensive_tests/ - Full system test results
  └── decisions/               - Saved trading decisions
```

## Running Tests

### Collaborative Market Analysis

To run collaborative market analysis tests:

```bash
./run_collaborative_test.sh [--symbol SYMBOL] [--output-dir DIR]
```

Example:
```bash
./run_collaborative_test.sh --symbol BTCUSDT --output-dir data/logs/my_test
```

### Collaborative Integration Tests

To run integration tests between agents and the database:

```bash
./run_collaborative_integration.sh [--symbol SYMBOL] [--output-dir DIR]
```

Example:
```bash
./run_collaborative_integration.sh --symbol BTCUSDT --output-dir data/logs/integration_tests
```

### Trading Decision Tests

To run trading decision tests:

```bash
./run_trading_decision.sh
```

### Structured Decision Tests

To run structured trading decision tests with database integration:

```bash
./run_structured_decision_test.sh [--symbol SYMBOL] [--output-dir DIR]
```

Example:
```bash
./run_structured_decision_test.sh --symbol BTCUSDT --output-dir data/logs/structured_decisions
```

### Database Integration Tests

To run basic database integration tests to verify connectivity and data access:

```bash
./run_db_test.sh [--output-dir DIR]
```

Example:
```bash
./run_db_test.sh --output-dir data/logs/db_tests
```

### Comprehensive Tests

To run comprehensive tests:

```bash
./run_comprehensive_tests.sh [--tests TYPE] [--symbol SYMBOL] [--output-dir DIR]
```

Where:
- `TYPE` can be "all", "single", "simplified", "decision", or "collaborative"
- `SYMBOL` is the trading symbol to test (default: BTCUSDT)
- `DIR` is the output directory for test logs

Example:
```bash
./run_comprehensive_tests.sh --tests simplified --symbol BTCUSDT
```

## Viewing Test Results

To view test results:

```bash
python view_test_results.py [--log-dir DIR] [--test-type TYPE] [--session-id ID]
```

Where:
- `DIR` is the log directory to search (default: data/logs)
- `TYPE` can be "all", "collaborative", "decision", or "single"
- `ID` is a specific session ID to view in detail

Example:
```bash
python view_test_results.py --log-dir data/logs/current_tests --test-type collaborative
```

## Dependencies

The test framework requires the following dependencies:

- Python 3.8+
- autogen
- psycopg2
- pandas
- numpy

## Database Integration

The test framework integrates with a PostgreSQL database for market data retrieval. The database connection is configured through environment variables:

- `DATABASE_URL` - PostgreSQL connection URL

## API Integration

The test framework uses the OpenAI API for agent functionality. The API key is provided through the environment:

- `OPENAI_API_KEY` - OpenAI API key

## Example Test Flow

1. **Market Data Retrieval** - Agents retrieve market data from the database
2. **Technical Analysis** - Agents perform technical analysis on the data
3. **Collaborative Discussion** - Agents discuss analysis findings
4. **Decision Making** - Agents make trading decisions based on analysis
5. **Result Logging** - Test results are logged and can be viewed with the results viewer
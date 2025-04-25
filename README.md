# aGENtrader v2.2

An advanced multi-agent AI trading platform with sophisticated deployment and workflow management capabilities, focusing on intelligent cryptocurrency trading and comprehensive system monitoring.

## Repository Structure

The repository follows a standardized structure for better maintainability and organization.

For a detailed overview of the repository structure, see [Repository Structure](docs/REPOSITORY_STRUCTURE.md).

Key directories:

```
/
├── agents/               # AI agents for trading decisions
├── core/                 # Core system functionality
├── data/                 # Data storage and management
├── config/               # Configuration files
├── deployment/           # Deployment scripts and configurations
├── docker/               # Docker configurations
├── docs/                 # Documentation
├── logs/                 # System logs
├── scripts/              # Utility scripts
├── tests/                # Test scripts and frameworks
└── utils/                # Utility functions and helpers
```

## Key Components

### Agents

The system is built around a multi-agent architecture where specialist agents collaborate to make trading decisions:

- **Technical Analyst Agent**: Performs technical analysis on price data
- **Sentiment Analyst Agent**: Analyzes market sentiment data
- **Liquidity Analyst Agent**: Monitors market liquidity conditions
- **Portfolio Manager Agent**: Manages overall portfolio allocation
- **Risk Guard Agent**: Enforces risk management rules
- **Trade Executor Agent**: Executes trading decisions

### Data Providers

The system can fetch data from multiple sources:

- **Binance API**: Primary source for cryptocurrency market data
- **CoinAPI**: Secondary/fallback market data source

### Core System

- **Decision Logger**: Creates human-readable summaries of agent decisions
- **Live Trading**: Core trading functionality that integrates all specialist agents
- **Trigger Scheduler**: Manages scheduled triggers for different timeframes

## Getting Started

### Running the System

The main entry points remain unchanged:

```bash
# For standard operation
python run.py

# For development/testing
python main.py
```

### Deployment

Deployment scripts are available in the deployment directory:

```bash
# Local deployment
./deployment/deploy_local.sh

# EC2 deployment
./deployment/deploy_ec2.sh
```

## Important Notes

- Symbolic links are provided at the root level for backward compatibility
- Configuration is managed through environment variables and the `config/` directory
- Logs are stored in the `logs/` directory with various specialized subdirectories

## Dependencies

- Python 3.10+
- See requirements.txt for Python package dependencies
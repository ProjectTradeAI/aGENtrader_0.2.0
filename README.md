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

### Deployment & Operations

The system includes robust deployment, rollback, and verification tools:

```bash
# Standard deployment to EC2
./deployment/deploy_ec2.sh

# Clean deployment (full wipe and fresh install)
./deployment/clean_deploy_ec2.sh

# Local deployment
./deployment/deploy_local.sh

# Rollback to previous version
./deployment/rollback_ec2.sh

# Validate deployment
python deployment/validate_deployment.py

# Test deployment & rollback flow
./deployment/test_deployment_flow.sh

# Verify versioning system integrity
python deployment/verify_versioning.py
```

#### Versioning System

The aGENtrader platform uses Git tags and commit hashes for versioning:

- Each release is tagged with a version (e.g., `v0.2.0`)
- Docker images are built with version information through build arguments
- Rollbacks can target any specific version or commit hash
- Version information is accessible at runtime for monitoring and logging

#### Rollback System

The platform includes a comprehensive rollback mechanism:

1. **Automated Rollback**: Use `rollback_ec2.sh` script to revert to any previous version
2. **Testing**: Use `test_deployment_flow.sh` to validate rollback processes
3. **Verification**: Automated health checks run after rollback to ensure system integrity
4. **Documentation**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed procedures

For detailed information on deployments and rollbacks, see:
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete deployment procedures
- [docs/ROLLBACK_PROCEDURE.md](docs/ROLLBACK_PROCEDURE.md) - Comprehensive rollback documentation

## Important Notes

- Symbolic links are provided at the root level for backward compatibility
- Configuration is managed through environment variables and the `config/` directory
- Logs are stored in the `logs/` directory with various specialized subdirectories

## Dependencies

- Python 3.10+
- See requirements.txt for Python package dependencies
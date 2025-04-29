# aGENtrader v2.2

An advanced multi-agent AI trading platform with sophisticated deployment and workflow management capabilities, focusing on intelligent cryptocurrency trading and comprehensive system monitoring.

## Recent Updates

- **2025-04-29**: Implemented automatic Ollama health check system with environment-specific startup procedures
- **2025-04-29**: Enhanced LLM client with improved error diagnostics and environment detection
- **2025-04-29**: Implemented agent-specific LLM routing - Sentiment agents now use Grok, others use Mistral
- **2025-04-29**: Fixed validation script to properly detect Binance API initialization by matching the correct log pattern
- **2025-04-28**: Upgraded from Mixtral to Mistral as the default LLM due to EC2 memory constraints
- **2025-04-27**: Enhanced error handling in all market data providers
- **2025-04-26**: Improved deployment validation with automatic container detection and fallback to local process checks

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

- **Technical Analyst Agent**: Performs technical analysis on price data (Uses Mistral)
- **Sentiment Analyst Agent**: Analyzes market sentiment data (Uses Grok)
- **Sentiment Aggregator Agent**: Aggregates sentiment from various sources (Uses Grok)
- **Liquidity Analyst Agent**: Monitors market liquidity conditions (Uses Mistral)
- **Funding Rate Analyst Agent**: Analyzes futures market funding rates (Uses Mistral)
- **Open Interest Analyst Agent**: Evaluates open interest trends (Uses Mistral)
- **Decision Agent**: Weighs all analyses and makes final decisions (Uses Mistral)

#### LLM Model Selection Strategy

The system uses an intelligent model routing strategy:
- Sentiment-related tasks use Grok (2-1212) for its superior natural language understanding
- Technical analysis and market structure tasks use Mistral for efficiency
- Each agent has a dedicated LLM client with its specific model configuration
- System automatically falls back to alternative models if the primary is unavailable

### Data Providers

The system can fetch data from multiple sources:

- **Binance API**: Primary source for cryptocurrency market data
- **CoinAPI**: Secondary/fallback market data source

### Core System

- **Decision Logger**: Creates human-readable summaries of agent decisions
- **Live Trading**: Core trading functionality that integrates all specialist agents
- **Trigger Scheduler**: Manages scheduled triggers for different timeframes
- **Ollama Health Check**: Automatic LLM service management with environment-specific detection

#### Ollama Health Check System

The platform includes a robust automatic LLM service management system:

- **Automatic Detection**: Detects environment (EC2, Docker, local) and uses appropriate configuration
- **Service Management**: Automatically starts Ollama service if not running
- **Model Verification**: Ensures required models (Mistral) are available
- **Fallback Mechanism**: Gracefully falls back to Grok API when Ollama is unavailable
- **Diagnostics**: Provides detailed error messages with environment-specific troubleshooting steps

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
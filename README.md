# aGENtrader v0.2.2

An advanced multi-agent AI trading platform with sophisticated deployment and workflow management capabilities, focusing on intelligent cryptocurrency trading and comprehensive system monitoring.

## Recent Updates

- **2025-05-06**: Added CI integration with version tag validation to ensure consistent versioning across all components
- **2025-05-06**: Updated system version to v0.2.2 with standardized version tracking in all agent outputs
- **2025-04-30**: Implemented unified agent architecture with standardized interfaces and improved testability (branch: v2.2.1)
- **2025-04-30**: Created comprehensive agent testing framework with isolated testing capabilities
- **2025-04-29**: Implemented automatic Ollama health check system with environment-specific startup procedures
- **2025-04-29**: Enhanced LLM client with improved error diagnostics and environment detection
- **2025-04-29**: Implemented agent-specific LLM routing - Sentiment agents now use Grok, others use Mistral
- **2025-04-29**: Fixed validation script to properly detect Binance API initialization by matching the correct log pattern
- **2025-04-28**: Upgraded from Mixtral to Mistral as the default LLM due to EC2 memory constraints

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

#### Agent Architecture (v0.2.2)

The agent system follows a standardized architecture with interfaces and base classes:

- **Interfaces**:
  - `AgentInterface`: Core interface for all agents
  - `AnalystAgentInterface`: For market analysis agents
  - `DecisionAgentInterface`: For trading decision agents
  - `ExecutionAgentInterface`: For trade execution agents

- **Base Classes**:
  - `BaseAgent`: Provides core agent functionality
  - `BaseAnalystAgent`: For market analysis agents
  - `BaseDecisionAgent`: For trading decision agents

- **Testing Framework**:
  - Individual agent testing with `tests/test_agent_individual.py`
  - Support for real or mock data sources
  - Detailed logging of agent reasoning

For details on using or implementing agents, see:
- [Agent Migration Guide](docs/AGENT_MIGRATION_GUIDE.md)
- [Development Notes](docs/DEV_NOTES.md)
- [Test Suite Documentation](tests/README.md)

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

- Each release is tagged with a version (e.g., `v0.2.2`)
- Docker images are built with version information through build arguments
- Rollbacks can target any specific version or commit hash
- Version information is accessible at runtime for monitoring and logging

##### Version Tag Validation

The system includes automatic version tag validation through CI:

- Ensures all agent outputs include the current system version
- Validates version consistency across all system components
- Prevents deployment of inconsistent versions
- Run validation locally: `python scripts/validate_version_tags.py`

The version tags are sourced from:
1. `version.json`
2. `core/version.py`
3. `config/settings.yaml` (under `system.version`)

For detailed information on version validation, see [CONTRIBUTING.md](CONTRIBUTING.md).

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
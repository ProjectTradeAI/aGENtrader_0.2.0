#!/bin/bash
# Create Directory Structure Script
# This script creates the target directory structure for the reorganized codebase

# Function to create a directory structure
create_dirs() {
  echo "Creating directory structure..."
  
  # Create main directories
  mkdir -p orchestration
  mkdir -p backtesting/{core,strategies,analysis,utils,scripts}
  mkdir -p data/{sources,storage,preprocessing}
  mkdir -p agents/{technical,fundamental,portfolio}
  mkdir -p strategies/{core,implementations}
  mkdir -p utils/{logging,config,validation}
  mkdir -p scripts/{setup,deployment,maintenance}
  mkdir -p docs
  mkdir -p tests/{unit,integration}
  
  echo "✅ Directory structure created successfully"
}

# Function to create README files
create_readmes() {
  echo "Creating README files for each directory..."
  
  # Main README
  cat > README.md << 'EOF'
# Multi-Agent Trading System

## Overview
This is an advanced multi-agent AI trading platform with sophisticated backtesting capabilities, focusing on intelligent market analysis and deployment infrastructure.

## Core Components
- **Orchestration**: Agent coordination and decision-making
- **Backtesting**: Comprehensive testing framework with authentic market data
- **Data**: Market data management and integration
- **Agents**: Specialist AI agents for different aspects of trading
- **Strategies**: Trading strategy implementations
- **Utilities**: Common utilities and helpers
- **Scripts**: Operational scripts for deployment and maintenance

## Repository Structure
```
/
├── orchestration/           # Agent coordination
├── backtesting/             # All backtesting functionality
├── data/                    # Data management
├── agents/                  # Agent framework
├── strategies/              # Trading strategies
├── utils/                   # General utilities
├── scripts/                 # Operational scripts
├── docs/                    # Documentation
└── tests/                   # Test suite
```

## Getting Started
1. See the [setup documentation](docs/setup.md) for installation instructions
2. Review the [architecture overview](docs/architecture.md) to understand the system
3. Check the [usage examples](docs/usage.md) for common operations

## License
Proprietary - All Rights Reserved
EOF

  # Orchestration README
  cat > orchestration/README.md << 'EOF'
# Orchestration Module

This module handles agent coordination and decision-making processes.

## Key Components
- `decision_session.py`: Core decision-making logic with agent framework integration
- Agent coordination utilities
- Communication management between specialist agents

## Usage
The orchestration module is primarily used to:
1. Initialize agent sessions
2. Manage market data access for agents
3. Coordinate multi-agent decision processes
4. Handle communication between technical, fundamental, and portfolio management agents
EOF

  # Backtesting README
  cat > backtesting/README.md << 'EOF'
# Backtesting Module

This module provides comprehensive backtesting capabilities for trading strategies.

## Key Components
- Core backtesting engine
- Strategy testing utilities
- Performance analysis tools
- Results visualization

## Directory Structure
- `core/`: Core backtesting engine
- `strategies/`: Strategy implementations for testing
- `analysis/`: Results analysis tools
- `utils/`: Helper utilities
- `scripts/`: Execution scripts

## Usage
Run backtests using the provided scripts:
```bash
./backtesting/scripts/run_backtest.sh --strategy=strategy_name --symbol=BTCUSDT --interval=1h --days=30
```
EOF

  # Create other README files
  cat > data/README.md << 'EOF'
# Data Module

This module handles market data acquisition, storage, and preprocessing.

## Key Components
- Data source connectors
- Storage utilities
- Data preprocessing tools

## Directory Structure
- `sources/`: Connectors to data sources (exchanges, APIs)
- `storage/`: Data storage utilities
- `preprocessing/`: Data preparation and normalization

## Usage
Data utilities can be used directly or through the backtesting/trading modules.
EOF

  cat > agents/README.md << 'EOF'
# Agents Module

This module contains the specialist AI agents used in the trading system.

## Key Components
- Technical analysis agents
- Fundamental analysis agents
- Portfolio management agents

## Directory Structure
- `technical/`: Technical analysis specialists
- `fundamental/`: Fundamental analysis specialists
- `portfolio/`: Portfolio management specialists

## Usage
Agents are typically accessed through the orchestration module and not used directly.
EOF

  # Create documentation
  cat > docs/setup.md << 'EOF'
# Setup Instructions

## Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL database
- OpenAI API key

## Installation
1. Clone the repository
2. Install Python dependencies: `pip install -r requirements.txt`
3. Install Node.js dependencies: `npm install`
4. Set up environment variables in `.env`
5. Initialize the database: `python setup_database.py`

## Environment Variables
- `DATABASE_URL`: PostgreSQL database connection string
- `OPENAI_API_KEY`: OpenAI API key for agent functionality
- `ALPACA_API_KEY` and `ALPACA_API_SECRET`: For paper trading (optional)
EOF

  cat > docs/architecture.md << 'EOF'
# System Architecture

## Overview
The trading system uses a multi-agent architecture where specialist AI agents collaborate to make trading decisions.

## Core Components
1. **Decision Framework**: Orchestrates agent communication and decision-making
2. **Agent System**: Specialist agents for different aspects of analysis
3. **Backtesting Engine**: Framework for testing strategies against historical data
4. **Data Management**: Market data acquisition and storage

## Data Flow
1. Market data is acquired from exchanges or APIs
2. Data is processed and stored in the database
3. During decision-making or backtesting, agents access the data
4. Agents communicate and collaborate to produce trading decisions
5. Decisions are executed or recorded for analysis

## Agent Communication
Agents use a structured communication protocol to share insights and form consensus.
EOF

  cat > docs/usage.md << 'EOF'
# Usage Examples

## Running a Backtest
```bash
./run_backtest.sh --strategy=multi_agent --symbol=BTCUSDT --interval=1h --days=30
```

## Analyzing Results
```bash
python backtesting/analysis/analyze_results.py --result-dir=./results/backtest_20250416_123456
```

## Deploying to EC2
```bash
./scripts/deployment/deploy_to_ec2.sh
```

## Running Tests
```bash
pytest tests/
```
EOF

  echo "✅ README files created successfully"
}

# Main function
main() {
  echo "========================================"
  echo "CREATE DIRECTORY STRUCTURE SCRIPT"
  echo "========================================"
  echo "This script will create the target directory"
  echo "structure for the reorganized codebase."
  echo "========================================"
  
  # Create directories
  create_dirs
  
  # Create README files
  create_readmes
  
  echo -e "\n========================================"
  echo "DIRECTORY STRUCTURE CREATION COMPLETED"
  echo "========================================"
  echo "You can now proceed with the reorganization process."
  echo "========================================\n"
}

# Run the main function
main
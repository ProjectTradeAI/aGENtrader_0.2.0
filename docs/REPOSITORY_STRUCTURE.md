# aGENtrader v2.2 Repository Structure

This document provides a detailed overview of the aGENtrader v2.2 repository structure after the code reorganization.

## Directory Structure

```
/
├── agents/                     # AI agent components
│   ├── data_providers/         # Market data providers
│   │   ├── binance_data_provider.py
│   │   └── market_data_provider_factory.py
│   ├── base_agent.py           # Base class for all agents
│   ├── technical_analyst_agent.py
│   ├── sentiment_aggregator_agent.py
│   ├── liquidity_analyst_agent.py
│   ├── portfolio_manager_agent.py
│   ├── position_sizer_agent.py
│   ├── risk_guard_agent.py
│   └── trade_executor_agent.py
│
├── core/                       # Core system functionality
│   ├── logging/                # Logging systems
│   │   └── decision_logger.py  # Logger for agent decisions
│   ├── trading/                # Trading logic
│   │   └── live_trading.py     # Live trading system
│   ├── core_orchestrator.py    # Main orchestration logic
│   └── trigger_scheduler.py    # Scheduler for recurring actions
│
├── data/                       # Data storage and management
│   ├── feed/                   # Market data feeds
│   ├── live/                   # Live trading data
│   ├── simulated/              # Simulated/backtesting data
│   ├── coinapi_fetcher.py      # CoinAPI integration
│   └── database.py             # Database operations
│
├── config/                     # Configuration files
│   └── default.json            # Default configuration
│
├── deployment/                 # Deployment scripts
│   ├── requirements/           # Python requirements
│   │   ├── requirements.txt    # Standard requirements
│   │   └── requirements-ec2.txt # EC2-specific requirements
│   ├── build_image.sh          # Docker image build script
│   ├── deploy_ec2.sh           # EC2 deployment script
│   ├── deploy_local.sh         # Local deployment script
│   └── monitor_agentrader.sh   # Monitoring script
│
├── docker/                     # Docker configuration
│   ├── Dockerfile              # Main Dockerfile
│   └── docker-compose.yml      # Docker Compose configuration
│
├── docs/                       # Documentation
│   ├── v2.2.0-RC1-RELEASE.md   # Release notes
│   ├── API_ERROR_HANDLING.md   # API error handling guide
│   ├── BINANCE_INTEGRATION.md  # Binance integration guide
│   └── [various other guides]  # Additional documentation
│
├── logs/                       # System logs
│   ├── decisions/              # Trading decision logs
│   └── performance/            # Performance metrics
│
├── scripts/                    # Utility scripts
│   ├── export_decision_dataset.py # Export decisions for analysis
│   ├── git_sync.sh             # Git synchronization
│   ├── view_open_trades.py     # View currently open trades
│   └── view_performance.py     # Performance visualization
│
├── tests/                      # Test framework
│   └── scripts/                # Test scripts
│
├── utils/                      # Utility functions
│   ├── js/                     # JavaScript utilities
│   │   ├── run_python_sync.js  # Python execution wrapper
│   │   ├── start.js            # Main start script
│   │   └── start-dev.js        # Development start script
│   └── config.py               # Configuration utilities
│
├── archive/                    # Archived files
│   ├── aGENtrader_v1/          # Version 1 code archive
│   ├── aGENtrader_v2/          # Early version 2 code
│   ├── md_files/               # Old documentation
│   └── scripts/                # Legacy scripts
│
├── main.py                     # Main application entry point
├── run.py                      # Runner script for the system
├── setup.py                    # Installation script
└── README.md                   # Project overview
```

## Symbolic Links

For backward compatibility and ease of use, several symbolic links are maintained:

- `build_image.sh` → `deployment/build_image.sh`
- `deploy_ec2.sh` → `deployment/deploy_ec2.sh`
- `deploy_local.sh` → `deployment/deploy_local.sh`
- `binance_data_provider.py` → `agents/data_providers/binance_data_provider.py`
- `market_data_provider_factory.py` → `agents/data_providers/market_data_provider_factory.py`
- `BINANCE_INTEGRATION.md` → `docs/BINANCE_INTEGRATION.md`
- `LIVE_TRADING.md` → `docs/LIVE_TRADING.md`
- `TESTING_GUIDE.md` → `docs/TESTING_GUIDE.md`
- `default.json` → `config/default.json`

## Key File Descriptions

### Entry Points

- `main.py`: Main entry point for the application
- `run.py`: Runner script for the trading system

### Agent Components

- `agents/base_agent.py`: Base class for all analyst agents
- `agents/technical_analyst_agent.py`: Technical analysis agent
- `agents/sentiment_aggregator_agent.py`: Sentiment analysis agent

### Core System

- `core/core_orchestrator.py`: Main orchestration logic
- `core/logging/decision_logger.py`: Decision logging system
- `core/trading/live_trading.py`: Live trading system

### Deployment

- `deployment/build_image.sh`: Docker image build script
- `deployment/deploy_ec2.sh`: EC2 deployment script
- `deployment/deploy_local.sh`: Local deployment script

### Docker

- `docker/Dockerfile`: Main Dockerfile
- `docker/docker-compose.yml`: Docker Compose configuration

## Organizational Principles

1. **Modular Design**: Each component is organized by functionality
2. **Clear Boundaries**: Clear separation between agents, core system, and data management
3. **Configuration Separation**: Configurations are kept separate from code
4. **Backward Compatibility**: Symbolic links maintain compatibility with existing scripts
5. **Documentation**: Comprehensive documentation in the `docs` directory
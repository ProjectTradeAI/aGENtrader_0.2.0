# aGENtrader v2

A modern multi-agent trading platform built with AutoGen Core and Python, focused on backend intelligence.

## Overview

aGENtrader v2 is a complete redesign of the original trading system, rebuilt from the ground up with a focus on:

- **Clean Architecture**: Modular, decoupled design for testability and maintainability
- **AutoGen Core**: Leveraging the latest multi-agent framework for sophisticated market analysis
- **Backend Intelligence**: Pure Python implementation focused on decision quality
- **Simulation Capabilities**: Realistic market event simulation for development and testing

## Key Components

- **Market Event Simulator**: Generates realistic market data for development and testing
- **Specialized Agents**:
  - LiquidityAnalystAgent: Analyzes market depth, volume profiles, and funding rates
  - TechnicalAnalystAgent: Evaluates price action, indicators, and chart patterns
  - SentimentAnalystAgent: Analyzes market sentiment from various sources
  - DecisionAgent: Makes final trading decisions with confidence scores and agent weighting
  - PortfolioManagerAgent: Tracks portfolio allocations and enforces exposure limits
  - RiskGuardAgent: Evaluates trade risk factors and vetoes high-risk trades
  - PositionSizerAgent: Calculates optimal position sizes based on confidence and volatility
- **Core Orchestrator**: Manages the flow of data between agents
- **Database Connector**: PostgreSQL integration for real market data (when available)

## Getting Started

### Installation

#### Option 1: Direct Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/aGENtrader.git
cd aGENtrader/aGENtrader_v2

# Install dependencies
pip install -r requirements.txt
```

#### Option 2: Docker Installation (Recommended for Deployment)

```bash
# Clone the repository
git clone https://github.com/yourusername/aGENtrader.git
cd aGENtrader

# Create and configure environment variables
cp .env.example .env
# Edit .env file to add your CoinAPI key and other settings

# Build and run with Docker Compose
docker-compose up -d
```

For detailed Docker deployment instructions, see the [Docker Deployment](#docker-deployment) section below.

### Running the Pipeline

```bash
# Run a single market event simulation
python example_pipeline.py --mode single --symbol BTCUSDT --interval 1h --event-type normal

# Run a batch of simulations
python example_pipeline.py --mode batch --num-runs 3

# Run live trading mode
python live_trading.py --symbol BTC/USDT --interval 1h
```

## System Architecture

The system follows a pipeline architecture:

```
Market Event → [LiquidityAnalystAgent, TechnicalAnalystAgent, SentimentAnalystAgent] → DecisionAgent → PortfolioManagerAgent → RiskGuardAgent → TradeExecutorAgent → Performance Tracking
```

Each agent specializes in a specific aspect of market analysis, with the orchestrator managing the overall flow.

## Development

- Python 3.8+ recommended
- Uses mock LLM provider for development
- Gracefully handles missing market data for offline development

## Features

- **Market Data Integration**: Live data integration with CoinAPI.io
- **Multi-Agent Analysis**: Multiple specialized agents collaborate to analyze market conditions
- **Weighted Decision Making**: Configurable agent weights for optimized trading decisions
- **Sentiment Analysis**: Market sentiment evaluation with configurable data sources
- **Trade Execution**: Simulated trade execution with configurable risk parameters 
- **Performance Tracking**: Comprehensive metrics for trade performance analysis
- **Agent Contribution Analysis**: In-depth analysis of each agent's performance
- **Risk Management**: Multi-layered risk controls with portfolio limits and risk guard validation
- **Risk-Factor Analysis**: Trade risk evaluation across volatility, liquidity, and market conditions

## Docker Deployment

For production deployments, we recommend using Docker to ensure consistent environments and easy deployment on servers like EC2.

### Docker Setup Details

The Docker setup in the root directory includes:

- **Dockerfile**: Defines the container image based on Python 3.11
- **docker-compose.yml**: Simplifies container management and volume mounting
- **.env.example**: Template for environment variables
- **.dockerignore**: Excludes unnecessary files from the container

### Key Features

- **Volume Persistence**: Your logs, reports, and trading data persist across container restarts
- **Configuration Mounting**: Edit settings without rebuilding the container
- **Environment Variables**: Set API keys and other settings via environment variables
- **Database Support**: Optional PostgreSQL database setup for market data storage

### Running with Docker

```bash
# Building and starting with Docker Compose
cd /path/to/aGENtrader
docker-compose up -d

# View logs
docker-compose logs -f

# Run a specific command in the container
docker-compose run --rm aGENtrader python aGENtrader_v2/live_trading.py --symbol ETH/USDT --interval 15m
```

### Data Persistence

The Docker setup mounts these volumes for data persistence:

- `./aGENtrader_v2/logs`: For error logs, decision logs, and portfolio snapshots
- `./aGENtrader_v2/reports`: For performance reports and analytics
- `./aGENtrader_v2/trades`: For executed trade records
- `./aGENtrader_v2/config`: For configuration files that can be edited without rebuilding

### Environment Variables

The following environment variables can be set in your `.env` file:

- `COINAPI_KEY`: Your CoinAPI.io API key
- `DATABASE_URL`: PostgreSQL connection string (if using external database)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
- `TRADING_MODE`: Trading mode (disabled, dry_run, live)
- Database credentials if using the Postgres service

## Future Plans

- Add external sentiment data API integration (LunarCrush, Santiment)
- Implement dynamic agent weighting based on performance
- Create a web dashboard for performance visualization
- Add proper database schemas for persistent market data
- Develop a REST API for external integration

## License

This project is licensed under the terms of the MIT license.
# Multi-Agent Trading System: Backend Focus

This repository has been reorganized to focus solely on the backend trading system first, with all frontend components archived. This allows us to ensure the core trading functionality is robust before adding a user interface.

## Current Structure

```
.
├── agents/                  # Specialist trading agents
│   ├── technical/           # Technical analysis
│   ├── fundamental/         # Fundamental analysis
│   └── portfolio/           # Portfolio management
├── api/                     # API interface between Python and Node.js
│   └── trading_api.py       # Python API bridge
├── data/                    # Data management
│   ├── sources/             # Data source connectors
│   └── storage/             # Database integration
├── orchestration/           # Agent coordination
│   └── decision_session.py  # Decision engine
├── backtesting/             # Backtesting framework
├── server/                  # Node.js API server
│   └── index.js             # Express server
├── logs/                    # System logs
└── results/                 # Trading results and analysis
```

## Getting Started

1. Start the API server:
   ```
   node server/index.js
   ```

2. API Endpoints:
   - `GET /api/health` - Check system health
   - `GET /api/system` - Get system information
   - `POST /api/decision` - Request a trading decision
   - `POST /api/backtest` - Run a backtest

## Next Steps

1. Finalize the Python trading system implementation
2. Complete the integration with the API server
3. Implement comprehensive testing
4. Add a frontend interface (in future phases)

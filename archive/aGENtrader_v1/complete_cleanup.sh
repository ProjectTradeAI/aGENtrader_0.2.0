#!/bin/bash
# Complete cleanup script for Multi-Agent Trading System
echo "Starting comprehensive cleanup process..."

# Create archive directories if they don't exist
mkdir -p archive/{python_files,scripts,backtesting,config,test_files,logs,misc,chunks,data_files}

# Move unnecessary files to the archive
echo "Archiving unnecessary files..."

# Python files that are not part of the new structure
echo "Archiving Python files..."
KEEP_PYTHONS="inventory_codebase.py reorganize_codebase.py test_system.py"

for pyfile in *.py; do
    if [ -f "$pyfile" ]; then
        if ! echo "$KEEP_PYTHONS" | grep -q "$pyfile"; then
            echo "  - Archiving $pyfile"
            mv "$pyfile" archive/python_files/ 2>/dev/null
        fi
    fi
done

# Archive log files
echo "Archiving log files..."
for logfile in *.log; do
    if [ -f "$logfile" ]; then
        echo "  - Archiving $logfile"
        mv "$logfile" archive/logs/ 2>/dev/null
    fi
done

# Archive old config files
echo "Archiving configuration files..."
for configfile in *.json *.cjs *.config.*; do
    if [ -f "$configfile" ] && [ "$configfile" != "package.json" ] && [ "$configfile" != "tsconfig.json" ] && [ "$configfile" != "tailwind.config.ts" ] && [ "$configfile" != "theme.json" ] && [ "$configfile" != "vite.config.ts" ]; then
        echo "  - Archiving $configfile"
        mv "$configfile" archive/config/ 2>/dev/null
    fi
done

# Archive chunk files
echo "Archiving chunk files..."
mv chunk_* archive/chunks/ 2>/dev/null

# Archive shell scripts
echo "Archiving shell scripts..."
KEEP_SHELL="backup_codebase.sh complete_cleanup.sh"
for shellfile in *.sh; do
    if [ -f "$shellfile" ]; then
        if ! echo "$KEEP_SHELL" | grep -q "$shellfile"; then
            echo "  - Archiving $shellfile"
            mv "$shellfile" archive/scripts/ 2>/dev/null
        fi
    fi
done

# Archive various data files
echo "Archiving data files..."
for datafile in *.txt *.csv *.tar.gz; do
    if [ -f "$datafile" ]; then
        echo "  - Archiving $datafile"
        mv "$datafile" archive/data_files/ 2>/dev/null
    fi
done

# Create .gitignore to prevent committing the archive
echo "Creating .gitignore for the archive..."
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Archived files
archive/
__pycache__/
*.pyc
*.pyo
.DS_Store
.env.local
node_modules/
EOF
fi

# Create a simple main.py entry point
echo "Creating main.py entry point..."
cat > main.py << 'EOF'
"""
Multi-Agent Trading System Entry Point

This file provides a simple entry point to the trading system.
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/trading_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

def main():
    """Main entry point for the trading system"""
    try:
        from orchestration.decision_session import DecisionSession
        
        # Get symbol from command line if provided, otherwise use default
        symbol = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
        logging.info(f"Starting decision session for {symbol}")
        
        # Initialize the decision session
        session = DecisionSession()
        
        # Run the decision
        result = session.run_decision(symbol)
        
        # Display the result
        print("\n===== Trading Decision =====")
        print(f"Symbol: {symbol}")
        print(f"Decision: {result.get('decision', 'No decision')}")
        print(f"Confidence: {result.get('confidence', 0)}")
        print(f"Entry Price: {result.get('entry_price', 'N/A')}")
        print(f"Stop Loss: {result.get('stop_loss', 'N/A')}")
        print(f"Take Profit: {result.get('take_profit', 'N/A')}")
        print(f"Position Size: {result.get('position_size', 'N/A')}")
        print("\nReasoning:")
        print(result.get('reasoning', 'No reasoning provided'))
        
        logging.info(f"Completed decision session for {symbol}")
        return 0
    
    except ImportError as e:
        logging.error(f"Import error: {str(e)}")
        print(f"Error: {str(e)}")
        print("The system may not be correctly installed or initialized.")
        return 1
    
    except Exception as e:
        logging.error(f"Error during execution: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the main function
    sys.exit(main())
EOF

# Create a proper README
echo "Creating README.md..."
cat > README.md << 'EOF'
# Multi-Agent Trading System

An advanced trading platform using a collaborative multi-agent approach for cryptocurrency market analysis.

## Overview

This system integrates several AI agents specializing in different aspects of trading analysis:

- **Technical Analysis Agent**: Analyzes price patterns and technical indicators
- **Fundamental Analysis Agent**: Evaluates market sentiment, news, and fundamentals
- **Portfolio Management Agent**: Handles risk assessment and position sizing

Agents collaborate through a structured decision-making process orchestrated by the Decision Session framework.

## Directory Structure

```
.
├── agents/                 # Specialist agents
│   ├── technical/          # Technical analysis agents
│   ├── fundamental/        # Fundamental analysis agents
│   └── portfolio/          # Portfolio management agents
├── orchestration/          # Agent coordination
│   └── decision_session.py # Decision-making framework
├── data/                   # Data management
│   ├── sources/            # Data source connectors
│   └── storage/            # Database integration
├── backtesting/            # Backtesting framework
│   ├── core/               # Core backtesting engine
│   ├── analysis/           # Analysis tools
│   └── scripts/            # Execution scripts
├── logs/                   # System logs
└── results/                # Trading results and metrics
```

## Getting Started

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Run a trading decision:
   ```
   python main.py BTCUSDT
   ```

4. Run a backtest:
   ```
   ./backtesting/scripts/run_backtest.sh --symbol BTCUSDT --interval 1h --days 30
   ```

## Core Components

- **Decision Session**: Orchestrates the multi-agent decision process
- **Market Data Integration**: Provides authentic market data from multiple sources
- **Backtesting Framework**: Evaluates strategy performance on historical data
- **Portfolio Management**: Handles position sizing and risk management

## Development

- Use `test_system.py` to verify system integrity
- Follow the code structure in `agents/README.md` for agent development
- See `backtesting/README.md` for adding custom backtesting strategies

## Deployment

The system can be deployed to AWS EC2 for improved performance and to leverage local LLMs:

```
./scripts/deploy_to_ec2.sh
```
EOF

# Copy essential configuration files to their proper locations
echo "Copying essential configuration files..."
mkdir -p config
if [ -f ".env" ]; then
    cp .env config/.env.example
    # Remove any API keys or sensitive information
    sed -i 's/\(.*_KEY=\).*/\1YOUR_API_KEY_HERE/g' config/.env.example
    sed -i 's/\(.*_SECRET=\).*/\1YOUR_SECRET_HERE/g' config/.env.example
fi

# Create directories for results
echo "Creating results directories..."
mkdir -p results/{backtests,trading,analysis}

# Cleanup any __pycache__ directories
echo "Cleaning up __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} +

# Create an initialization script
echo "Creating initialization script..."
cat > initialize_system.py << 'EOF'
"""
System Initialization Script

This script initializes the trading system and verifies that all components
are properly configured and working.
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/initialization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

def check_environment():
    """Check if environment variables are set"""
    required_vars = ["OPENAI_API_KEY", "ALPACA_API_KEY", "ALPACA_API_SECRET"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logging.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file")
        return False
    
    logging.info("Environment variables check passed")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import pandas
        import numpy
        import sqlalchemy
        import requests
        logging.info("All required packages are installed")
        return True
    except ImportError as e:
        logging.error(f"Missing dependency: {str(e)}")
        print(f"Error: Missing dependency - {str(e)}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_directory_structure():
    """Check if the directory structure is correct"""
    required_dirs = [
        "agents/technical", "agents/fundamental", "agents/portfolio",
        "data/sources", "data/storage",
        "orchestration",
        "backtesting/core", "backtesting/scripts"
    ]
    
    missing_dirs = [d for d in required_dirs if not os.path.isdir(d)]
    
    if missing_dirs:
        logging.warning(f"Missing directories: {', '.join(missing_dirs)}")
        print(f"Warning: Missing directories: {', '.join(missing_dirs)}")
        return False
    
    logging.info("Directory structure check passed")
    return True

def main():
    """Main initialization function"""
    print("Starting system initialization...")
    logging.info("Starting system initialization")
    
    # Create required directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("results/backtests", exist_ok=True)
    
    # Check environment and dependencies
    env_check = check_environment()
    dep_check = check_dependencies()
    dir_check = check_directory_structure()
    
    if env_check and dep_check and dir_check:
        print("\n✅ System initialization successful!")
        logging.info("System initialization successful")
        return 0
    else:
        print("\n⚠️ System initialization completed with warnings.")
        logging.warning("System initialization completed with warnings")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

echo "Cleanup process completed successfully!"
echo "New directory structure:"
find . -maxdepth 2 -type d | sort | grep -v "__pycache__" | grep -v "node_modules" | grep -v "\.git"
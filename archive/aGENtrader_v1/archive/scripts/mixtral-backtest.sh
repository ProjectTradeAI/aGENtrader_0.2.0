#!/bin/bash
# Quick shortcut for running full-scale multi-agent backtest with Mixtral

# Show a simple banner
echo -e "\033[0;36m"
echo "╔══════════════════════════════════════════════════════╗"
echo "║  MIXTRAL MULTI-AGENT BACKTEST                        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "\033[0m"

# Execute the full backtest script with appropriate options
./run-full-backtest.sh "$@"

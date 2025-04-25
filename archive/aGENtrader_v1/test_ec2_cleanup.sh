#!/bin/bash
# Simplified EC2 Cleanup Script for testing

echo "Starting simplified EC2 cleanup test..."

# Create the required directory structure if it doesn't exist
echo "Creating directory structure..."
mkdir -p agents api backtesting config data docs orchestration scripts server strategies tests utils archive

# Move files to their appropriate directories (basic tests only)
echo "Moving agent files..."
find . -maxdepth 1 -name "*agent*.py" -not -path "./agents/*" -exec mv {} ./agents/ \; 2>/dev/null || true

echo "Moving API files..."
find . -maxdepth 1 -name "*api*.py" -not -path "./api/*" -exec mv {} ./api/ \; 2>/dev/null || true

echo "Moving backtesting files..."
find . -maxdepth 1 -name "*backtest*.py" -not -path "./backtesting/*" -exec mv {} ./backtesting/ \; 2>/dev/null || true

echo "Moving configuration files..."
find . -maxdepth 1 -name "*config*.json" -not -path "./config/*" -exec mv {} ./config/ \; 2>/dev/null || true

echo "Moving data files..."
find . -maxdepth 1 -name "*.csv" -not -path "./data/*" -exec mv {} ./data/ \; 2>/dev/null || true

echo "Moving documentation files..."
find . -maxdepth 1 -name "*.md" -not -path "./docs/*" -not -name "README.md" -exec mv {} ./docs/ \; 2>/dev/null || true

echo "Moving server-related files..."
find . -maxdepth 1 -name "*server*.js" -not -path "./server/*" -exec mv {} ./server/ \; 2>/dev/null || true

echo "Moving utility files..."
find . -maxdepth 1 -name "*util*.py" -not -path "./utils/*" -exec mv {} ./utils/ \; 2>/dev/null || true

# Move outdated or redundant files to archive
echo "Archiving outdated files..."
find . -maxdepth 1 -name "*.bak" -exec mv {} ./archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*old*" -exec mv {} ./archive/ \; 2>/dev/null || true

echo "Simplified EC2 cleanup test completed!"
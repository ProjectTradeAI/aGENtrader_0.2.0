#!/bin/bash
# Script to clean up unused and redundant files in the data directory

echo "Starting data directory cleanup..."

# Create archive directory for data files if it doesn't exist
mkdir -p archive/data_files

# Keep essential data directories, archive the rest
ESSENTIAL_DIRS="sources storage market_data"

echo "Moving redundant data directories to archive..."

# Process each directory in the data folder
cd data || exit 1
for dir in */; do
    dir_name="${dir%/}"  # Remove trailing slash
    
    # Check if this is an essential directory
    if echo "$ESSENTIAL_DIRS" | grep -q "$dir_name"; then
        echo "  • Keeping essential directory: $dir_name"
    else
        echo "  • Archiving directory: $dir_name"
        mkdir -p "../archive/data_files/$dir_name"
        cp -r "$dir_name"/* "../archive/data_files/$dir_name/" 2>/dev/null
        rm -rf "$dir_name"
    fi
done

# Archive dated paper trading directories
echo "Archiving dated paper trading directories..."
for dir in paper_trading_*/ test_paper_trading_*/; do
    if [ -d "$dir" ]; then
        dir_name="${dir%/}"
        echo "  • Archiving: $dir_name"
        mkdir -p "../archive/data_files/$dir_name"
        cp -r "$dir_name"/* "../archive/data_files/$dir_name/" 2>/dev/null
        rm -rf "$dir_name"
    fi
done

# Archive JSON files (after preserving essential ones)
echo "Processing data JSON files..."
ESSENTIAL_JSON="database_structure.json market_data_summary.json"

for json_file in *.json; do
    if [ -f "$json_file" ]; then
        if echo "$ESSENTIAL_JSON" | grep -q "$json_file"; then
            echo "  • Keeping essential JSON: $json_file"
        else
            echo "  • Archiving JSON: $json_file"
            cp "$json_file" "../archive/data_files/" 2>/dev/null
            rm "$json_file"
        fi
    fi
done

# Clean up any text files that might be temporary
echo "Cleaning up text and temporary files..."
for txt_file in *.txt; do
    if [ -f "$txt_file" ] && [ "$txt_file" != "README.txt" ]; then
        echo "  • Archiving: $txt_file"
        cp "$txt_file" "../archive/data_files/" 2>/dev/null
        rm "$txt_file"
    fi
done

# Return to the root directory
cd .. || exit 1

# Create simplified structure for the data directory
echo "Creating simplified data directory structure..."

# Ensure essential directories exist
mkdir -p data/sources data/storage data/market_data

# Create a README for the data directory explaining the new structure
cat > data/README.md << 'EOF'
# Data Management

This directory contains essential data components for the Multi-Agent Trading System.

## Directory Structure

### `/data/sources`
Data source connectors that retrieve market data from various external sources.

- Contains interfaces to Alpaca, databases, and other data providers
- Provides standardized data access regardless of source

### `/data/storage`
Components for persistent storage and database interaction.

- Database connection and query utilities
- Data persistence and retrieval logic
- Schema definitions and migrations

### `/data/market_data`
Market data storage and processing.

- Historical market data cache
- Price and volume data
- OHLC candles and other time-series data

## Data Files

- `database_structure.json`: Schema definition for the database
- `market_data_summary.json`: Summary of available market data

## Note on Archive

All non-essential data has been archived in `archive/data_files/`. This includes:
- Old test results and logs
- Paper trading simulations
- Performance analysis
- Dated test directories
- Risk testing data
EOF

echo "Data directory cleanup complete!"
echo "Essential data preserved in data/sources, data/storage, and data/market_data"
echo "All other data archived in archive/data_files/"
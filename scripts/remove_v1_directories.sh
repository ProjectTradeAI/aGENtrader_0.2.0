#!/bin/bash

# This script removes the original v1 directories after they've been copied
# to aGENtrader_v1 directory

echo "Removing original v1 directories that are already copied to aGENtrader_v1/..."

# Function to safely remove a directory if it exists
remove_if_exists() {
    if [ -d "$1" ] && [ "$1" != "aGENtrader_v1" ] && [ "$1" != "aGENtrader_v2" ] && [ "$1" != "temp_v2_repo" ] && [ "$1" != ".git" ]; then
        echo "Removing directory: $1"
        rm -rf "$1"
    fi
}

# Remove directories that belong exclusively to v1
for dir in agents agents_backup api archive backtesting backups coding config data \
           data_integrity_deployment deployment docs examples logs models node_modules \
           orchestration results scripts server strategies tests utils; do
    remove_if_exists "$dir"
done

echo "Removal complete!"
echo "Checking the root directory structure..."
ls -la
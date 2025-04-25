#!/bin/bash
# Apply data integrity implementation

# Set project path
PROJECT_PATH=$(dirname $(readlink -f $0))
echo "Project path: ${PROJECT_PATH}"

# Ensure agents directory exists
mkdir -p "${PROJECT_PATH}/../agents"

# Copy data_integrity.py to agents directory if it doesn't exist
if [ ! -f "${PROJECT_PATH}/../agents/data_integrity.py" ]; then
    echo "Copying data_integrity.py to agents directory"
    cp -v "${PROJECT_PATH}/data_integrity.py" "${PROJECT_PATH}/../agents/"
fi

# Apply patches
echo "Applying decision session patch..."
python "${PROJECT_PATH}/patch_decision_session.py"

echo "Applying run session patch..."
python "${PROJECT_PATH}/patch_run_session.py"

echo "Verifying data integrity implementation..."
python "${PROJECT_PATH}/verify_data_integrity.py"

echo "Data integrity implementation complete!"
echo "You can now restart your trading system to apply the changes."

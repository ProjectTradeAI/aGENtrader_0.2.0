#!/bin/bash
# aGENtrader v2.2 - Rollback Test Script
# This script simulates a rollback procedure locally for testing

set -e

# Display header
echo "======================================================================"
echo "              aGENtrader v2.2 - Rollback Test Script"
echo "======================================================================"
echo

# Get current branch/tag
CURRENT_VERSION=$(git describe --tags --always)
echo "Current version: $CURRENT_VERSION"

# Simulate a deployment with a new "buggy" version
echo
echo "Simulating a deployment with a 'buggy' version..."
echo

# Create a temporary branch
TEMP_BRANCH="temp-buggy-deployment-$(date +%s)"
git checkout -b $TEMP_BRANCH

# Make a dummy change
echo "# This is a simulated buggy deployment" >> README.md
git add README.md
git commit -m "Simulated buggy deployment for rollback testing"

echo "Deployed 'buggy' version: $(git rev-parse --short HEAD)"
echo

# Now simulate a rollback
echo "Simulating rollback to previous version: $CURRENT_VERSION..."
echo

git checkout $CURRENT_VERSION

echo "Successfully rolled back to: $CURRENT_VERSION"
echo

# Clean up
echo "Cleaning up test branch..."
git branch -D $TEMP_BRANCH

echo
echo "Rollback test completed successfully!"
echo "This demonstrates the ability to roll back to a previous known good version."
echo

exit 0
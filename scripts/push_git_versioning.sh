#!/bin/bash
# Script to create and push the v2 versioning tags and branches for aGENtrader

# Ensure we're up to date with origin
echo "Pulling latest changes from origin..."
git pull origin main

# Create v2.0.0 tag if it doesn't exist
if ! git tag -l | grep -q "v2.0.0"; then
    echo "Creating v2.0.0 tag..."
    git tag -a v2.0.0 -m "Initial production-ready version after successful 24h test"
else
    echo "Tag v2.0.0 already exists"
fi

# Create v2.1-dev branch if it doesn't exist
if ! git branch -l | grep -q "v2.1-dev"; then
    echo "Creating v2.1-dev branch..."
    git branch v2.1-dev
else
    echo "Branch v2.1-dev already exists"
fi

# Push tag and branch to origin
echo "Pushing v2.0.0 tag to origin..."
git push origin v2.0.0

echo "Pushing v2.1-dev branch to origin..."
git push origin v2.1-dev

echo "Done! The versioning has been set up correctly."
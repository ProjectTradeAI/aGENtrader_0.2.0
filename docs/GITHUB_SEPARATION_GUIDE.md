# GitHub Repository Separation Guide

This document provides guidance on how to properly separate the aGENtrader v1 and v2 implementations in GitHub repositories.

## Current State

The repository currently contains:
- `aGENtrader_v1/`: Original implementation (archived)
- `aGENtrader_v2/`: New implementation with AutoGen Core

## Option 1: Maintain as a Single Repository with Branches

### Steps:
1. Create a `v1-archive` branch from the current state
2. On the `main` branch, remove unnecessary v1 files
3. Use the `main` branch for active v2 development
4. Reference the `v1-archive` branch when needed

### Commands:
```bash
# Create archive branch
git checkout -b v1-archive
git add .
git commit -m "Archive v1 implementation"
git push origin v1-archive

# Return to main branch and clean up
git checkout main
# Remove v1 files (keep only aGENtrader_v2/ and essential root files)
git add .
git commit -m "Clean up repository for v2 focus"
git push origin main
```

## Option 2: Complete Repository Separation (Recommended)

### Steps:
1. Create a new GitHub repository for aGENtrader v2
2. Push the current aGENtrader_v2 directory to the new repository
3. Archive the original repository or keep it for v1 only

### Commands:
```bash
# Create a new repository on GitHub first (aGENtrader-v2)

# Clone the new empty repository
git clone https://github.com/yourusername/aGENtrader-v2.git
cd aGENtrader-v2

# Copy the v2 files from the original repository
cp -r /path/to/original/aGENtrader_v2/* .

# Add and commit
git add .
git commit -m "Initial commit of aGENtrader v2"
git push origin main

# (Optional) Archive the original repository on GitHub
```

## Repository Structure After Separation

### aGENtrader-v2 Repository
```
/
├── agents/
├── config/
├── data/
├── models/
├── orchestrator/
├── simulators/
├── example_pipeline.py
├── run.py
├── README.md
└── requirements.txt
```

## Documentation Updates

After separation, update:

1. Repository descriptions on GitHub
2. README files to point to the correct repositories
3. Any external documentation referencing these projects

## Benefits of Separation

- Cleaner development history
- Focused issue tracking
- Simplified codebase
- Clear separation of concerns
- Easier onboarding for new developers
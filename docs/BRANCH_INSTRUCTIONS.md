# Git Branch Instructions for Agent Architecture Migration

This document provides step-by-step instructions for creating the `v2.2.1` branch for the agent architecture migration. These steps should be performed manually as automated Git operations are restricted in the current environment.

## Before You Begin

1. Ensure you have write access to the repository
2. Make sure you have the latest changes from the `main` branch
3. Verify that Git is properly configured on your machine

## Step 1: Tag Current Stable State

First, tag the current stable state of the `main` branch for future reference:

```bash
# Ensure you're on the main branch
git checkout main

# Pull latest changes
git pull origin main

# Tag the current stable state
git tag -a v2.2.0-stable -m "Stable version before agent architecture migration"

# Push the tag to remote
git push origin v2.2.0-stable
```

## Step 2: Create and Switch to New Branch

Create the new branch for the agent architecture migration:

```bash
# Create and switch to new branch
git checkout -b v2.2.1

# Verify you're on the new branch
git branch
```

## Step 3: Commit Your Changes

Make sure all changes to the agent architecture are committed:

```bash
# Check status of changes
git status

# Add all changes
git add .

# Create a commit with descriptive message
git commit -m "Implement standardized agent architecture with interfaces and base classes"
```

## Step 4: Push the Branch to Remote

Push the new branch to the remote repository:

```bash
# Push the branch
git push origin v2.2.1

# Verify the branch was pushed
git branch -a
```

## Step 5: Create Pull Request (Optional)

If using GitHub or similar platform, create a pull request for code review before merging to `main`:

1. Go to the repository on GitHub
2. Click "Compare & pull request" for the v2.2.1 branch
3. Add description of the changes and request reviewers
4. Leave as draft until fully tested on EC2

## Testing Process

Before merging this branch to `main`, ensure:

1. All agents are properly migrated to the new architecture
2. The system functions correctly on EC2 with the new architecture
3. All tests pass, including the new agent test framework

## Rollback Instructions

If issues are discovered, you can roll back to the stable tag:

```bash
# Checkout the stable tag
git checkout v2.2.0-stable

# Create a new branch from the stable tag if needed
git checkout -b hotfix-from-stable

# OR return to main branch
git checkout main
```

## Documentation Updates

The following documentation has been updated to reflect the architecture changes:

1. `README.md`: Added agent architecture section and updated recent changes
2. `docs/DEV_NOTES.md`: Created with migration details and development notes
3. `docs/AGENT_MIGRATION_GUIDE.md`: Created with step-by-step migration instructions
4. `tests/README.md`: Added for test framework documentation
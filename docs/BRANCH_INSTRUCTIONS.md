# Branch Management Guidelines

This document provides guidelines for managing branches during the migration to the new agent architecture. The goal is to maintain a stable main branch while implementing significant architectural changes.

## Branch Strategy

We're using the following branch structure:

1. **main** - The stable production branch (v2.2.0-stable)
2. **v2.2.1-agent-migration** - Branch for agent architecture migration
3. **feature/[feature-name]** - Branches for individual features

## Current Branches

| Branch Name | Version | Purpose | Status |
|-------------|---------|---------|--------|
| main | v2.2.0 | Production-ready code | Stable |
| v2.2.1-agent-migration | v2.2.1-dev | Agent architecture migration | In Progress |

## Creating the Migration Branch

If you haven't already created the migration branch, follow these steps:

```bash
# Make sure you're on the main branch and up to date
git checkout main
git pull origin main

# Create the migration branch
git checkout -b v2.2.1-agent-migration

# Push the branch to remote
git push -u origin v2.2.1-agent-migration
```

## Working on the Migration

When working on the agent architecture migration:

1. **Always work on the v2.2.1-agent-migration branch**
2. Make small, incremental commits with clear messages
3. Keep the branch up to date with main by regularly merging changes from main

```bash
# Update your local copy of main
git checkout main
git pull origin main

# Switch back to the migration branch
git checkout v2.2.1-agent-migration

# Merge changes from main (resolve conflicts if needed)
git merge main
```

## Testing During Migration

Always test your changes on the migration branch:

1. Run the test harness for individual agents:
   ```bash
   python tests/test_agent_individual.py --agent BaseAnalystAgent --mock-data
   ```

2. Test with real agents as they are migrated:
   ```bash
   python tests/test_agent_individual.py --agent TechnicalAnalystAgent
   ```

3. Run the full system tests:
   ```bash
   python tests/test_system.py
   ```

## Merging Migration Changes Back to Main

Once the migration is complete and thoroughly tested:

1. Create a pull request from v2.2.1-agent-migration to main
2. Have someone else review the changes
3. Run the full test suite on the PR
4. When all tests pass and the PR is approved, merge the changes
5. Tag the main branch with the new version:
   ```bash
   git checkout main
   git pull origin main
   git tag -a v2.2.1 -m "Agent architecture migration"
   git push origin v2.2.1
   ```

## Emergency Fixes During Migration

If you need to fix a critical issue in the main branch while migration is in progress:

1. Create a hotfix branch from main:
   ```bash
   git checkout main
   git checkout -b hotfix/issue-description
   ```

2. Make the necessary changes and commit them

3. Create a PR to merge the hotfix into main

4. After merging to main, update the migration branch:
   ```bash
   git checkout v2.2.1-agent-migration
   git merge main
   ```

## Version Numbering

We follow semantic versioning:

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backward-compatible manner
- **PATCH** version for backward-compatible bug fixes

For the agent migration, we're incrementing the MINOR version since it adds new functionality while maintaining backward compatibility.

## Further Resources

- [Git Branching Guide](https://git-scm.com/book/en/v2/Git-Branching-Branching-Workflows)
- [Semantic Versioning](https://semver.org/)
- [Pull Request Best Practices](https://opensource.com/article/19/7/create-pull-request-github)
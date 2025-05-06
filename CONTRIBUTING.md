# Contributing to aGENtrader v0.2.2

Thank you for your interest in contributing to the aGENtrader project! This document provides guidelines for development and contribution to ensure consistency and quality across the codebase.

## Development Environment

1. Clone the repository
2. Install requirements: `pip install -r agentrader_v2_requirements.txt`
3. Create a new branch for your changes
4. Make your changes following the coding standards
5. Submit a pull request

## Coding Standards

1. Follow PEP 8 style guide for Python code
2. Use consistent naming conventions:
   - Classes: CamelCase
   - Functions and methods: snake_case
   - Constants: UPPERCASE_WITH_UNDERSCORES
3. Write unit tests for new functionality
4. Document your code with docstrings (Google style preferred)

## Version Control

aGENtrader uses semantic versioning (vX.Y.Z):

- **X**: Major version (breaking changes)
- **Y**: Minor version (new features, non-breaking)
- **Z**: Patch version (bug fixes, non-breaking)

### Version Tag Validation

The CI pipeline includes version tag validation to ensure consistency across the codebase. This helps prevent versioning discrepancies between different components.

#### How Version Validation Works

1. The expected version is read from one of the following sources (in order of priority):
   - `version.json`
   - `core/version.py`
   - `config/settings.yaml` (under `system.version`)
   - Environment variable `SYSTEM_VERSION`

2. All output files (JSON, JSONL) in the following directories are scanned:
   - `logs/`
   - `trades/`
   - `datasets/`

3. Files are checked for version tags in the following keys:
   - `version`
   - `system_version`
   - `version_tag`
   - `agent_version`
   - `plan_version`

4. CI will fail if any files have missing or inconsistent version tags.

#### Running Version Validation Locally

You can run version validation manually:

```bash
python scripts/validate_version_tags.py
```

Use the `--verbose` flag for detailed output:

```bash
python scripts/validate_version_tags.py --verbose
```

#### When Updating Versions

When updating the system version:

1. Update the version in `version.json`
2. Update the version in `core/version.py`
3. Update the version in `config/settings.yaml`
4. Run version validation to ensure all components are updated

## Pull Request Process

1. Ensure your code has appropriate test coverage
2. Update the documentation to reflect any changes
3. Verify all CI checks pass, including version validation
4. Update the CHANGELOG.md file with details of changes
5. Request review from a project maintainer

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Follow the golden rule: treat others as you'd like to be treated

Thank you for contributing to aGENtrader!
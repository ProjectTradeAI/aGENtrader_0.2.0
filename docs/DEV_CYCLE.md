# aGENtrader Development Cycle

This document explains how to use the automated development cycle script to streamline your development workflow.

## Overview

The development cycle script (`scripts/dev_cycle.sh`) automates the process of:

1. Pulling the latest code changes from the repository
2. Building a fresh Docker image
3. Deploying the updated container
4. Validating the deployment
5. Providing detailed logs of the process

This tool is designed to save time, prevent manual errors, and provide consistent deployment results.

## Prerequisites

Before using the dev cycle script, ensure you have:

- Git installed and configured
- Docker installed and running
- Proper permissions to execute scripts
- aGENtrader repository cloned locally

## Usage

### Basic Usage

From the root of the aGENtrader repository, run:

```bash
./scripts/dev_cycle.sh
```

The script is interactive and will guide you through the process with clear logs and status updates.

### What happens during execution

1. **Pre-flight checks**:
   - Verifies you're in the correct directory
   - Checks if Docker is installed and running

2. **Git Pull**:
   - Fetches and pulls the latest changes from the main branch
   - Shows a summary of changes if any were pulled

3. **Docker Build**:
   - Builds a fresh Docker image using deployment/build_image.sh
   - Tags the image appropriately

4. **Deployment**:
   - Deploys the container locally or to EC2 (with confirmation)
   - Handles stopping existing containers if needed

5. **Validation**:
   - Runs deployment validation to ensure everything is working
   - Shows detailed logs of the validation process

6. **Summary and Logs**:
   - Displays a summary of the entire process
   - Offers the option to tail logs for monitoring

### Script Safety Features

The script includes several safety features:

- **Idempotent operation**: Safe to run multiple times without adverse effects
- **Error handling**: Exits gracefully if any critical step fails
- **Detailed logging**: Creates a timestamped log file of the entire process
- **Environment checks**: Verifies Docker is running before attempting builds
- **User confirmation**: Requires confirmation for potentially destructive actions

## Troubleshooting

### Common Issues

1. **Git pull failures**:
   - Check your network connection
   - Ensure you have the right repository permissions
   - Resolve any merge conflicts manually before retrying

2. **Docker build failures**:
   - Check Docker daemon is running: `docker info`
   - Ensure sufficient disk space for build
   - Review build logs for specific errors

3. **Deployment failures**:
   - Check for port conflicts (another service using port 8000)
   - Verify environment variables are correctly set
   - Check Docker network settings

4. **Validation issues**:
   - Examine container logs: `docker logs agentrader`
   - Verify API endpoints are accessible
   - Check database connectivity if applicable

### Logs

The script creates detailed logs in the root directory with timestamp:
```
dev_cycle_YYYYMMDD_HHMMSS.log
```

These logs are invaluable for debugging issues that occur during the dev cycle.

## Advanced Usage

### Customizing the Script

You can customize the script by editing the configuration variables at the top:

- `CONTAINER_NAME`: Name of the Docker container
- `IMAGE_NAME`: Name of the Docker image
- `IMAGE_TAG`: Tag for the Docker image
- `GITHUB_REPO`: Git remote name (default: origin)
- `GITHUB_BRANCH`: Git branch to pull from (default: main)

### Manual Steps

If you need to run individual steps manually:

1. **Git pull only**:
   ```bash
   git pull origin main
   ```

2. **Build only**:
   ```bash
   ./deployment/build_image.sh
   ```

3. **Deploy only**:
   ```bash
   ./deployment/deploy_local.sh
   ```

4. **Validate only**:
   ```bash
   python3 deployment/validate_deployment.py
   ```

## Best Practices

1. **Run regularly**: Use the dev cycle script whenever you resume work to ensure you have the latest code
2. **Review logs**: Always check the generated logs to catch subtle issues
3. **Commit first**: Commit your local changes before running the script to avoid losing work
4. **Clean environment**: Occasionally run Docker cleanup to remove old images and containers

## Support

If you encounter issues with the dev cycle script, please:

1. Check the logs for detailed error messages
2. Verify all prerequisites are met
3. Run individual steps manually to isolate the problem
4. Contact the development team if issues persist
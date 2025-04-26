# aGENtrader v2.2 Rollback Procedures

This document provides comprehensive guidance on the rollback procedures implemented in the aGENtrader v2.2 system. The system is designed to support quick and reliable rollbacks to previous versions when deployment issues arise.

## Rollback Architecture

The rollback system leverages the following components:

1. **Git-based versioning**: All code versions are tracked through Git tags and commits
2. **Docker containerization**: All deployments run in Docker containers with version-specific images
3. **Automated scripts**: Scripts automate the rollback process to minimize human error
4. **Validation tools**: Automated checks verify successful rollbacks

## Automated Rollback

### Using the Rollback Script

The primary method for rolling back is to use the automated script:

```bash
# From the project root on your development machine
bash deployment/rollback_ec2.sh [ec2-hostname-or-ip]
```

This script will:

1. Connect to the EC2 instance
2. Retrieve available versions (Git tags) and recent commits
3. Prompt you to select a version to roll back to
4. Confirm your selection
5. Check out the specified version
6. Rebuild Docker containers with the rolled-back version
7. Validate the deployment automatically

### Example Rollback Session

```
====================================================================
          aGENtrader v2.2 - Deployment Rollback
====================================================================

Connecting to EC2 instance...

Available versions:
v0.2.0 - Initial stable release
v0.1.0 - Beta release

Recent commits:
abc1234 (2025-04-24) - Fix deployment pipeline
def5678 (2025-04-23) - Add new technical indicator
ghi9012 (2025-04-22) - Update API integration

Enter version/tag/commit to roll back to: v0.1.0

Confirm rollback to v0.1.0? [y/n]: y

Rolling back to v0.1.0...
Stopping containers...
Checking out version...
Building new image...
Starting containers...
Validating deployment...

Rollback completed successfully!
```

## Manual Rollback

If automated rollback is not possible, follow these manual steps:

1. SSH into your EC2 instance:
   ```bash
   ssh -i aGENtrader.pem ubuntu@ec2-instance-ip
   ```

2. Navigate to the deployment directory:
   ```bash
   cd ~/aGENtrader
   ```

3. List available versions:
   ```bash
   git tag -l
   git log --oneline -n 10
   ```

4. Check out the desired version:
   ```bash
   git fetch --all --tags
   git checkout v0.1.0  # Or specific commit hash
   ```

5. Stop running containers:
   ```bash
   cd docker
   docker-compose down
   ```

6. Rebuild with the older version:
   ```bash
   VERSION=$(git describe --tags --always) docker-compose build --no-cache
   VERSION=$(git describe --tags --always) docker-compose up -d
   ```

7. Validate the deployment:
   ```bash
   cd ..
   python deployment/validate_deployment.py
   ```

## Emergency Rollbacks

For critical system failures, an emergency rollback can be performed:

1. SSH into the EC2 instance
2. Stop all containers:
   ```bash
   docker stop $(docker ps -q)
   ```
3. Run the last known working image directly:
   ```bash
   docker run -d --name agentrader_emergency \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/config:/app/config \
     --env-file .env \
     agentrader:last_known_good_version
   ```

## Versioning System

### Version Identification

The system uses multiple identifiers for versioning:

1. **Git tags**: Formal releases (e.g., `v0.2.0`)
2. **Commit hashes**: Specific code points (e.g., `abcd1234`)
3. **Docker image tags**: Built from Git information

### How Versions Are Managed

1. **In the Dockerfile**:
   ```dockerfile
   ARG VERSION="v0.2.0"
   # ...
   LABEL version="${VERSION}"
   ENV AGENTRADER_VERSION="${VERSION}"
   ```

2. **In docker-compose.yml**:
   ```yaml
   image: agentrader:${VERSION:-latest}
   ```

3. **In build scripts**:
   ```bash
   VERSION=$(git describe --tags --always)
   docker build --build-arg VERSION=$VERSION -t agentrader:$VERSION .
   ```

4. **Runtime access**:
   ```python
   import os
   version = os.environ.get("AGENTRADER_VERSION", "unknown")
   ```

## Testing the Rollback System

Before relying on the rollback system in production, it's crucial to test it thoroughly:

```bash
# Run the deployment flow test
bash deployment/test_deployment_flow.sh
```

This script tests:
1. Creation of versioned deployments
2. Version passing to Docker builds
3. Rollback between versions
4. Cleanup processes

## Rollback Best Practices

1. **Always validate** the rolled-back system using the validation script
2. **Document incidents** that required rollbacks for future reference
3. **Test rollbacks regularly** as part of your operations process
4. **Keep multiple past versions** available in your image registry
5. **Practice rollbacks** with your operations team regularly

## Troubleshooting

### Common Rollback Issues

1. **Git checkout failures**:
   - Ensure you have proper permissions
   - Verify the tag or commit exists
   - Check for any local changes that might block the checkout

2. **Docker build failures**:
   - Check Docker daemon status
   - Verify Docker has sufficient disk space
   - Look for dependency changes between versions

3. **Validation failures**:
   - Check system logs for errors
   - Verify environment variables are set correctly
   - Confirm API connections are working

### Rollback Logs

Rollback operations are logged in:
- Git commit history (if a rollback commit is created)
- System logs in the `logs/` directory
- Docker logs for the containers

## Conclusion

The aGENtrader v2.2 rollback system provides a robust mechanism for returning to known-good states when issues arise. By following these procedures and best practices, your team can minimize downtime and ensure reliable operation of the trading platform.
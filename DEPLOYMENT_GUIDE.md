# aGENtrader v2.2 Deployment Guide

This guide explains how to set up and deploy the aGENtrader v2.2 system from Replit to GitHub to EC2.

## Deployment Architecture

The deployment flow follows this path:

1. Development on Replit
2. Push code to GitHub repository
3. Deploy from GitHub to EC2 instance 
4. Build and run Docker containers on EC2

## Prerequisites

- A Replit account with the aGENtrader repository
- A GitHub account with access to the aGENtrader_0.2.0 repository
- An AWS EC2 instance running Ubuntu
- SSH access to the EC2 instance

## Setting Up SSH Keys for GitHub Integration

### On Replit

1. Generate an SSH key pair within your Replit environment:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keygen -t rsa -b 4096 -C "replit@agentrader" -f ~/.ssh/id_rsa -N ""
```

2. Display the public key:

```bash
cat ~/.ssh/id_rsa.pub
```

3. Add this public key to GitHub:
   - Go to the GitHub repository settings
   - Navigate to "Deploy keys"
   - Click "Add deploy key"
   - Paste the key and give it a name like "Replit Deploy Key"
   - Check "Allow write access"
   - Click "Add key"

4. Update the Git remote URL to use SSH:

```bash
git remote set-url origin git@github.com:ProjectTradeAI/aGENtrader_0.2.0.git
```

### On EC2 Instance

1. Generate an SSH key for EC2:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keygen -t rsa -b 4096 -C "ec2@agentrader" -f ~/.ssh/id_rsa -N ""
```

2. Add the key to GitHub as another deploy key for read-only access.

3. Ensure GitHub is recognized:

```bash
ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts
```

## Deploying from Replit to GitHub

1. Make your changes in Replit
2. Commit your changes:

```bash
git add .
git commit -m "Description of changes"
```

3. Push to GitHub:

```bash
git push origin main
```

## Deploying from GitHub to EC2

### Standard Deployment

1. Ensure `aGENtrader.pem` file is in your Replit environment
2. Run the deployment script:

```bash
bash deployment/deploy_ec2.sh
```

3. When prompted, enter your EC2 instance's hostname or IP address

The script will:
- SSH into your EC2 instance
- Pull the latest code from GitHub
- Build a new Docker image with version tag
- Start the containers using docker-compose
- Validate the deployment is working correctly

### Clean Deployment (Full Wipe and Fresh Install)

For situations where you need a completely fresh deployment, use the clean deployment script:

```bash
bash deployment/clean_deploy_ec2.sh
```

This script provides a more thorough process that:

1. Removes all Docker containers, images, volumes, and networks
2. Deletes the existing aGENtrader repository folder
3. Clones a fresh copy of the repository
4. Sets up environment variables
5. Builds new Docker images
6. Starts containers with the correct version tag
7. Validates the deployment is functioning correctly

The script has several useful options:

```bash
# View help message with examples
bash deployment/clean_deploy_ec2.sh --help

# Specify host directly
bash deployment/clean_deploy_ec2.sh --host your-ec2-ip

# Specify key file
bash deployment/clean_deploy_ec2.sh --key path/to/your-key.pem

# Upload environment file (recommended)
bash deployment/clean_deploy_ec2.sh --env ./.env.production

# Skip confirmation prompt (for automation)
bash deployment/clean_deploy_ec2.sh --yes

# Complete example with all options
bash deployment/clean_deploy_ec2.sh --host ec2-12-34-56-78.compute-1.amazonaws.com --key ~/.ssh/my-key.pem --env ./.env.production --yes
```

The environment file upload feature (`--env`) is particularly useful as it securely transfers your local environment variables to the EC2 instance, ensuring all API keys and configuration are properly set up without manual intervention.

See [docs/EC2_SETUP_GUIDE.md](docs/EC2_SETUP_GUIDE.md) for detailed instructions on setting up a fresh EC2 instance if needed.

### Manual Deployment Steps

If you prefer to deploy manually, follow these steps:

1. SSH into your EC2 instance:

```bash
ssh -i aGENtrader.pem ubuntu@your-ec2-ip
```

2. Navigate to the deployment directory:

```bash
cd ~/aGENtrader
```

3. Pull the latest code:

```bash
git pull origin main
```

4. Stop existing containers:

```bash
cd docker
docker-compose down
```

5. Build and start new containers:

```bash
VERSION=$(git describe --tags --always) docker-compose build --no-cache
VERSION=$(git describe --tags --always) docker-compose up -d
```

6. Validate the deployment:

```bash
cd ..
python deployment/validate_deployment.py
```

## Environment Variables and Configuration

The aGENtrader system requires certain environment variables for API access. These must be properly configured before deployment:

### Required Environment Variables

```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
XAI_API_KEY=your_xai_key_here
```

### Setting Up Your Environment

For detailed instructions on setting up your environment, validating API keys, and troubleshooting environment issues, see the dedicated guide:

[Environment Setup Guide](docs/ENVIRONMENT_SETUP.md)

### Environment Validation

You can use the environment validation script to verify your setup:

```bash
python deployment/check_env.py
```

This will check for required variables, test API connections, and validate your `.env` file configuration.

### Best Practice for Environment Variable Management

1. **Never commit** `.env` files with actual API keys to version control
2. Use the `--env` flag with clean deployment for secure environment transfer
3. Create separate `.env` files for different environments (e.g., `.env.production`, `.env.development`)
4. Set `AGENTRADER_VERSION` environment variable for custom version tagging

## Versioning

The system uses Git tags for versioning:

1. Tag your releases:

```bash
git tag -a v0.2.0 -m "Version 0.2.0"
git push origin v0.2.0
```

2. Docker images will be built using these version tags or the commit hash if no tag is available.

## Troubleshooting

### SSH Issues

- Ensure SSH keys have correct permissions: `chmod 400 ~/.ssh/id_rsa`
- Verify GitHub is in known_hosts: `ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts`

### Docker Issues

- Check container status: `docker ps -a`
- View container logs: `docker logs aGENtrader_production`
- Ensure Docker daemon is running: `sudo systemctl status docker`

### Environment and API Issues

- Run the environment check script: `python deployment/check_env.py`
- Check API status manually:
  ```bash
  # Test Binance API connectivity
  curl -H "X-MBX-APIKEY: $BINANCE_API_KEY" https://api.binance.com/api/v3/ping
  
  # Verify .env file is correctly formatted
  grep -v '^#' .env | grep -v '^$'
  
  # Ensure .env file is being loaded
  docker-compose config | grep -i "environment"
  ```
- Common API errors:
  - `{"code": -2015, "msg": "Invalid API-key, IP, or permissions for action."}` - Your IP might be restricted, or your API key doesn't have the required permissions
  - `Connection refused` - Binance API may be blocked by your network or firewall
  - `{"code": -1022, "msg": "Signature for this request is not valid."}` - API secret is incorrect or malformed

For detailed environment setup help, refer to [Environment Setup Guide](docs/ENVIRONMENT_SETUP.md).

### Deployment Validation

If validation fails:
1. Check logs: `docker logs aGENtrader_production`
2. Verify environment variables are set correctly
3. Check connectivity to Binance API
4. Manually run validation: `python deployment/validate_deployment.py`

## Monitoring

Monitor the system with:

```bash
docker logs -f aGENtrader_production
```

View decision logs:

```bash
docker exec aGENtrader_production cat /app/logs/decision_summary.logl
```

## Rollback Procedure

### Automated Rollback

The aGENtrader system provides an automated rollback script to restore previous versions in case of deployment issues:

```bash
# Run the rollback script
bash deployment/rollback_ec2.sh [ec2-hostname-or-ip]
```

The script will:
1. Connect to the EC2 instance
2. Show available versions (Git tags) and recent commits
3. Prompt you to enter the version to roll back to (can be a Git tag, branch name, or commit hash)
4. Confirm your rollback choice
5. Check out the specified version on the EC2 instance
6. Rebuild and restart Docker containers with the old version
7. Validate the rollback deployment automatically
8. Create a local Git tag to mark this rollback event

### Manual Rollback

If you prefer to perform a manual rollback, follow these steps:

1. SSH into your EC2 instance:
   ```bash
   ssh -i aGENtrader.pem ubuntu@your-ec2-ip
   ```

2. Navigate to the deployment directory:
   ```bash
   cd ~/aGENtrader
   ```

3. List available versions:
   ```bash
   git tag -l --sort=-v:refname
   # Or list recent commits
   git log --oneline -n 10
   ```

4. Check out the desired version:
   ```bash
   git fetch --all --tags
   git checkout v0.2.0  # Or any specific tag, branch, or commit hash
   ```

5. Stop existing containers:
   ```bash
   cd docker
   docker-compose down
   ```

6. Rebuild and restart with the old version:
   ```bash
   VERSION=$(git describe --tags --always) docker-compose build --no-cache
   VERSION=$(git describe --tags --always) docker-compose up -d
   ```

7. Validate the deployment:
   ```bash
   cd ..
   python deployment/validate_deployment.py
   ```

### Best Practices for Rollbacks

1. **Always validate** the system after rollback using the validation script
2. **Document the reason** for rollback in your team's incident log
3. **Create a Git tag** to mark the rollback point for future reference
4. **Monitor the system** for at least 30 minutes after rollback
5. **Check logs** to ensure the system is operating normally

### Testing Deployment and Rollback Procedures

The aGENtrader system includes a testing script to verify that your deployment and rollback procedures are working correctly without affecting your production environment:

```bash
# Run the deployment flow test
bash deployment/test_deployment_flow.sh
```

This test script:
1. Creates temporary Git branches and tags
2. Simulates a deployment and version update
3. Tests the rollback procedure
4. Verifies that Docker images are built with correct version tags
5. Validates that all necessary versioning components are in place
6. Cleans up all temporary branches and tags when finished

Run this test before performing actual deployments to ensure your infrastructure is properly configured for versioning and rollbacks. You can also run a versioning verification check independently:

```bash
# Verify versioning components
python deployment/verify_versioning.py
```

This script checks:
1. Git repository and tag setup
2. VERSION arguments in the Dockerfile
3. Docker Compose version variable handling
4. Deployment script version handling

### Emergency Rollback

In case of critical failures where even the automated rollback script cannot be used:

1. SSH into the EC2 instance
2. Stop all containers:
   ```bash
   docker stop $(docker ps -q)
   ```
3. Find the latest working image:
   ```bash
   docker images | grep aGENtrader
   ```
4. Run the container directly:
   ```bash
   docker run -d --name aGENtrader_emergency \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/config:/app/config \
     --env-file .env \
     aGENtrader:known_working_version
   ```
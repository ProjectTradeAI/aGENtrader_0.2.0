# aGENtrader v2.2 Environment Setup Guide

This document provides a guide for setting up and configuring your environment for aGENtrader v2.2 development and deployment.

## Required Environment Variables

aGENtrader v2.2 requires the following environment variables:

| Variable | Purpose | Required? |
|----------|---------|-----------|
| `BINANCE_API_KEY` | Binance API key for market data and trading | Yes |
| `BINANCE_API_SECRET` | Binance API secret for authenticated requests | Yes |
| `XAI_API_KEY` | API key for XAI (sentiment analysis) | Yes |
| `OPENAI_API_KEY` | OpenAI API key for advanced analysis (optional) | No |
| `GITHUB_TOKEN` | GitHub access token for CI/CD operations | No |

## Setting Up Environment Variables

### Local Development Environment

1. Create a `.env` file in the root directory of the project.
2. Add your environment variables in the format:

```
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
XAI_API_KEY=your_xai_api_key
```

3. Do not commit your `.env` file to version control (it's included in `.gitignore`).

### Deploying with Environment Variables

When deploying to an EC2 instance, you have two options for setting up environment variables:

#### Option 1: Using the clean_deploy_ec2.sh script with --env flag (Recommended)

The `clean_deploy_ec2.sh` script can automatically upload your local `.env` file to the EC2 instance:

```bash
./deployment/clean_deploy_ec2.sh --host your-ec2-instance.compute.amazonaws.com --key /path/to/key.pem --env /path/to/.env
```

This is the most secure and reliable way to transfer your environment variables.

#### Option 2: Manual Configuration

If you prefer to manually configure your environment variables:

1. SSH into the EC2 instance:
   ```bash
   ssh -i /path/to/key.pem ubuntu@your-ec2-instance.compute.amazonaws.com
   ```

2. Create or edit the `.env` file in the aGENtrader directory:
   ```bash
   nano /home/ubuntu/aGENtrader/.env
   ```

3. Add your environment variables and save the file.

4. Restart the Docker containers:
   ```bash
   cd /home/ubuntu/aGENtrader/docker && docker-compose restart
   ```

## Verifying Your Environment Setup

You can verify your environment setup using the `check_env.py` script:

```bash
python deployment/check_env.py
```

This script will:

1. Check if all required environment variables are set
2. Verify that the `.env` file exists and contains the required variables
3. Test connections to external APIs (Binance and XAI)
4. Provide a summary of any issues found

## Troubleshooting

If you encounter issues with your environment setup:

1. Check if your API keys are valid and have the correct permissions.
2. Ensure your `.env` file is in the correct location and has the right format.
3. Verify that the environment variables are being loaded (they should be visible in the logs).
4. If using Docker, make sure the environment variables are correctly passed to the container.

For further assistance, refer to the troubleshooting section in the main documentation or contact the development team.
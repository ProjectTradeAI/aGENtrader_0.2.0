# EC2 Deployment from Replit

This document explains how to deploy the trading bot with local LLM capabilities from this Replit environment to your AWS EC2 instance.

## Prerequisites

1. An AWS EC2 instance running Amazon Linux 2
2. SSH key pair for connecting to your EC2 instance
3. EC2 instance with at least 4GB RAM and 2 vCPUs (recommended: t2.medium or better)
4. EC2 instance with Python 3.8+ installed

## Deployment Process

### Step 1: Create Deployment Package

First, we need to create a deployment package that can be transferred to your EC2 instance:

```bash
./create-aws-package.sh
```

This will create a file called `aws-deploy-package.tar.gz` that contains all the necessary files for deployment.

### Step 2: Download the Package

Download the `aws-deploy-package.tar.gz` file from Replit to your local machine by clicking on the file in the file explorer and then clicking the download button.

### Step 3: Generate Deployment Commands

To generate personalized deployment commands for your EC2 instance, run:

```bash
./generate-ec2-commands.sh
```

This script will provide step-by-step instructions for deploying to your specific EC2 instance.

### Step 4: Upload to EC2

From your local machine, upload the package to your EC2 instance:

```bash
scp -i /path/to/your/ec2-key.pem aws-deploy-package.tar.gz ec2-user@YOUR_EC2_IP:~/
```

Replace `/path/to/your/ec2-key.pem` with the path to your EC2 SSH key file and `YOUR_EC2_IP` with your EC2 instance's public IP address.

### Step 5: Setup on EC2

SSH into your EC2 instance:

```bash
ssh -i /path/to/your/ec2-key.pem ec2-user@YOUR_EC2_IP
```

Extract the package and run the setup script:

```bash
tar -xzf aws-deploy-package.tar.gz
cd aws-deploy-package
./setup-ec2.sh
```

The setup script will:

1. Install necessary system dependencies
2. Install Python packages and Node.js
3. Set up PM2 for process management
4. Optionally download the Llama-2-7B model
5. Configure your OpenAI API key

### Step 6: Run Your First Backtest

After setup is complete, you can run your first backtest:

```bash
./run-backtest.sh
```

## Running Backtests on EC2

To run backtests on your EC2 instance, use the `run-backtest.sh` script:

```bash
./run-backtest.sh
```

### Customizing Backtest Parameters

You can customize the backtest parameters using command-line options:

```bash
./run-backtest.sh -s BTCUSDT -i 1h -f 2025-03-01 -t 2025-03-15 -o 120 -r 0.02 -b 10000
```

Options:
- `-s SYMBOL`: Trading symbol (default: BTCUSDT)
- `-i INTERVAL`: Time interval (default: 1h)
- `-f START_DATE`: Start date (default: 2025-03-01)
- `-t END_DATE`: End date (default: 2025-03-15)
- `-o TIMEOUT`: Analysis timeout in seconds (default: 120)
- `-r RISK`: Risk per trade as decimal (default: 0.02)
- `-b BALANCE`: Initial balance (default: 10000)

## Monitoring

The backtests are run using PM2, which provides monitoring and log management. To view the logs:

```bash
pm2 logs trading-bot-backtesting
```

To view the status of running processes:

```bash
pm2 status
```

## Troubleshooting

### SSH Connection Issues

If you have trouble connecting to your EC2 instance:
- Ensure your instance is running
- Verify that your security group allows SSH (port 22) inbound traffic
- Check that your EC2 SSH key and IP address are correct

### Model Download Issues

If model download fails:
- Ensure your EC2 instance has internet connectivity
- Check that you have enough disk space (~4GB minimum for the Llama-2-7B model)
- Try manually downloading using the Hugging Face CLI

### Python Dependency Issues

If you encounter Python dependency errors:
- Manually install the dependencies: `pip3 install --user -r requirements.txt`
- For llama-cpp-python specifically: `pip3 install --user llama-cpp-python`
- Install specific dependencies as needed
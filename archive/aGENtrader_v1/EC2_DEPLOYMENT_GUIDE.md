# EC2 Deployment Guide for Trading System API

This guide explains how to deploy the Trading System API to an Amazon EC2 instance.

## Prerequisites

- An Amazon EC2 instance running Amazon Linux 2
- The trading-bot-deployer.pem private key file
- The EC2 public IP address stored in EC2_PUBLIC_IP environment variable
- Node.js and npm installed on the EC2 instance
- Python 3.6+ installed on the EC2 instance

## Deployment Process

The deployment has been set up with the following scripts:

1. `ec2_deploy_with_key.sh` - Deploys the trading system to EC2
2. `ec2_cleanup.sh` - Organizes the EC2 environment into a proper directory structure

### Files Deployed to EC2

The following files have been deployed to the `~/aGENtrader/` directory on the EC2 instance:

- **API Server Files**:
  - `test_simple_api.js` - Express server for the API
  - `start_test_server.sh` - Script to start the API server
  - `stop_test_server.sh` - Script to stop the API server
  - `run_python_sync.js` - Node.js script to run Python processes synchronously
  - `API_DOCUMENTATION.md` - API documentation

- **Python Backend Files**:
  - `api/trading_api.py` - Main API implementation
  - `orchestration/__init__.py` - Orchestration package initialization
  - `orchestration/decision_session.py` - Decision session implementation

- **Directory Structure**:
  - `api/` - API implementation files
  - `orchestration/` - Trading system orchestration files
  - `agents/` - Agent implementation files
  - `utils/` - Utility functions 
  - `scripts/` - Helper scripts
  - `data/` - Data storage (decisions, backtests, logs)

## Starting the API Server

To start the API server on the EC2 instance:

1. SSH into the EC2 instance:
   ```
   ssh -i trading-bot-deployer.pem ec2-user@<EC2_PUBLIC_IP>
   ```

2. Navigate to the aGENtrader directory:
   ```
   cd ~/aGENtrader
   ```

3. Install required npm packages (first time only):
   ```
   npm install express cors
   ```

4. Start the API server:
   ```
   ./start_test_server.sh
   ```

The API will be available at: `http://<EC2_PUBLIC_IP>:5050`

## Stopping the API Server

To stop the API server:

```
./stop_test_server.sh
```

## Updating the Deployment

To update the deployment, run the deployment script again:

```
./ec2_deploy_with_key.sh
```

This will copy the latest files to the EC2 instance.

## Troubleshooting

If you encounter any issues with the API server:

1. Check the server log:
   ```
   cat server.log
   ```

2. Organize the environment:
   ```
   ./ec2_cleanup.sh
   ```

3. Restart the server:
   ```
   ./stop_test_server.sh
   ./start_test_server.sh
   ```

4. Check python compatibility:
   ```
   python --version
   ```

5. Verify the API files are in the correct location:
   ```
   ls -la ~/aGENtrader/api/
   ls -la ~/aGENtrader/orchestration/
   ```
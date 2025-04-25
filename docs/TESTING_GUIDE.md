# aGENtrader v2.1 Testing Guide

This guide explains how to run the comprehensive test suite for aGENtrader v2.1, which validates the system's functionality including Binance API integration, TechnicalAnalystAgent with real technical indicators, and SentimentAggregatorAgent with Grok integration.

## Environment Issue with Environment Variables

If you're experiencing issues with environment variables not being found despite being in your `.env` file, this is because they need to be explicitly exported to your current shell session. The test package now includes a special wrapper script that handles this automatically.

## Installation and Testing

### Local Testing

1. **Download the test package**:
   ```bash
   # Already in your current directory
   ```

2. **Extract the test package**:
   ```bash
   mkdir -p test_local
   tar -xzf agentrader_v2.1_test_package.tar.gz -C test_local
   cd test_local
   ```

3. **Make scripts executable** (in case permissions were lost):
   ```bash
   chmod +x *.sh
   ```

4. **Run the environment-aware test wrapper**:
   ```bash
   ./run_with_env.sh
   ```
   
   This script will:
   - Check if `.env` file exists, and create one if it doesn't
   - Automatically load environment variables from the `.env` file
   - Verify that all required variables are properly set
   - Offer you a choice of which test to run

### EC2 Testing

1. **Transfer the test package to your EC2 instance**:
   ```bash
   scp -i aGENtrader.pem agentrader_v2.1_test_package.tar.gz ec2-user@YOUR_EC2_IP:~/
   ```

2. **SSH into your EC2 instance**:
   ```bash
   ssh -i aGENtrader.pem ec2-user@YOUR_EC2_IP
   ```

3. **Extract and run the tests**:
   ```bash
   mkdir -p test_v2.1
   tar -xzf agentrader_v2.1_test_package.tar.gz -C test_v2.1
   cd test_v2.1
   chmod +x *.sh
   ./run_with_env.sh
   ```

## Test Types

The test suite offers three types of tests:

1. **Full Docker Test** (Recommended):
   - Tests the entire system in Docker containers
   - Validates all API connections
   - Most representative of the production environment

2. **Direct Test**:
   - Tests components directly without Docker
   - Useful for detailed debugging
   - More verbose output for troubleshooting

3. **Mock Test**:
   - Tests the system flow with mock data
   - Useful when API access is limited or for quick validation
   - Doesn't require internet connectivity

## Troubleshooting

### Environment Variables Not Available

If you still experience issues with environment variables:

1. Check the `.env` file content:
   ```bash
   cat .env
   ```

2. Manually export variables:
   ```bash
   export BINANCE_API_KEY="your_key_here"
   export BINANCE_API_SECRET="your_secret_here"
   export XAI_API_KEY="your_xai_key_here"
   export COINAPI_KEY="your_coinapi_key_here"
   ```

3. Verify they're exported:
   ```bash
   echo $BINANCE_API_KEY
   ```

### Docker Issues

If Docker tests fail:

1. Check Docker installation:
   ```bash
   docker --version
   docker-compose --version
   ```

2. Verify Docker service is running:
   ```bash
   sudo systemctl status docker
   ```

3. Start Docker if needed:
   ```bash
   sudo systemctl start docker
   ```

### API Access Issues

If tests fail due to API access:

1. Verify API keys are correct in the `.env` file
2. Check for geolocation restrictions (especially for Binance)
3. Try using a VPN or proxy if needed
4. Consider running the Mock Test first to validate system flow

## Contact

For additional help with testing, refer to the documentation or contact the development team.
#!/bin/bash
# Test script for EC2 deployment

echo "Testing EC2 deployment script locally..."

# Create a test deployment directory
echo "Creating test deployment directory..."
mkdir -p test_deploy

# Simulate deployment package creation
echo "Creating deployment package..."
mkdir -p deploy_package

# Copy essential test files
touch test_simple_api.js
touch start_test_server.sh
touch stop_test_server.sh
touch API_DOCUMENTATION.md
mkdir -p api && touch api/test_api.py
mkdir -p orchestration && touch orchestration/test_orchestration.py
mkdir -p agents && touch agents/test_agent.py
mkdir -p utils && touch utils/test_util.py
mkdir -p scripts && touch scripts/test_script.sh
touch run_python_sync.js

# Copy files to deployment package
cp test_simple_api.js deploy_package/
cp start_test_server.sh deploy_package/
cp stop_test_server.sh deploy_package/
cp API_DOCUMENTATION.md deploy_package/
cp -r api deploy_package/
cp -r orchestration deploy_package/
cp -r agents deploy_package/
cp -r utils deploy_package/
cp -r scripts deploy_package/
cp run_python_sync.js deploy_package/
cp test_ec2_cleanup.sh deploy_package/ec2_cleanup.sh

# Create a README for EC2
cat > deploy_package/README.md << 'EOF'
# Trading System API for EC2 - Test
This is a test deployment package.
EOF

echo "Deployment package created."

# Simulate SCP by copying to test_deploy
echo "Simulating SCP by copying to test directory..."
cp -r deploy_package/* test_deploy/

# Cleanup
rm -rf deploy_package
rm test_simple_api.js start_test_server.sh stop_test_server.sh API_DOCUMENTATION.md run_python_sync.js
rm -rf api orchestration agents utils scripts

echo "Deployment simulation completed successfully!"
echo "Deployment files copied to test_deploy/"

echo -e "\nTest deployment contents:"
find test_deploy -type f | sort

echo -e "\nCleaning up..."
rm -rf test_deploy
echo "Test completed."
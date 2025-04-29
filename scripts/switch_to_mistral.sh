#!/bin/bash
# switch_to_mistral.sh
# Script to switch from Mixtral to Mistral on EC2 instances
# due to memory constraints

set -e
echo "===== aGENtrader LLM Model Switch Tool ====="
echo "This script will help you switch from Mixtral to Mistral"
echo "to accommodate EC2 instances with memory constraints."
echo ""

# Check if Ollama is installed
echo "Step 1: Checking if Ollama is installed..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "Ollama installed successfully!"
else
    echo "Ollama is already installed!"
fi

# Stop any running Ollama processes
echo "Step 2: Stopping Ollama service..."
sudo systemctl stop ollama 2>/dev/null || pkill ollama 2>/dev/null || killall ollama 2>/dev/null || echo "No running Ollama processes found."
sleep 2

# Check and remove Mixtral if present
echo "Step 3: Checking if Mixtral is installed..."
if ollama list 2>/dev/null | grep -q "mixtral"; then
    echo "Mixtral found. Removing to free up space..."
    ollama rm mixtral
    echo "Mixtral removed successfully!"
else
    echo "Mixtral not installed. Continuing..."
fi

# Clean up Ollama cache
echo "Step 4: Cleaning up Ollama cache..."
rm -rf ~/.ollama/tmp/* 2>/dev/null || echo "No cache files to clean."

# Start Ollama service
echo "Step 5: Starting Ollama service..."
(sudo systemctl start ollama 2>/dev/null || (ollama serve > /tmp/ollama.log 2>&1 &)) && echo "Ollama service started!"
sleep 3

# Pull the Mistral model
echo "Step 6: Installing Mistral model..."
ollama pull mistral
echo "Mistral installed successfully!"

# Verify installation
echo "Step 7: Verifying installation..."
ollama list

echo ""
echo "===== Testing Mistral Model ====="
echo "Hello, can you explain what makes you special as an LLM?" | ollama run mistral -c 1

echo ""
echo "===== Switch Complete ====="
echo "The system has been successfully switched to use Mistral instead of Mixtral."
echo "Memory footprint has been significantly reduced while maintaining good performance."
echo "To apply these changes to your app, update the .env file with LLM_MODEL_DEFAULT=mistral"
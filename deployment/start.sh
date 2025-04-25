#!/bin/bash
# Install required dependencies
pip install python-dotenv openai requests

# Make sure the aGENtrader_v2 directory structure exists
mkdir -p aGENtrader_v2/agents
mkdir -p aGENtrader_v2/data/feed
mkdir -p logs

# Run the application with sentiment analysis demo
python run.py --sentiment
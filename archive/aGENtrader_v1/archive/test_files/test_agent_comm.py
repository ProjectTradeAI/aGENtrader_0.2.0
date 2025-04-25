#!/usr/bin/env python3
"""Test agent communications logging"""

import os
import sys
import logging
from datetime import datetime

# Set up timestamp and log file
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_dir = os.path.join('data', 'logs')
os.makedirs(log_dir, exist_ok=True)
agent_log_file = os.path.join(log_dir, f'agent_test_{timestamp}.log')

# Configure logging
print(f'Setting up logging to: {agent_log_file}')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(agent_log_file)
    ]
)

# Create a special logger for agent communications
agent_logger = logging.getLogger('agent_comms')

# Log some test messages
print("Logging agent communications test messages...")
agent_logger.info('=== AGENT COMMUNICATIONS TEST ===')
agent_logger.info('Technical Analyst: Based on the recent price action, I see a bullish pattern forming.')
agent_logger.info('Fundamental Analyst: On-chain metrics and recent news are positive.')
agent_logger.info('Risk Manager: Given current volatility, I recommend a position size of 2% of portfolio.')
agent_logger.info('Decision Agent: After considering all inputs, I recommend a BUY with 80% confidence.')
agent_logger.info('=== TEST COMPLETED ===')

print(f'\nTest completed. Agent communications logged to: {agent_log_file}')
print('To verify, run: cat ' + agent_log_file)

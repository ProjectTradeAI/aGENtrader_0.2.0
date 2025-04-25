#!/usr/bin/env python3
"""
Simple test for paper trading system
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function"""
    print("Simple Paper Trading Test")
    print("========================")
    
    # Create data directory
    os.makedirs('data/paper_trading', exist_ok=True)
    
    # Import the paper trading system
    try:
        print("Importing paper_trading...")
        sys.path.insert(0, '.')
        from agents.paper_trading import PaperTradingSystem
        print("Successfully imported PaperTradingSystem")
        
        # Create a paper trading system with correct parameters
        print("Creating paper trading system...")
        pts = PaperTradingSystem(
            data_dir='data/paper_trading',
            default_account_id='test_account',
            initial_balance=10000.0
        )
        print("Created paper trading system")
        
        # Get the test account
        print("Getting test account...")
        account = pts.get_account('test_account')
        print(f"Test account balance: ${account.balance}")
        
    except Exception as e:
        print(f"Error with paper trading system: {e}")
        import traceback
        print(traceback.format_exc())
    
    print("Test completed")

if __name__ == '__main__':
    main()

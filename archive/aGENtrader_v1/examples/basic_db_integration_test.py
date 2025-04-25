"""
Basic Database Integration Test

This simplified script tests the database integration functions without 
running the full AutoGen conversation flow.
"""

import os
import sys
from typing import Dict, Any

# Import database query agent
try:
    from agents.database_query_agent import DatabaseQueryAgent
except ImportError:
    print("Error: Could not import DatabaseQueryAgent")
    sys.exit(1)

def test_database_functions():
    """
    Test the database query functions
    """
    print("Testing database query functions...")
    
    # Create database query agent
    try:
        agent = DatabaseQueryAgent()
        print("✓ Successfully created DatabaseQueryAgent")
    except Exception as e:
        print(f"✗ Failed to create DatabaseQueryAgent: {e}")
        return
    
    # Test functions
    try:
        # Test market data query
        symbol = "BTCUSDT"
        interval = "1h"
        limit = 5
        
        print(f"\nTesting query_market_data({symbol}, {interval}, {limit})...")
        market_data = agent.query_market_data(symbol, interval, limit=limit, format_type="json")
        print(f"✓ Successfully retrieved market data: {market_data[:200]}...")
        
        # Test market statistics
        print(f"\nTesting get_market_statistics({symbol}, {interval})...")
        stats = agent.get_market_statistics(symbol, interval, days=7, format_type="json")
        print(f"✓ Successfully retrieved market statistics: {stats[:200]}...")
        
        # Test funding rates
        print(f"\nTesting query_funding_rates({symbol})...")
        funding = agent.query_funding_rates(symbol, days=3, format_type="json")
        print(f"✓ Successfully retrieved funding rates: {funding[:200]}...")
        
        # Test exchange flows
        print(f"\nTesting query_exchange_flows({symbol})...")
        flows = agent.query_exchange_flows(symbol, days=3, format_type="json")
        print(f"✓ Successfully retrieved exchange flows: {flows[:200]}...")
        
    except Exception as e:
        print(f"✗ Error testing functions: {e}")
    finally:
        # Close the agent
        agent.close()
        print("\nClosed database connections")

if __name__ == "__main__":
    # Check for environment variables
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Run tests
    test_database_functions()
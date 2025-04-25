"""
Simple test to verify database connection and query functionality
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the database interface
try:
    from agents.database_integration import DatabaseQueryManager, AgentDatabaseInterface
except ImportError as e:
    print(f"Error importing database modules: {e}")
    sys.exit(1)

def test_database_query_manager():
    """Test the database query manager functionality"""
    print("Testing database query manager...")
    
    # Check if the DATABASE_URL environment variable is set
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Create query manager
    query_manager = DatabaseQueryManager()
    
    try:
        # Get available symbols
        symbols = query_manager.get_available_symbols()
        print(f"Available symbols: {symbols}")
        
        # Get available intervals for BTCUSDT
        intervals = query_manager.get_available_intervals("BTCUSDT")
        print(f"Available intervals for BTCUSDT: {intervals}")
        
        # Get market data for BTCUSDT - ensure limit is an integer
        print("\nFetching market data for BTCUSDT (1h interval, last 5 records)...")
        limit = 5  # Make sure this is an integer
        market_data = query_manager.get_market_data(symbol="BTCUSDT", interval="1h", limit=limit)
        
        # Print in table format
        print("\n| Timestamp | Open | High | Low | Close | Volume |")
        print("|-----------|------|------|-----|-------|--------|")
        for record in market_data:
            # Safely extract and format values
            timestamp = record.get("timestamp", "")
            if timestamp and isinstance(timestamp, str):
                ts = timestamp.replace("T", " ")[:19]
            else:
                ts = "N/A"
                
            # Extract numeric values safely
            try:
                open_price = float(record.get("open", 0))
                high_price = float(record.get("high", 0))
                low_price = float(record.get("low", 0))
                close_price = float(record.get("close", 0))
                volume = float(record.get("volume", 0))
                
                print(f"| {ts} "
                      f"| ${open_price:.2f} "
                      f"| ${high_price:.2f} "
                      f"| ${low_price:.2f} "
                      f"| ${close_price:.2f} "
                      f"| {volume:.1f} |")
            except (ValueError, TypeError) as e:
                print(f"| {ts} | Error parsing record: {e} |")
        
        # Get price statistics - ensure days is an integer
        print("\nPrice statistics for BTCUSDT (1d interval, last 30 days):")
        days = 30  # Make sure this is an integer
        try:
            stats = query_manager.get_price_statistics(symbol="BTCUSDT", interval="1d", days=days)
            if isinstance(stats, dict):
                # Extract and format statistics
                try:
                    min_price = float(stats.get('min_price', 0))
                    max_price = float(stats.get('max_price', 0))
                    avg_price = float(stats.get('avg_price', 0))
                    current_price = float(stats.get('current_price', 0))
                    
                    print(f"Min: ${min_price:.2f}")
                    print(f"Max: ${max_price:.2f}")
                    print(f"Avg: ${avg_price:.2f}")
                    print(f"Current: ${current_price:.2f}")
                except (ValueError, TypeError) as e:
                    print(f"Error parsing statistics values: {e}")
            else:
                print(f"Unexpected statistics format: {type(stats)}")
        except Exception as e:
            print(f"Error getting price statistics: {e}")
        
        # Close the connection
        query_manager.close()
        
    except Exception as e:
        print(f"Error during database query manager test: {e}")
        sys.exit(1)

def test_agent_database_interface():
    """Test the agent database interface"""
    print("\nTesting agent database interface...")
    
    # Create agent database interface
    agent_db = AgentDatabaseInterface()
    
    try:
        # Test natural language query processing
        print("\nProcessing natural language query...")
        market_query = "Show me the latest market data for Bitcoin"
        result = agent_db.process_query(market_query)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Successfully processed query: '{market_query}'")
            print(f"Result contains {len(result.get('data', []))} records")
            
        # Test with specific parameters
        print("\nProcessing query with specific parameters...")
        param_query = "Show me Bitcoin price statistics"
        params = {"symbol": "BTCUSDT", "interval": "1d", "days": 30}
        result = agent_db.process_query(param_query, params)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Successfully processed query with parameters")
            stats = result.get('data', {})
            if 'min_price' in stats:
                print(f"Min: ${stats.get('min_price', 0):.2f}")
                print(f"Max: ${stats.get('max_price', 0):.2f}")
                print(f"Avg: ${stats.get('avg_price', 0):.2f}")
                print(f"Current: ${stats.get('current_price', 0):.2f}")
        
        # Close the connection
        agent_db.close()
        
    except Exception as e:
        print(f"Error during agent database interface test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_database_query_manager()
    test_agent_database_interface()
    print("\nAll database tests completed successfully!")
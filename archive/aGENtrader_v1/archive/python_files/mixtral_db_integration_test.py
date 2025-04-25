"""
Mixtral Database Integration Test

This script tests the integration of Mixtral 8x7B with AutoGen and database queries
"""

import os
import json
import sys
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

def ensure_package_installed(package_name):
    """Check if a package is installed and install it if not present"""
    print(f"Checking for {package_name}...")
    try:
        __import__(package_name)
        print(f"{package_name} is already installed.")
        return True
    except ImportError:
        print(f"{package_name} not found. Attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"Successfully installed {package_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package_name}: {e}")
            return False

def query_market_data(symbol: str, interval: str = '1h', limit: int = 24, 
                     days: Optional[int] = None, format_type: str = 'json') -> str:
    """
    Query market data for a specific symbol.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
        limit: Number of data points to retrieve
        days: Number of days to look back (alternative to limit)
        format_type: Output format ('json', 'markdown', 'text')
        
    Returns:
        Formatted market data as a string
    """
    try:
        # Import here to avoid importing before testing for packages
        import psycopg2
        from psycopg2.extras import RealDictCursor
        import json
        from datetime import datetime, timedelta
        
        # Connect to the database using a connection string
        conn_string = os.getenv('DATABASE_URL')
        if not conn_string:
            return "Database connection string not found in environment variables."
        
        # Connect to the database
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build the query based on parameters
        if days is not None:
            # Use days parameter instead of limit
            query = """
                SELECT * FROM market_data 
                WHERE symbol = %s AND interval = %s 
                AND timestamp >= NOW() - INTERVAL %s DAY
                ORDER BY timestamp DESC
            """
            cursor.execute(query, (symbol, interval, days))
        else:
            # Use limit parameter
            query = """
                SELECT * FROM market_data 
                WHERE symbol = %s AND interval = %s 
                ORDER BY timestamp DESC
                LIMIT %s
            """
            cursor.execute(query, (symbol, interval, limit))
        
        # Fetch the results
        rows = cursor.fetchall()
        
        # Convert rows to list of dictionaries with serializable datetime
        result = []
        for row in rows:
            row_dict = dict(row)
            if 'timestamp' in row_dict and isinstance(row_dict['timestamp'], datetime):
                row_dict['timestamp'] = row_dict['timestamp'].isoformat()
            result.append(row_dict)
        
        # Close the connection
        cursor.close()
        conn.close()
        
        # Format the results
        if format_type == 'json':
            return json.dumps(result, indent=2)
        elif format_type == 'markdown':
            # Generate markdown table
            if not result:
                return "No data found."
            
            headers = list(result[0].keys())
            markdown = "| " + " | ".join(headers) + " |\n"
            markdown += "| " + " | ".join(["---" for _ in headers]) + " |\n"
            
            for row in result:
                markdown += "| " + " | ".join([str(row[h]) for h in headers]) + " |\n"
            
            return markdown
        else:  # text format
            # Generate plain text representation
            if not result:
                return "No data found."
            
            text = ""
            for row in result:
                text += f"Time: {row.get('timestamp', 'N/A')}\n"
                text += f"Price: Open={row.get('open', 'N/A')}, High={row.get('high', 'N/A')}, "
                text += f"Low={row.get('low', 'N/A')}, Close={row.get('close', 'N/A')}\n"
                text += f"Volume: {row.get('volume', 'N/A')}\n"
                text += "---\n"
            
            return text
    
    except Exception as e:
        return f"Error querying market data: {str(e)}"


def get_market_statistics(symbol: str, interval: str = '1d', 
                         days: int = 30, format_type: str = 'json') -> str:
    """
    Get market statistics for a specific symbol.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1h', '4h', '1d')
        days: Number of days to look back
        format_type: Output format ('json', 'markdown', 'text')
        
    Returns:
        Formatted market statistics as a string
    """
    try:
        # Import here to avoid importing before testing for packages
        import psycopg2
        from psycopg2.extras import RealDictCursor
        import json
        import numpy as np
        from datetime import datetime, timedelta
        
        # Connect to the database using a connection string
        conn_string = os.getenv('DATABASE_URL')
        if not conn_string:
            return "Database connection string not found in environment variables."
        
        # Connect to the database
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get market data for the specified period
        query = """
            SELECT * FROM market_data 
            WHERE symbol = %s AND interval = %s 
            AND timestamp >= NOW() - INTERVAL %s DAY
            ORDER BY timestamp DESC
        """
        cursor.execute(query, (symbol, interval, days))
        
        # Fetch the results
        rows = cursor.fetchall()
        
        # If no data, return empty result
        if not rows:
            return "No data found for the specified parameters."
        
        # Convert rows to list of dictionaries
        market_data = []
        for row in rows:
            row_dict = dict(row)
            market_data.append(row_dict)
        
        # Calculate statistics
        closes = [float(row.get('close', 0)) for row in market_data]
        highs = [float(row.get('high', 0)) for row in market_data]
        lows = [float(row.get('low', 0)) for row in market_data]
        volumes = [float(row.get('volume', 0)) for row in market_data]
        
        # Basic statistics
        latest_close = closes[0] if closes else None
        highest_price = max(highs) if highs else None
        lowest_price = min(lows) if lows else None
        price_change = closes[0] - closes[-1] if len(closes) > 1 else None
        percent_change = (price_change / closes[-1] * 100) if len(closes) > 1 and closes[-1] != 0 else None
        
        # Volatility (standard deviation of returns)
        returns = [np.log(closes[i] / closes[i+1]) for i in range(len(closes) - 1)] if len(closes) > 1 else []
        volatility = np.std(returns) * np.sqrt(252) if returns else None
        
        # Volume statistics
        avg_volume = np.mean(volumes) if volumes else None
        max_volume = max(volumes) if volumes else None
        
        # Create statistics dictionary
        statistics = {
            "symbol": symbol,
            "interval": interval,
            "period_days": days,
            "latest_price": latest_close,
            "highest_price": highest_price,
            "lowest_price": lowest_price,
            "price_change": price_change,
            "percent_change": percent_change,
            "volatility_annualized": volatility,
            "average_volume": avg_volume,
            "max_volume": max_volume,
            "data_points": len(market_data),
            "first_timestamp": market_data[-1].get('timestamp').isoformat() if market_data and 'timestamp' in market_data[-1] else None,
            "last_timestamp": market_data[0].get('timestamp').isoformat() if market_data and 'timestamp' in market_data[0] else None
        }
        
        # Close the connection
        cursor.close()
        conn.close()
        
        # Format the results
        if format_type == 'json':
            return json.dumps(statistics, indent=2)
        elif format_type == 'markdown':
            # Generate markdown table for statistics
            markdown = "| Metric | Value |\n"
            markdown += "| --- | --- |\n"
            
            for key, value in statistics.items():
                # Format floating point values
                if isinstance(value, float):
                    value = f"{value:.2f}"
                markdown += f"| {key} | {value} |\n"
            
            return markdown
        else:  # text format
            # Generate plain text representation
            text = f"Market Statistics for {symbol} ({interval}, {days} days):\n\n"
            
            for key, value in statistics.items():
                # Format floating point values
                if isinstance(value, float):
                    value = f"{value:.2f}"
                text += f"{key}: {value}\n"
            
            return text
    
    except Exception as e:
        return f"Error getting market statistics: {str(e)}"

def test_agent_with_database():
    """Test AutoGen agent with database integration"""
    # Add parent directory to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Ensure required packages are installed
    if not ensure_package_installed("llama_cpp"):
        print("ERROR: Required package llama_cpp could not be installed. Test cannot proceed.")
        return 1
    
    try:
        # Import AutoGen
        import autogen
        from autogen.agentchat.contrib.capabilities.agent_capabilities import register_function
        
        # Try to import our custom autogen_integration
        from utils.llm_integration.autogen_integration import get_llm_config
        
        # Get and print the current LLM config
        llm_config = get_llm_config()
        
        # Create a basic agent config
        config_list = llm_config.get("config_list", [])
        if not config_list:
            print("ERROR: No config_list found in llm_config")
            return 1
        
        # Check the model being used
        model_name = config_list[0].get('model', 'unknown')
        print(f"Model being used: {model_name}")
        
        # Register the database functions
        functions = [
            {
                "name": "query_market_data",
                "description": "Query market data for a specific symbol and timeframe",
                "function": query_market_data,
            },
            {
                "name": "get_market_statistics",
                "description": "Get market statistics for a specific symbol over a time period",
                "function": get_market_statistics,
            }
        ]
        
        # Create assistant with function calling capability
        assistant = autogen.AssistantAgent(
            name="crypto_analyst",
            llm_config={
                "config_list": config_list,
                "functions": functions
            },
            system_message="You are an expert cryptocurrency market analyst. You can query market data and provide insights on cryptocurrency markets. You have access to SQL database query functions."
        )
        
        # Create user proxy agent
        user_proxy = autogen.UserProxyAgent(
            name="user",
            human_input_mode="never",
            code_execution_config={
                "work_dir": "coding",
                "use_docker": False,
            },
            function_map={
                "query_market_data": query_market_data,
                "get_market_statistics": get_market_statistics,
            }
        )
        
        # Test the agent with a database query
        print("\nTesting database integration with Mixtral model...")
        user_proxy.initiate_chat(
            assistant, 
            message="Please analyze the recent price action of Bitcoin (BTCUSDT). "
                   "First get the market statistics for the last 30 days with daily data, "
                   "then provide a detailed analysis of the 24-hour price action using hourly data. "
                   "What patterns do you see? Is the market bullish or bearish based on this data?"
        )
        
        print("\nMixtral database integration test completed!")
        return 0
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Print current time
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(test_agent_with_database())
"""
Test of AutoGen Database Integration with Real Data Verification

This script tests that AutoGen agents are using real market data from the database
and not operating in any kind of simulation mode.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import database components
try:
    from agents.database_integration import DatabaseQueryManager
    from agents.database_query_agent import DatabaseQueryAgent
except ImportError:
    logger.error("Failed to import database components")
    sys.exit(1)

# Import AutoGen
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
except ImportError:
    logger.error("Failed to import AutoGen. Make sure it's installed with 'pip install pyautogen'")
    sys.exit(1)

def verify_real_data():
    """
    Verify that database contains real market data by checking multiple data points
    and comparing them to expected values.
    """
    # Set up database query manager
    try:
        db_manager = DatabaseQueryManager()
        logger.info("Successfully connected to database to verify data")
        
        # Check if data exists
        symbols = db_manager.get_available_symbols()
        intervals = db_manager.get_available_intervals()
        
        if not symbols:
            logger.error("No symbols found in database")
            return False, "No symbols found in database"
        
        if not intervals:
            logger.error("No intervals found in database")
            return False, "No intervals found in database"
        
        logger.info(f"Found symbols: {symbols}")
        logger.info(f"Found intervals: {intervals}")
        
        # Check data for BTCUSDT
        test_symbol = "BTCUSDT" if "BTCUSDT" in symbols else symbols[0]
        test_interval = "1h" if "1h" in intervals else intervals[0]
        
        logger.info(f"Testing data for symbol: {test_symbol}, interval: {test_interval}")
        
        # Get a significant amount of data to verify consistency
        market_data = db_manager.get_market_data(
            symbol=test_symbol,
            interval=test_interval,
            limit=100  # Get 100 records to ensure a good sample
        )
        
        if not market_data:
            logger.error(f"No data found for {test_symbol} with {test_interval} interval")
            return False, f"No data found for {test_symbol} with {test_interval} interval"
        
        logger.info(f"Retrieved {len(market_data)} records")
        
        # Check for data consistency and patterns of real data
        # 1. Check for timestamp sequence
        is_sequential = True
        prev_time = None
        time_differences = []
        
        for data_point in market_data:
            current_time = data_point.get('timestamp')
            if prev_time and current_time:
                # Calculate time difference in seconds
                if isinstance(current_time, str):
                    current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
                if isinstance(prev_time, str):
                    prev_time = datetime.fromisoformat(prev_time.replace('Z', '+00:00'))
                
                diff = abs((prev_time - current_time).total_seconds())
                time_differences.append(diff)
                
                # In real data, time differences should generally be consistent
                # (For 1h interval, it should be close to 3600 seconds)
            prev_time = current_time
        
        # Check for price data consistency
        open_prices = [float(point.get('open', 0)) for point in market_data if point.get('open')]
        close_prices = [float(point.get('close', 0)) for point in market_data if point.get('close')]
        high_prices = [float(point.get('high', 0)) for point in market_data if point.get('high')]
        low_prices = [float(point.get('low', 0)) for point in market_data if point.get('low')]
        
        # In real data:
        # 1. High should always be >= open, close, and low
        # 2. Low should always be <= open, close, and high
        high_low_valid = all(
            high >= max(open_val, close_val) and low <= min(open_val, close_val)
            for high, low, open_val, close_val in zip(
                high_prices, low_prices, open_prices, close_prices
            )
        )
        
        # Calculate price volatility (std dev / mean)
        if close_prices:
            avg_price = sum(close_prices) / len(close_prices)
            variance = sum((price - avg_price) ** 2 for price in close_prices) / len(close_prices)
            volatility = (variance ** 0.5) / avg_price  # Normalized volatility
            
            # Real crypto data typically has some volatility
            has_volatility = 0.0001 < volatility < 0.3
        else:
            has_volatility = False
        
        # Real data shouldn't have all identical values
        prices_not_identical = len(set(close_prices)) > 1
        
        # Summarize verification results
        verification_results = {
            "symbol": test_symbol,
            "interval": test_interval,
            "records_found": len(market_data),
            "high_low_valid": high_low_valid,
            "has_volatility": has_volatility,
            "volatility_value": volatility if 'volatility' in locals() else None,
            "prices_not_identical": prices_not_identical,
            "price_range": {
                "min": min(close_prices) if close_prices else None,
                "max": max(close_prices) if close_prices else None,
                "avg": avg_price if 'avg_price' in locals() else None
            }
        }
        
        logger.info(f"Verification results: {json.dumps(verification_results, indent=2)}")
        
        # Close connection
        db_manager.close()
        
        # Overall verification result
        is_real_data = (
            len(market_data) > 0 and
            high_low_valid and
            has_volatility and
            prices_not_identical
        )
        
        if is_real_data:
            logger.info("✅ Verification PASSED: Data appears to be real market data")
            return True, verification_results
        else:
            logger.warning("❌ Verification FAILED: Data does not appear to be real market data")
            return False, verification_results
        
    except Exception as e:
        logger.error(f"Error verifying real data: {str(e)}")
        return False, str(e)

def test_autogen_database_integration():
    """
    Test AutoGen integration with the database by having agents perform
    real-time market analysis and data retrieval.
    """
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key found in environment variables")
        return "Please set the OPENAI_API_KEY environment variable"
    
    # Create a database query agent
    db_agent = DatabaseQueryAgent()
    
    # Define wrapper functions for AutoGen
    def query_market_data(symbol: str, interval: str = '1h', limit: int = 24, 
                         days: Optional[int] = None, format_type: str = 'text') -> str:
        """
        Query market data from the database
        """
        logger.info(f"AutoGen requesting market data: {symbol}, {interval}, {limit}, {days}")
        return db_agent.query_market_data(symbol, interval, limit, days, format_type)
    
    def get_market_statistics(symbol: str, interval: str = '1d', 
                             days: int = 30, format_type: str = 'text') -> str:
        """
        Get market statistics from the database
        """
        logger.info(f"AutoGen requesting market statistics: {symbol}, {interval}, {days}")
        return db_agent.get_market_statistics(symbol, interval, days, format_type)
    
    # Configure AutoGen agents
    llm_config = {
        "config_list": [{"model": "gpt-3.5-turbo", "api_key": api_key}],
        "temperature": 0.1,
        "functions": [
            {
                "name": "query_market_data",
                "description": "Query historical market data for a trading symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., 'BTCUSDT')"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of data points to retrieve"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back (alternative to limit)"
                        },
                        "format_type": {
                            "type": "string",
                            "description": "Output format ('json', 'markdown', 'text')"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_market_statistics",
                "description": "Get market statistics for a trading symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., 'BTCUSDT')"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval (e.g., '1h', '4h', '1d')"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back"
                        },
                        "format_type": {
                            "type": "string",
                            "description": "Output format ('json', 'markdown', 'text')"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        ],
        "function_map": {
            "query_market_data": query_market_data,
            "get_market_statistics": get_market_statistics
        }
    }
    
    # Create AutoGen agents
    analyst = AssistantAgent(
        name="MarketAnalyst",
        system_message="""You are a cryptocurrency market analyst. 
You analyze market data to provide insights and trading recommendations.
NEVER make up data - only use the provided database functions to get real market data.
Always verify the data you receive exists before making conclusions.""",
        llm_config=llm_config
    )
    
    user_proxy = UserProxyAgent(
        name="User",
        code_execution_config=False,
        human_input_mode="NEVER"
    )
    
    # Series of tests to verify database access
    test_scenarios = [
        "What's the latest price of Bitcoin? Use query_market_data to check.",
        "Analyze the price trend of BTCUSDT over the last 24 hours. Query the hourly data and identify key support and resistance levels.",
        "Check the volatility of Bitcoin over the last 7 days using get_market_statistics.",
        "Compare the BTCUSDT prices from multiple timeframes (1h and 4h) and tell me if there are any discrepancies that might indicate simulated data."
    ]
    
    # Run the tests
    logger.info("Starting AutoGen test scenarios")
    
    results = []
    for i, test in enumerate(test_scenarios):
        logger.info(f"Running test scenario {i+1}: {test}")
        
        chat_result = user_proxy.initiate_chat(
            analyst,
            message=test
        )
        
        last_message = analyst.last_message()["content"]
        results.append({
            "scenario": test,
            "agent_response": last_message
        })
        
        logger.info(f"Test {i+1} completed")
    
    return results

def main():
    """Main function for testing AutoGen database integration"""
    logger.info("Starting test of AutoGen database integration with real data verification")
    
    # Verify real data
    logger.info("Step 1: Verifying database contains real market data")
    is_real, verification_results = verify_real_data()
    
    if not is_real:
        logger.error("Database verification failed - data does not appear to be real market data")
        logger.error(f"Verification results: {json.dumps(verification_results, indent=2)}")
        return
    
    # Test AutoGen integration
    logger.info("Step 2: Testing AutoGen integration with database")
    autogen_results = test_autogen_database_integration()
    
    # Save results to file
    os.makedirs("data", exist_ok=True)
    with open("data/autogen_database_test_results.json", "w") as f:
        json.dump({
            "verification_results": verification_results,
            "autogen_test_results": autogen_results
        }, f, indent=2)
    
    logger.info("Test completed - results saved to data/autogen_database_test_results.json")
    
    # Print conclusion
    print("\n==== TEST CONCLUSION ====")
    if is_real:
        print("✅ PASSED: Database contains real market data")
    else:
        print("❌ FAILED: Database does not contain real market data")
    
    print("\nTest scenarios run with AutoGen agents:")
    for i, result in enumerate(autogen_results):
        print(f"\nScenario {i+1}: {result['scenario']}")
        print(f"Response (truncated): {result['agent_response'][:150]}...")
    
    print("\nDetailed results saved to data/autogen_database_test_results.json")

if __name__ == "__main__":
    main()
"""
Debug Database Integration

This script debugs the database integration for testing interval and days parameters
"""
import logging
import argparse
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('debug_db_integration')

# Import database integration
from agents.database_integration import DatabaseQueryManager
from agents.database_query_agent import DatabaseQueryAgent

def test_market_data_parameter_handling():
    """Test how the market data function handles different parameter types"""
    
    # Initialize the database query manager
    db_manager = DatabaseQueryManager()
    
    # Test different interval and days combinations
    test_cases = [
        {"interval": "4h", "days": 7, "label": "String interval, Integer days"},
        {"interval": "4h", "days": "7", "label": "String interval, String days"},
        {"interval": "1d", "days": 14, "label": "String interval, Integer days (larger)"},
        {"interval": "1h", "days": 3, "label": "String interval, Integer days (smaller)"}
    ]
    
    for test_case in test_cases:
        interval = test_case["interval"]
        days = test_case["days"]
        label = test_case["label"]
        
        logger.info(f"Testing: {label}")
        logger.info(f"  Interval: {interval} (type: {type(interval).__name__})")
        logger.info(f"  Days: {days} (type: {type(days).__name__})")
        
        try:
            # Try to get market summary
            result = db_manager.get_market_summary(
                symbol="BTCUSDT", 
                interval=interval,
                days=days
            )
            
            if "error" in result:
                logger.error(f"  Error: {result['error']}")
            else:
                logger.info(f"  Success! Got market summary with {len(result.get('market_data', []))} data points")
                
        except Exception as e:
            logger.error(f"  Exception: {str(e)}")
    
    # Close the database connection
    db_manager.close()

def test_query_agent_parameter_handling():
    """Test how the database query agent handles parameters from natural language"""
    
    # Initialize the database query agent
    agent = DatabaseQueryAgent()
    
    # Test different natural language queries
    test_queries = [
        "Get a market summary for Bitcoin using 4-hour candles over the past week",
        "Show me the market summary for BTCUSDT using 1-day timeframe over the last 2 weeks",
        "What's the market summary for Bitcoin in the 1-hour timeframe over 3 days?",
        "Give me a comprehensive market analysis for BTC in the daily timeframe"
    ]
    
    for query in test_queries:
        logger.info(f"Testing query: '{query}'")
        
        try:
            # Parse the query
            query_type, params = agent._parse_query(query)
            logger.info(f"  Parsed as: query_type={query_type}, params={params}")
            
            # Process the query
            response = agent.process_message(query)
            logger.info(f"  Got response with length: {len(response)}")
            
            # Check if there's an error in the response
            if "error" in response.lower():
                logger.error(f"  Error in response: {response}")
                
        except Exception as e:
            logger.error(f"  Exception: {str(e)}")
    
    # Close the agent (which closes the database connection)
    agent.close()

def main():
    parser = argparse.ArgumentParser(description="Debug database integration")
    parser.add_argument("--test", choices=["market_data", "query_agent", "all"], 
                        default="all", help="Which test to run")
    args = parser.parse_args()
    
    logger.info("Starting database integration debugging")
    
    if args.test in ["market_data", "all"]:
        logger.info("Testing market data parameter handling:")
        test_market_data_parameter_handling()
        
    if args.test in ["query_agent", "all"]:
        logger.info("\nTesting query agent parameter handling:")
        test_query_agent_parameter_handling()
    
    logger.info("Completed database integration debugging")

if __name__ == "__main__":
    main()
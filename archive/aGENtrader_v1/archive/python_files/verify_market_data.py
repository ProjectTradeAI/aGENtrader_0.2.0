"""
Verify Market Data Access

A simple script to verify access to market data from the database
without the complexity of agent interactions.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("market_data_verify")

# Import database tools
from agents.database_retrieval_tool import (
    get_latest_price,
    get_recent_market_data,
    CustomJSONEncoder
)

def display_header(title: str) -> None:
    """Display a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def save_results(data: Dict[str, Any]) -> str:
    """Save results to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("data/logs/current_tests", exist_ok=True)
    output_file = f"data/logs/current_tests/market_data_verify_{timestamp}.json"
    
    with open(output_file, "w") as f:
        json.dump(data, f, cls=CustomJSONEncoder, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    return output_file

def verify_market_data():
    """Verify market data access functions"""
    display_header("Verifying Market Data Access")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    try:
        # Test get_latest_price
        display_header("Testing get_latest_price")
        symbol = "BTCUSDT"
        logger.info(f"Getting latest price for {symbol}...")
        
        latest_price_raw = get_latest_price(symbol)
        logger.info(f"Raw result type: {type(latest_price_raw)}")
        logger.info(f"Raw result: {latest_price_raw}")
        
        # Handle string response (parse JSON if needed)
        if isinstance(latest_price_raw, str):
            try:
                latest_price = json.loads(latest_price_raw)
                logger.info("Successfully parsed JSON response")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {latest_price_raw}")
                # If it's just a numeric string, use it directly
                if latest_price_raw.replace('.', '', 1).isdigit():
                    latest_price = {"close": float(latest_price_raw)}
                    logger.info(f"Interpreted as numeric value: {latest_price['close']}")
                else:
                    latest_price = {"raw_response": latest_price_raw}
        else:
            latest_price = latest_price_raw
        
        if latest_price:
            logger.info(f"Latest price data retrieved successfully:")
            
            if isinstance(latest_price, dict):
                if "symbol" in latest_price:
                    logger.info(f"Symbol: {latest_price.get('symbol')}")
                if "timestamp" in latest_price:
                    logger.info(f"Timestamp: {latest_price.get('timestamp')}")
                if "close" in latest_price:
                    logger.info(f"Close: {latest_price.get('close')}")
            
            results["tests"]["get_latest_price"] = {
                "status": "success",
                "data": latest_price
            }
        else:
            logger.error(f"Failed to get latest price for {symbol}")
            results["tests"]["get_latest_price"] = {
                "status": "error",
                "message": "Failed to retrieve data"
            }
        
        # Test get_recent_market_data
        display_header("Testing get_recent_market_data")
        limit = 5
        logger.info(f"Getting recent market data for {symbol} (limit {limit})...")
        
        recent_data_raw = get_recent_market_data(symbol, limit)
        logger.info(f"Raw result type: {type(recent_data_raw)}")
        logger.info(f"Raw result: {recent_data_raw}")
        
        # Handle string response (parse JSON if needed)
        if isinstance(recent_data_raw, str):
            try:
                recent_data = json.loads(recent_data_raw)
                logger.info("Successfully parsed JSON response")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {recent_data_raw}")
                recent_data = None
        else:
            recent_data = recent_data_raw
        
        # Special case handling: if we got a list directly instead of expected dict with "data" field
        if recent_data and isinstance(recent_data, list):
            logger.info("Response is a direct list, wrapping in standard format")
            recent_data = {"data": recent_data}
        
        if recent_data and isinstance(recent_data, dict) and "data" in recent_data and len(recent_data["data"]) > 0:
            data_count = len(recent_data["data"])
            logger.info(f"Retrieved {data_count} recent data points")
            
            # Display each data point
            for i, entry in enumerate(recent_data["data"]):
                if isinstance(entry, dict):
                    timestamp = entry.get('timestamp', 'Unknown time')
                    open_price = entry.get('open', 'N/A')
                    close_price = entry.get('close', 'N/A')
                    print(f"{i+1}. {timestamp} - Open: {open_price}, Close: {close_price}")
                else:
                    print(f"{i+1}. Raw entry: {entry}")
            
            # Calculate price changes if possible
            if data_count >= 2:
                try:
                    latest = recent_data["data"][0] if isinstance(recent_data["data"][0], dict) else {"close": None, "timestamp": "unknown"}
                    previous = recent_data["data"][1] if isinstance(recent_data["data"][1], dict) else {"close": None, "timestamp": "unknown"}
                    
                    if latest.get("close") is not None and previous.get("close") is not None:
                        price_change = latest["close"] - previous["close"]
                        percent_change = (price_change / previous["close"]) * 100
                        
                        print(f"\nPrice change analysis:")
                        print(f"Latest close ({latest.get('timestamp', 'Unknown')}): ${latest['close']}")
                        print(f"Previous close ({previous.get('timestamp', 'Unknown')}): ${previous['close']}")
                        print(f"Change: ${price_change:.2f} ({percent_change:.2f}%)")
                        print(f"Direction: {'UP' if price_change > 0 else 'DOWN' if price_change < 0 else 'UNCHANGED'}")
                    else:
                        print("\nCannot calculate price change: missing close prices")
                except (KeyError, TypeError) as e:
                    logger.error(f"Error calculating price changes: {str(e)}")
                    print("\nCannot calculate price change: data format issue")
            
            results["tests"]["get_recent_market_data"] = {
                "status": "success",
                "data_count": data_count,
                "data": recent_data
            }
        else:
            logger.error(f"Failed to get recent market data for {symbol}")
            results["tests"]["get_recent_market_data"] = {
                "status": "error",
                "message": "Failed to retrieve data or empty response",
                "raw_data": recent_data
            }
        
        # Save the results
        save_results(results)
        
        # Overall status
        all_success = all(test["status"] == "success" for test in results["tests"].values())
        results["overall_status"] = "success" if all_success else "error"
        
        display_header("Verification Complete")
        print(f"Overall status: {'✅ SUCCESS' if all_success else '❌ FAILURE'}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        results["overall_status"] = "error"
        results["error"] = str(e)
        
        # Save the results even if there was an error
        save_results(results)
        
        return results

if __name__ == "__main__":
    verify_market_data()
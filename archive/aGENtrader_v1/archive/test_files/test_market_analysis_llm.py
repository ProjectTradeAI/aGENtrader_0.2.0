"""
Test Market Analysis with Local LLM

This script tests the local LLM's ability to perform market analysis tasks
similar to what would be needed in the trading bot.
"""

import os
import sys
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_market_analysis_llm")

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_market_analyst():
    """Test the local LLM as a market analyst"""
    try:
        # Import local LLM
        from utils.llm_integration import LocalChatCompletion, clear_model
        
        # Sample market data (simplified for testing)
        market_data = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "latest_price": 63250.45,
            "24h_change_pct": 2.35,
            "24h_volume": 28450000000,
            "latest_candles": [
                {"timestamp": "2025-03-28T18:00:00", "open": 62150.75, "high": 63510.25, "low": 62100.50, "close": 63250.45, "volume": 1245000000},
                {"timestamp": "2025-03-28T17:00:00", "open": 61900.25, "high": 62300.75, "low": 61800.50, "close": 62150.75, "volume": 1150000000},
                {"timestamp": "2025-03-28T16:00:00", "open": 61750.50, "high": 62100.25, "low": 61650.75, "close": 61900.25, "volume": 980000000},
                {"timestamp": "2025-03-28T15:00:00", "open": 62050.25, "high": 62100.50, "low": 61700.25, "close": 61750.50, "volume": 1050000000},
                {"timestamp": "2025-03-28T14:00:00", "open": 62150.75, "high": 62300.50, "low": 61950.25, "close": 62050.25, "volume": 1120000000}
            ],
            "rsi_14": 58.75,
            "macd": {"macd": 125.75, "signal": 100.25, "histogram": 25.50},
            "ma_50": 60150.25,
            "ma_200": 55750.50
        }
        
        # Format data for prompt
        market_data_str = json.dumps(market_data, indent=2)
        
        # Create prompt (simplified for faster generation)
        system_message = """
        You are a Market Analyst. Analyze the provided Bitcoin data and determine
        if the trend is bullish, bearish, or neutral. Keep your answer short.
        """
        
        user_message = f"""
        BTC price: {market_data['latest_price']}, 
        24h change: {market_data['24h_change_pct']}%, 
        RSI: {market_data['rsi_14']}, 
        MACD: {market_data['macd']['histogram']}, 
        Price vs MA50: {(market_data['latest_price'] - market_data['ma_50']) / market_data['ma_50'] * 100:.2f}%
        """
        
        # Start time
        start_time = time.time()
        
        # Generate analysis
        logger.info("Generating market analysis...")
        result = LocalChatCompletion.create(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=100,
            timeout=15  # Set a 15-second timeout
        )
        
        # End time
        end_time = time.time()
        
        # Log the result
        logger.info(f"Response time: {end_time - start_time:.2f} seconds")
        logger.info(f"Analysis:\n{result['choices'][0]['message']['content']}")
        
        # Clean up
        clear_model()
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing market analysis capabilities of local LLM...")
    success = test_market_analyst()
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed. Check logs for details.")
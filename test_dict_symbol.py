#!/usr/bin/env python
"""
Test for TechnicalAnalystAgent and SentimentAnalystAgent to verify they handle dictionary symbols correctly
"""

from agents.technical_analyst_agent import TechnicalAnalystAgent
from agents.sentiment_analyst_agent import SentimentAnalystAgent

def test_technical_analyst():
    """Test the TechnicalAnalystAgent with a dictionary as the symbol parameter"""
    print("\n--- TESTING TECHNICAL ANALYST AGENT ---")
    
    # Create the agent
    agent = TechnicalAnalystAgent()
    
    # Create a dictionary similar to the one in the error message
    market_data_dict = {
        'symbol': 'BTC/USDT', 
        'interval': '4h', 
        'ohlcv': [
            {
                'timestamp': 1744790400000, 
                'open': 83363.17, 
                'high': 84127.05, 
                'low': 83140.89, 
                'close': 84048.11, 
                'volume': 2832.84259
            },
            {
                'timestamp': 1744804800000, 
                'open': 84048.36, 
                'high': 85270.27, 
                'low': 83512.2, 
                'close': 84840.0, 
                'volume': 3000.0
            }
            # More price data would be here...
        ]
    }
    
    # Test the agent with the dictionary passed as the first parameter (symbol)
    print("Testing with dictionary as symbol parameter:")
    try:
        result = agent.analyze(market_data_dict)
        # If it worked, we'll see a success message
        print(f"Success! Agent returned result with status: {result.get('status', 'unknown')}")
        print(f"Signal: {result.get('signal')}, Confidence: {result.get('confidence')}%")
    except Exception as e:
        print(f"Failed with error: {str(e)}")

    # Test with dictionary as market_data parameter
    print("\nTesting with dictionary as market_data parameter:")
    try:
        result = agent.analyze("BTC/USDT", market_data_dict)
        # If it worked, we'll see a success message
        print(f"Success! Agent returned result with status: {result.get('status', 'unknown')}")
        print(f"Signal: {result.get('signal')}, Confidence: {result.get('confidence')}%")
    except Exception as e:
        print(f"Failed with error: {str(e)}")

def test_sentiment_analyst():
    """Test the SentimentAnalystAgent with a dictionary as the symbol parameter"""
    print("\n--- TESTING SENTIMENT ANALYST AGENT ---")
    
    # Create the agent
    agent = SentimentAnalystAgent()
    
    # Create a dictionary similar to the one in the error message
    market_data_dict = {
        'symbol': 'BTC/USDT', 
        'interval': '4h', 
        'ohlcv': [
            {
                'timestamp': 1744790400000, 
                'open': 83363.17, 
                'high': 84127.05, 
                'low': 83140.89, 
                'close': 84048.11, 
                'volume': 2832.84259
            }
        ],
        'news': [
            {"title": "Bitcoin price stabilizes after recent volatility", "sentiment": 0.3},
            {"title": "Analysts predict continued bullish trend for Bitcoin", "sentiment": 0.7}
        ]
    }
    
    # Test the agent with the dictionary passed as the first parameter (symbol)
    print("Testing with dictionary as symbol parameter:")
    try:
        result = agent.analyze(market_data_dict)
        # If it worked, we'll see a success message
        print(f"Success! Agent returned result with status: {result.get('status', 'unknown')}")
        print(f"Signal: {result.get('signal')}, Confidence: {result.get('confidence')}%")
    except Exception as e:
        print(f"Failed with error: {str(e)}")

    # Test with dictionary as market_data parameter
    print("\nTesting with dictionary as market_data parameter:")
    try:
        result = agent.analyze("BTC/USDT", market_data_dict)
        # If it worked, we'll see a success message
        print(f"Success! Agent returned result with status: {result.get('status', 'unknown')}")
        print(f"Signal: {result.get('signal')}, Confidence: {result.get('confidence')}%")
    except Exception as e:
        print(f"Failed with error: {str(e)}")

def main():
    """Run all tests"""
    test_technical_analyst()
    test_sentiment_analyst()

if __name__ == "__main__":
    main()
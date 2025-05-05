#!/usr/bin/env python
"""
Test for TechnicalAnalystAgent with the exact error case from the logs
"""

from agents.technical_analyst_agent import TechnicalAnalystAgent

def main():
    """Test the exact error case from the logs"""
    # Create the agent
    agent = TechnicalAnalystAgent()
    
    # Create a dictionary exactly as shown in the error log
    market_data_dict = {'symbol': 'BTC/USDT', 'interval': '4h', 'ohlcv': [
        {'timestamp': 1744790400000, 'open': 83363.17, 'high': 84127.05, 'low': 83140.89, 'close': 84048.11, 'volume': 2832.84259},
        # Add more data points to satisfy minimum data requirements
        {'timestamp': 1744804800000, 'open': 84048.36, 'high': 85270.27, 'low': 83512.2, 'close': 84840.0, 'volume': 3000.0}
    ]}
    
    # Add more data points to meet the 30-point minimum
    for i in range(30):
        market_data_dict['ohlcv'].append({
            'timestamp': 1744804800000 + (i * 14400000),  # Add 4 hours each time
            'open': 84000 + (i * 100),
            'high': 85000 + (i * 100),
            'low': 83000 + (i * 100),
            'close': 84500 + (i * 100),
            'volume': 3000.0 + (i * 10)
        })
    
    # Test with the first input form from error log - pass the dict as the symbol parameter
    print("Testing with the exact error case from logs:")
    try:
        print("Running TechnicalAnalystAgent analysis...")
        print(f"Fetching price data for {market_data_dict}")
        result = agent.analyze(market_data_dict)
        print(f"Analysis complete! Signal: {result.get('signal')}, Confidence: {result.get('confidence')}%")
    except Exception as e:
        print(f"Error fetching price data: {str(e)}")

if __name__ == "__main__":
    main()
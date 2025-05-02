"""
Simple test script to manually test the TechnicalAnalyst agent with the new indicators module
"""
import os
import sys
import logging
import pandas as pd
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('technical_analyst_test')

# Add the current directory to sys.path if it's not already there
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

try:
    # Import the TechnicalAnalystAgent
    from agents.technical_analyst_agent import TechnicalAnalystAgent
    from binance_data_provider import BinanceDataProvider
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    sys.exit(1)

def main():
    """
    Main function to test the TechnicalAnalystAgent with the new indicators module
    """
    # Symbols to analyze
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    intervals = ["1h", "4h", "1d"]
    
    # Check for API keys
    if os.environ.get('BINANCE_API_KEY') and os.environ.get('BINANCE_API_SECRET'):
        data_provider = BinanceDataProvider(
            api_key=os.environ.get('BINANCE_API_KEY'),
            api_secret=os.environ.get('BINANCE_API_SECRET')
        )
        logger.info("Using Binance API with authentication")
    else:
        # Use Binance API without authentication
        data_provider = BinanceDataProvider()
        logger.info("Using Binance API without authentication for public data only")
    
    # Initialize the TechnicalAnalystAgent
    agent = TechnicalAnalystAgent(data_fetcher=data_provider)
    
    # Analyze each symbol at different intervals
    results = []
    
    for symbol in symbols:
        for interval in intervals:
            try:
                # Analyze the symbol
                analysis_result = agent.analyze(symbol, interval=interval)
                
                # Extract key information
                signal = analysis_result.get('signal', 'UNKNOWN')
                confidence = analysis_result.get('confidence', 0)
                
                # Get key indicators from the analysis
                indicators = analysis_result.get('indicators', {})
                
                # Print the results
                logger.info(f"Analysis for {symbol} ({interval}):")
                logger.info(f"Signal: {signal} with {confidence}% confidence")
                
                if 'explanation' in analysis_result and analysis_result['explanation']:
                    logger.info(f"Explanation: {analysis_result['explanation'][0]}")
                
                # Log key indicators
                logger.info(f"Trend: {indicators.get('trend', 'UNKNOWN')}")
                logger.info(f"Strength: {indicators.get('strength', 0)}/100")
                logger.info(f"RSI: {indicators.get('rsi', 'N/A')}")
                logger.info(f"MACD: {indicators.get('macd', 'N/A')}")
                logger.info(f"Current Price: {indicators.get('current_price', 'N/A')}")
                logger.info(f"Support: {indicators.get('support', 'N/A')}")
                logger.info(f"Resistance: {indicators.get('resistance', 'N/A')}")
                logger.info("")
                
                # Store results
                results.append({
                    "symbol": symbol,
                    "interval": interval,
                    "signal": signal,
                    "confidence": confidence,
                    "price": indicators.get('current_price'),
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol} at {interval}: {str(e)}")
    
    # Save results to a file
    try:
        with open("technical_analysis_results.json", "w") as f:
            json.dump(results, f, indent=2)
        logger.info("Results saved to technical_analysis_results.json")
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")

if __name__ == "__main__":
    main()
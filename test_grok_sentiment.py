"""
Test script for Grok sentiment analysis client

This script tests the Grok sentiment client's ability to analyze market text
and convert sentiment to trading signals.
"""
import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_grok_sentiment")
logger.info("Loaded environment variables from .env file")

# Import the sentiment client
try:
    from models.grok_sentiment_client import GrokSentimentClient
except ImportError:
    logger.error("Could not import GrokSentimentClient")
    exit(1)

def test_sentiment_analysis():
    """Test basic sentiment analysis functionality."""
    client = GrokSentimentClient()
    if not client.enabled:
        logger.warning("Grok client not enabled. Check XAI_API_KEY and OpenAI package.")
        return False
        
    # Test with positive text
    positive_text = "Bitcoin price reaches new all-time high as institutional adoption grows"
    positive_result = client.analyze_sentiment(positive_text)
    logger.info(f"Positive text analysis: {json.dumps(positive_result, indent=2)}")
    
    # Test with negative text
    negative_text = "Major crypto exchange hacked, billions lost in security breach"
    negative_result = client.analyze_sentiment(negative_text)
    logger.info(f"Negative text analysis: {json.dumps(negative_result, indent=2)}")
    
    # Test with neutral text
    neutral_text = "Regulatory authorities announce plans to review cryptocurrency guidelines"
    neutral_result = client.analyze_sentiment(neutral_text)
    logger.info(f"Neutral text analysis: {json.dumps(neutral_result, indent=2)}")
    
    return True

def test_market_news_analysis():
    """Test analysis of multiple news items."""
    client = GrokSentimentClient()
    if not client.enabled:
        logger.warning("Grok client not enabled. Check XAI_API_KEY and OpenAI package.")
        return False
        
    news_items = [
        "Bitcoin reaches $70,000 as El Salvador announces increased BTC reserves",
        "SEC approves first spot Ethereum ETF applications, setting stage for market entry",
        "Concerns grow over stablecoin regulations as lawmakers debate new framework",
        "Major DeFi protocol faces security vulnerability, funds reported safe",
        "Central banks across Asia announce CBDC pilot programs for cross-border payments"
    ]
    
    result = client.analyze_market_news(news_items)
    logger.info(f"Market news analysis: {json.dumps(result, indent=2)}")
    
    return True

def test_signal_conversion():
    """Test conversion of sentiment to trading signals."""
    client = GrokSentimentClient()
    if not client.enabled:
        logger.warning("Grok client not enabled. Check XAI_API_KEY and OpenAI package.")
        return False
        
    # Test conversion from sentiment analysis
    sentiment_result = {
        "sentiment": "positive",
        "confidence": 0.85,
        "rating": 4,
        "reasoning": "Strong positive market indicators and institutional adoption"
    }
    
    signal = client.convert_sentiment_to_signal(sentiment_result)
    logger.info(f"Converted signal: {json.dumps(signal, indent=2)}")
    
    # Test conversion from market news analysis
    news_result = {
        "overall_sentiment": "negative",
        "confidence": 0.72,
        "summary": "Regulatory concerns and security issues outweigh positive developments",
        "items": [
            {"text": "Item 1", "sentiment": "positive", "rating": 4},
            {"text": "Item 2", "sentiment": "negative", "rating": 2}
        ]
    }
    
    news_signal = client.convert_sentiment_to_signal(news_result)
    logger.info(f"Converted news signal: {json.dumps(news_signal, indent=2)}")
    
    return True

def main():
    """Main function to run all tests."""
    logger.info("Starting Grok sentiment client tests")
    
    # Check if API key is available
    if not os.environ.get("XAI_API_KEY"):
        logger.error("XAI_API_KEY not found in environment variables")
        logger.info("Please set XAI_API_KEY in your .env file")
        return
        
    # Run tests - testing one at a time to avoid timeouts
    # Uncomment each test as needed
    sentiment_test = test_sentiment_analysis()
    # news_test = test_market_news_analysis()
    signal_test = test_signal_conversion()
    
    # Simplified check
    logger.info("Tests completed. Check logs for results.")

if __name__ == "__main__":
    main()
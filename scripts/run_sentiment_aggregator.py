#!/usr/bin/env python3
"""
Sentiment Aggregator Runner

This script runs the SentimentAggregatorAgent to retrieve sentiment data from Grok API
for a specific cryptocurrency on a specific date or date range.
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")

# Import the SentimentAggregatorAgent
try:
    from aGENtrader_v2.agents.sentiment_aggregator_agent import SentimentAggregatorAgent
except ImportError:
    print("Error: Unable to import SentimentAggregatorAgent. Make sure the module exists and is accessible.")
    sys.exit(1)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run sentiment analysis for cryptocurrency markets")
    parser.add_argument("--symbol", type=str, default="BTC", 
                        help="Trading symbol (e.g., BTC, ETH)")
    parser.add_argument("--date", type=str, default=None,
                        help="Date for sentiment analysis in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--lookback", type=int, default=1,
                        help="Number of days to look back for sentiment analysis")
    parser.add_argument("--detailed", action="store_true",
                        help="Include detailed sentiment breakdown")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file path for saving results (JSON format)")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose output")
    return parser.parse_args()

def print_sentiment_analysis(result: Dict[str, Any], verbose: bool = False):
    """
    Print sentiment analysis results in a readable format
    
    Args:
        result: Analysis results dictionary
        verbose: Whether to print detailed output
    """
    if result.get("status") == "error":
        print("⚠️ Error in sentiment analysis:")
        print(f"  Type: {result['error']['type']}")
        print(f"  Message: {result['error']['message']}")
        return
    
    print(f"📊 Sentiment Analysis for {result['asset']}:")
    print(f"  Period: {result['period']}")
    
    # Calculate sentiment tier
    sentiment = result["overall_sentiment"]
    if sentiment >= 70:
        sentiment_tier = "Extremely Bullish"
    elif sentiment >= 30:
        sentiment_tier = "Bullish"
    elif sentiment >= 10:
        sentiment_tier = "Slightly Bullish"
    elif sentiment >= -10:
        sentiment_tier = "Neutral"
    elif sentiment >= -30:
        sentiment_tier = "Slightly Bearish"  
    elif sentiment >= -70:
        sentiment_tier = "Bearish"
    else:
        sentiment_tier = "Extremely Bearish"
    
    print(f"  Overall Sentiment: {sentiment} ({sentiment_tier})")
    print(f"  Confidence: {result['confidence']}%")
    
    if verbose and "sentiment_breakdown" in result:
        print("\n📰 Sentiment Breakdown:")
        for source, score in result["sentiment_breakdown"].items():
            print(f"  {source.capitalize()}: {score}")
    
    if verbose and "key_events" in result:
        print("\n🔑 Key Events:")
        for event in result["key_events"]:
            print(f"  • {event}")
    
    if verbose and "sources" in result:
        print("\n📚 Data Sources:")
        for source in result["sources"]:
            print(f"  • {source}")

def save_results(result: Any, output_path: Optional[str] = None) -> str:
    """
    Save analysis results to a file
    
    Args:
        result: Analysis results (dictionary or list)
        output_path: Output file path (optional)
        
    Returns:
        Path to the saved file
    """
    # Generate default output path if not provided
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = result.get("asset", "unknown") if isinstance(result, dict) else "combined"
        output_path = f"sentiment_analysis_{symbol}_{timestamp}.json"
    
    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save results to file
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    return output_path

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Check for API key
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("⚠️ Warning: XAI_API_KEY environment variable not found.")
        print("Sentiment analysis may not work properly without a valid API key.")
    
    # Create SentimentAggregatorAgent
    sentiment_agent = SentimentAggregatorAgent(api_key=api_key)
    
    # Run sentiment analysis
    print(f"Running sentiment analysis for {args.symbol}...")
    result = sentiment_agent.analyze_sentiment(
        symbol=args.symbol,
        date=args.date,
        lookback_days=args.lookback,
        detailed=args.detailed or args.verbose
    )
    
    # Print results
    print_sentiment_analysis(result, verbose=args.verbose)
    
    # Save results if requested
    if args.output or args.verbose:
        output_path = save_results(result, args.output)
        print(f"\nResults saved to: {output_path}")

if __name__ == "__main__":
    main()
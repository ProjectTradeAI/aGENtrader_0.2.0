"""
Sentiment Analysis Runner

This script runs the SentimentAnalystAgent with real market data from CoinAPI
and demonstrates how to use external sentiment APIs when they are available.
"""

import os
import sys
import json
from datetime import datetime
import argparse
from typing import Dict, Any, Optional

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import required modules
from aGENtrader_v2.agents.sentiment_analyst_agent import SentimentAnalystAgent
from aGENtrader_v2.utils.config import get_config
from aGENtrader_v2.utils.logger import get_logger

logger = get_logger("sentiment_runner")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run Sentiment Analysis with SentimentAnalystAgent")
    
    parser.add_argument("--symbol", type=str, default="BTCUSDT", 
                        help="Trading symbol to analyze (default: BTCUSDT)")
    
    parser.add_argument("--interval", type=str, default="1h", 
                        help="Time interval for analysis (default: 1h)")
    
    parser.add_argument("--mode", type=str, default="mock", 
                        choices=["mock", "api", "scrape"],
                        help="Sentiment data mode to use (default: mock)")
    
    parser.add_argument("--output", type=str, default=None,
                        help="Output file path for results (default: None)")
    
    parser.add_argument("--verbose", action="store_true", 
                        help="Print detailed output")
    
    return parser.parse_args()

def update_config_for_mode(mode: str):
    """
    Update the configuration to use the specified sentiment mode
    
    Args:
        mode: Sentiment data mode to use (mock, api, scrape)
    """
    # Get config manager instance
    config = get_config()
    
    # Update sentiment_analyst settings
    agent_config = config.get_section("agents")
    if "sentiment_analyst" not in agent_config:
        agent_config["sentiment_analyst"] = {}
    
    agent_config["sentiment_analyst"]["data_mode"] = mode
    
    # Save updated configuration using the set method
    config.set("agents.sentiment_analyst.data_mode", mode)
    
    logger.info(f"Updated configuration to use sentiment data mode: {mode}")

def print_sentiment_analysis(result: Dict[str, Any], verbose: bool = False):
    """
    Print sentiment analysis results in a readable format
    
    Args:
        result: Analysis results dictionary
        verbose: Whether to print detailed output
    """
    # Extract primary results
    sentiment = result["analysis"]["sentiment"]
    action = result["analysis"]["action"]
    confidence = result["analysis"]["confidence"]
    reason = result["analysis"]["reason"]
    
    # Print formatted results
    print("\n===== SENTIMENT ANALYSIS RESULTS =====")
    print(f"Symbol: {result.get('symbol')}")
    print(f"Timestamp: {result.get('timestamp')}")
    print(f"Sentiment Source: {result.get('sentiment_source')}")
    print(f"Sentiment: {sentiment}")
    print(f"Action: {action}")
    print(f"Confidence: {confidence}")
    print(f"Reason: {reason}")
    
    # Print insights if available
    insights = result["analysis"].get("insights", [])
    if insights:
        print("\nInsights:")
        for insight in insights:
            print(f"- {insight}")
    
    # Print additional details if verbose mode is enabled
    if verbose:
        print("\nRaw Sentiment Data:")
        sentiment_data = result.get("sentiment_data", {})
        for key, value in sentiment_data.items():
            if key != "sources":  # Skip sources for now
                print(f"{key}: {value}")
        
        # Print source data if available
        sources = sentiment_data.get("sources", {})
        if sources:
            print("\nSentiment Sources:")
            for source_name, source_data in sources.items():
                print(f"\n{source_name.upper()}:")
                for key, value in source_data.items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for k, v in value.items():
                            print(f"    {k}: {v}")
                    else:
                        print(f"  {key}: {value}")

def save_results(result: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save analysis results to a file
    
    Args:
        result: Analysis results dictionary
        output_path: Output file path (optional)
        
    Returns:
        Path to the saved file
    """
    # Create default filepath if not provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = result.get("symbol", "unknown")
        output_path = os.path.join(script_dir, f"logs/sentiment/{symbol}_{timestamp}.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save results
    try:
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return ""

def main():
    """Main function"""
    args = parse_arguments()
    
    # Update configuration for the selected mode
    update_config_for_mode(args.mode)
    
    # Initialize the SentimentAnalystAgent
    agent = SentimentAnalystAgent()
    
    # Run sentiment analysis
    result = agent.analyze(args.symbol, args.interval)
    
    # Print results
    print_sentiment_analysis(result, args.verbose)
    
    # Save results if output path is specified
    if args.output:
        output_path = save_results(result, args.output)
        if output_path:
            print(f"\nResults saved to: {output_path}")
    
    # Get sentiment trend
    trend = agent.get_sentiment_trend(args.symbol)
    print(f"\nSentiment Trend: {trend['trend']} (Confidence: {trend['confidence']:.1f}%)")
    print(f"Data Points: {trend['data_points']} (Bullish: {trend['bullish_count']}, Bearish: {trend['bearish_count']}, Neutral: {trend['neutral_count']})")

if __name__ == "__main__":
    main()
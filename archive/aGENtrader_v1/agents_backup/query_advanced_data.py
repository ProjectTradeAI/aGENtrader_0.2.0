"""
AutoGen Advanced Data Query Functions

This module provides functions for querying advanced market data including:
- On-chain metrics
- Social sentiment
- Fear & Greed Index
- Whale transactions

These functions are designed to be used with AutoGen agents.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import integrated provider
try:
    from utils.integrated_advanced_data import get_provider as get_advanced_data_provider
    PROVIDER_AVAILABLE = True
except ImportError as e:
    logger.error(f"Error importing advanced data provider: {str(e)}")
    PROVIDER_AVAILABLE = False

# Attempt to get the Santiment API key from environment
SANTIMENT_API_KEY = os.environ.get("SANTIMENT_API_KEY")

# Initialize the provider
_provider = None

def _get_provider():
    """
    Get or initialize the advanced data provider
    
    Returns:
        Provider instance
    """
    global _provider
    
    if _provider is None and PROVIDER_AVAILABLE:
        try:
            _provider = get_advanced_data_provider(SANTIMENT_API_KEY)
            logger.info("Advanced data provider initialized")
        except Exception as e:
            logger.error(f"Error initializing advanced data provider: {str(e)}")
    
    return _provider

def _format_output(data: Dict[str, Any], format_type: str) -> str:
    """
    Format data for output
    
    Args:
        data: Data to format
        format_type: Output format (json, markdown, text)
        
    Returns:
        Formatted data as string
    """
    if format_type == "json":
        return json.dumps(data, indent=2)
    
    # Extract some information for easier access
    timestamp = data.get("timestamp", datetime.utcnow().isoformat())
    source = data.get("data_source", data.get("source", "unknown"))
    symbol = data.get("symbol", "")
    
    # Check for error
    if "error" in data:
        error_message = f"Error: {data['error']}"
        if format_type == "markdown":
            return f"### Error Retrieving Data\n\n{error_message}"
        else:  # text
            return error_message
    
    # Check if we have data
    if not data.get("data"):
        no_data_message = "No data available"
        if format_type == "markdown":
            return f"### No Data Available\n\n{no_data_message}"
        else:  # text
            return no_data_message
    
    # For Markdown format
    if format_type == "markdown":
        result = []
        
        # Add header
        if symbol:
            result.append(f"### Advanced Data: {symbol}")
        else:
            result.append(f"### Advanced Market Data")
        
        # Add metadata
        result.append(f"Data retrieved at {timestamp}")
        result.append(f"Source: {source}")
        result.append("")
        
        # Check data type and format accordingly
        data_items = data.get("data", [])
        
        if not data_items:
            result.append("No data points available")
        elif "value_classification" in data_items[0]:
            # Fear & Greed Index data
            result.append("| Date | Value | Classification |")
            result.append("|------|-------|---------------|")
            
            for item in data_items:
                date_str = item.get("date", "")
                value = item.get("value", "")
                classification = item.get("value_classification", "")
                result.append(f"| {date_str} | {value} | {classification} |")
        else:
            # On-chain or sentiment data
            # Get all possible keys from the data
            all_keys = set()
            for item in data_items:
                all_keys.update(item.keys())
            
            # Remove the datetime key as we'll display it separately
            if "datetime" in all_keys:
                all_keys.remove("datetime")
            
            # Sort the keys
            sorted_keys = sorted(all_keys)
            
            # Create the header
            header = "| Datetime |"
            for key in sorted_keys:
                formatted_key = key.replace("_", " ").title()
                header += f" {formatted_key} |"
            result.append(header)
            
            # Create the separator
            separator = "|---------|"
            for _ in sorted_keys:
                separator += "---------|"
            result.append(separator)
            
            # Add each data row
            for item in data_items:
                dt = item.get("datetime", "")
                row = f"| {dt} |"
                
                for key in sorted_keys:
                    value = item.get(key, "")
                    if isinstance(value, float):
                        row += f" {value:.4f} |"
                    else:
                        row += f" {value} |"
                
                result.append(row)
        
        return "\n".join(result)
    
    # For text format
    else:  # text
        result = []
        
        # Add header
        if symbol:
            result.append(f"Advanced Data: {symbol}")
        else:
            result.append(f"Advanced Market Data")
        
        result.append(f"Data retrieved at {timestamp}")
        result.append(f"Source: {source}")
        result.append("")
        
        # Check data type and format accordingly
        data_items = data.get("data", [])
        
        if not data_items:
            result.append("No data points available")
        elif "value_classification" in data_items[0]:
            # Fear & Greed Index data
            result.append("Date            Value  Classification")
            result.append("------------------------------------")
            
            for item in data_items:
                date_str = item.get("date", "").ljust(15)
                value = str(item.get("value", "")).ljust(6)
                classification = item.get("value_classification", "")
                result.append(f"{date_str} {value} {classification}")
        else:
            # On-chain or sentiment data
            for i, item in enumerate(data_items):
                if i > 0:
                    result.append("---")
                
                dt = item.get("datetime", "")
                result.append(f"Datetime: {dt}")
                
                for key, value in sorted(item.items()):
                    if key != "datetime":
                        formatted_key = key.replace("_", " ").title()
                        if isinstance(value, float):
                            result.append(f"{formatted_key}: {value:.4f}")
                        else:
                            result.append(f"{formatted_key}: {value}")
        
        return "\n".join(result)

def query_on_chain_metrics(symbol: str, days: int = 7, format_type: str = "json") -> str:
    """
    Query on-chain metrics for a cryptocurrency
    
    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
        days: Number of days of historical data to retrieve
        format_type: Output format (json, markdown, text)
        
    Returns:
        Formatted on-chain metrics as a string
    """
    provider = _get_provider()
    
    if not provider:
        error_msg = {
            "error": "Advanced data provider not available",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)
    
    try:
        # Get on-chain metrics
        data = provider.get_on_chain_metrics(symbol, days)
        
        # Format and return the result
        return _format_output(data, format_type)
    except Exception as e:
        logger.error(f"Error querying on-chain metrics: {str(e)}")
        error_msg = {
            "error": f"Error querying on-chain metrics: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)

def query_social_sentiment(symbol: str, days: int = 7, format_type: str = "json") -> str:
    """
    Query social sentiment data for a cryptocurrency
    
    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
        days: Number of days of historical data to retrieve
        format_type: Output format (json, markdown, text)
        
    Returns:
        Formatted social sentiment data as a string
    """
    provider = _get_provider()
    
    if not provider:
        error_msg = {
            "error": "Advanced data provider not available",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)
    
    try:
        # Get social sentiment
        data = provider.get_social_sentiment(symbol, days)
        
        # Format and return the result
        return _format_output(data, format_type)
    except Exception as e:
        logger.error(f"Error querying social sentiment: {str(e)}")
        error_msg = {
            "error": f"Error querying social sentiment: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)

def query_fear_greed_index(days: int = 7, format_type: str = "json") -> str:
    """
    Query the Fear & Greed Index
    
    Args:
        days: Number of days of historical data to retrieve
        format_type: Output format (json, markdown, text)
        
    Returns:
        Formatted Fear & Greed Index data as a string
    """
    provider = _get_provider()
    
    if not provider:
        error_msg = {
            "error": "Advanced data provider not available",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)
    
    try:
        # Get Fear & Greed Index
        data = provider.get_fear_greed_index(days)
        
        # Format and return the result
        return _format_output(data, format_type)
    except Exception as e:
        logger.error(f"Error querying Fear & Greed Index: {str(e)}")
        error_msg = {
            "error": f"Error querying Fear & Greed Index: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)

def query_whale_transactions(symbol: str, days: int = 7, format_type: str = "json") -> str:
    """
    Query whale transaction data for a cryptocurrency
    
    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
        days: Number of days of historical data to retrieve
        format_type: Output format (json, markdown, text)
        
    Returns:
        Formatted whale transaction data as a string
    """
    provider = _get_provider()
    
    if not provider:
        error_msg = {
            "error": "Advanced data provider not available",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)
    
    try:
        # Get whale transactions
        data = provider.get_whale_transactions(symbol, days)
        
        # Format and return the result
        return _format_output(data, format_type)
    except Exception as e:
        logger.error(f"Error querying whale transactions: {str(e)}")
        error_msg = {
            "error": f"Error querying whale transactions: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)

def get_fundamental_analysis(symbol: str, days: int = 7, format_type: str = "json") -> str:
    """
    Get a comprehensive fundamental analysis for a cryptocurrency,
    combining on-chain metrics and whale transactions.
    
    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
        days: Number of days of historical data to analyze
        format_type: Output format (json, markdown, text)
        
    Returns:
        Formatted fundamental analysis as a string
    """
    provider = _get_provider()
    
    if not provider:
        error_msg = {
            "error": "Advanced data provider not available",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)
    
    try:
        # Get on-chain metrics
        on_chain_data = provider.get_on_chain_metrics(symbol, days)
        
        # Get whale transactions
        whale_data = provider.get_whale_transactions(symbol, days)
        
        # Combine the data
        combined_data = {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "on_chain_metrics": on_chain_data.get("data", []),
            "whale_transactions": whale_data.get("data", []),
            "data_sources": {
                "on_chain": on_chain_data.get("data_source", "unknown"),
                "whale": whale_data.get("data_source", "unknown")
            }
        }
        
        # Add analysis summary (if we have data)
        if combined_data["on_chain_metrics"] or combined_data["whale_transactions"]:
            combined_data["analysis"] = _generate_fundamental_analysis(combined_data)
        
        # Format and return the result
        if format_type == "json":
            return json.dumps(combined_data, indent=2)
        
        # For text or markdown, create a more readable format
        if format_type == "markdown":
            result = [
                f"# Fundamental Analysis: {symbol}",
                f"Analysis performed at {combined_data['timestamp']}",
                "",
                "## Analysis Summary",
                ""
            ]
            
            if "analysis" in combined_data:
                for point in combined_data["analysis"]:
                    result.append(f"- {point}")
            else:
                result.append("*No analysis available due to insufficient data*")
            
            # Add data source information
            result.extend([
                "",
                "## Data Sources",
                f"- On-chain metrics: {combined_data['data_sources']['on_chain']}",
                f"- Whale transactions: {combined_data['data_sources']['whale']}",
                ""
            ])
            
            return "\n".join(result)
        else:  # text
            result = [
                f"FUNDAMENTAL ANALYSIS: {symbol}",
                f"Analysis performed at {combined_data['timestamp']}",
                "",
                "ANALYSIS SUMMARY:",
                ""
            ]
            
            if "analysis" in combined_data:
                for point in combined_data["analysis"]:
                    result.append(f"- {point}")
            else:
                result.append("No analysis available due to insufficient data")
            
            # Add data source information
            result.extend([
                "",
                "DATA SOURCES:",
                f"- On-chain metrics: {combined_data['data_sources']['on_chain']}",
                f"- Whale transactions: {combined_data['data_sources']['whale']}",
                ""
            ])
            
            return "\n".join(result)
    except Exception as e:
        logger.error(f"Error generating fundamental analysis: {str(e)}")
        error_msg = {
            "error": f"Error generating fundamental analysis: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)

def _generate_fundamental_analysis(data: Dict[str, Any]) -> List[str]:
    """
    Generate a fundamental analysis from the data
    
    Args:
        data: Combined data dictionary
        
    Returns:
        List of analysis points
    """
    analysis_points = []
    
    # Get the latest data points
    on_chain_latest = data["on_chain_metrics"][-1] if data["on_chain_metrics"] else None
    whale_latest = data["whale_transactions"][-1] if data["whale_transactions"] else None
    
    # Check on-chain metrics
    if on_chain_latest:
        # Daily active addresses
        if "daily_active_addresses" in on_chain_latest:
            addresses = on_chain_latest["daily_active_addresses"]
            if addresses > 1000000:
                analysis_points.append(f"Very high network activity with {addresses:,} daily active addresses")
            elif addresses > 500000:
                analysis_points.append(f"Strong network activity with {addresses:,} daily active addresses")
            elif addresses > 100000:
                analysis_points.append(f"Moderate network activity with {addresses:,} daily active addresses")
        
        # Network growth
        if "network_growth" in on_chain_latest:
            growth = on_chain_latest["network_growth"]
            if growth > 10000:
                analysis_points.append(f"Strong network growth with {growth:,} new addresses")
            elif growth > 5000:
                analysis_points.append(f"Moderate network growth with {growth:,} new addresses")
        
        # Developer activity
        if "dev_activity" in on_chain_latest:
            dev_activity = on_chain_latest["dev_activity"]
            if dev_activity > 100:
                analysis_points.append(f"Very high developer activity ({dev_activity:.2f})")
            elif dev_activity > 50:
                analysis_points.append(f"Strong developer activity ({dev_activity:.2f})")
            elif dev_activity > 20:
                analysis_points.append(f"Moderate developer activity ({dev_activity:.2f})")
        
        # Exchange funds flow
        if "exchange_funds_flow" in on_chain_latest:
            flow = on_chain_latest["exchange_funds_flow"]
            if flow < -1000000:
                analysis_points.append(f"Large outflow from exchanges (${abs(flow):,.2f}), indicating accumulation")
            elif flow < -100000:
                analysis_points.append(f"Moderate outflow from exchanges (${abs(flow):,.2f})")
            elif flow > 1000000:
                analysis_points.append(f"Large inflow to exchanges (${flow:,.2f}), indicating potential selling pressure")
            elif flow > 100000:
                analysis_points.append(f"Moderate inflow to exchanges (${flow:,.2f})")
    
    # Check whale transactions
    if whale_latest:
        # Large transactions
        if "large_transactions" in whale_latest:
            large_tx = whale_latest["large_transactions"]
            if large_tx > 1000:
                analysis_points.append(f"Very high whale activity with {large_tx:,} large transactions")
            elif large_tx > 500:
                analysis_points.append(f"Significant whale activity with {large_tx:,} large transactions")
            elif large_tx > 100:
                analysis_points.append(f"Moderate whale activity with {large_tx:,} large transactions")
        
        # Top holders percentage
        if "top_holders_percent" in whale_latest:
            top_holders = whale_latest["top_holders_percent"]
            if top_holders > 80:
                analysis_points.append(f"Very high concentration with top holders controlling {top_holders:.2f}% of supply")
            elif top_holders > 60:
                analysis_points.append(f"High concentration with top holders controlling {top_holders:.2f}% of supply")
            elif top_holders < 40:
                analysis_points.append(f"Good distribution with top holders controlling only {top_holders:.2f}% of supply")
    
    # If we couldn't generate any analysis points, add a generic one
    if not analysis_points:
        analysis_points.append("Insufficient on-chain data available for detailed analysis")
    
    return analysis_points

def get_sentiment_analysis(symbol: str, days: int = 7, format_type: str = "json") -> str:
    """
    Get a comprehensive sentiment analysis for a cryptocurrency,
    combining social sentiment and the Fear & Greed Index.
    
    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
        days: Number of days of historical data to analyze
        format_type: Output format (json, markdown, text)
        
    Returns:
        Formatted sentiment analysis as a string
    """
    provider = _get_provider()
    
    if not provider:
        error_msg = {
            "error": "Advanced data provider not available",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)
    
    try:
        # Get social sentiment
        sentiment_data = provider.get_social_sentiment(symbol, days)
        
        # Get Fear & Greed Index
        fear_greed_data = provider.get_fear_greed_index(days)
        
        # Combine the data
        combined_data = {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "social_sentiment": sentiment_data.get("data", []),
            "fear_greed_index": fear_greed_data.get("data", []),
            "data_sources": {
                "sentiment": sentiment_data.get("data_source", "unknown"),
                "fear_greed": fear_greed_data.get("data_source", "unknown")
            }
        }
        
        # Add analysis summary (if we have data)
        if combined_data["social_sentiment"] or combined_data["fear_greed_index"]:
            combined_data["analysis"] = _generate_sentiment_analysis(combined_data)
        
        # Format and return the result
        if format_type == "json":
            return json.dumps(combined_data, indent=2)
        
        # For text or markdown, create a more readable format
        if format_type == "markdown":
            result = [
                f"# Sentiment Analysis: {symbol}",
                f"Analysis performed at {combined_data['timestamp']}",
                "",
                "## Analysis Summary",
                ""
            ]
            
            if "analysis" in combined_data:
                for point in combined_data["analysis"]:
                    result.append(f"- {point}")
            else:
                result.append("*No analysis available due to insufficient data*")
            
            # Add data source information
            result.extend([
                "",
                "## Data Sources",
                f"- Social sentiment: {combined_data['data_sources']['sentiment']}",
                f"- Fear & Greed Index: {combined_data['data_sources']['fear_greed']}",
                ""
            ])
            
            return "\n".join(result)
        else:  # text
            result = [
                f"SENTIMENT ANALYSIS: {symbol}",
                f"Analysis performed at {combined_data['timestamp']}",
                "",
                "ANALYSIS SUMMARY:",
                ""
            ]
            
            if "analysis" in combined_data:
                for point in combined_data["analysis"]:
                    result.append(f"- {point}")
            else:
                result.append("No analysis available due to insufficient data")
            
            # Add data source information
            result.extend([
                "",
                "DATA SOURCES:",
                f"- Social sentiment: {combined_data['data_sources']['sentiment']}",
                f"- Fear & Greed Index: {combined_data['data_sources']['fear_greed']}",
                ""
            ])
            
            return "\n".join(result)
    except Exception as e:
        logger.error(f"Error generating sentiment analysis: {str(e)}")
        error_msg = {
            "error": f"Error generating sentiment analysis: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
        return _format_output(error_msg, format_type)

def _generate_sentiment_analysis(data: Dict[str, Any]) -> List[str]:
    """
    Generate a sentiment analysis from the data
    
    Args:
        data: Combined data dictionary
        
    Returns:
        List of analysis points
    """
    analysis_points = []
    
    # Get the latest data points
    sentiment_latest = data["social_sentiment"][-1] if data["social_sentiment"] else None
    
    # Get the most recent Fear & Greed Index
    fear_greed_latest = data["fear_greed_index"][-1] if data["fear_greed_index"] else None
    
    # Check social sentiment
    if sentiment_latest:
        # Overall sentiment score
        if "sentiment" in sentiment_latest:
            sentiment = sentiment_latest["sentiment"]
            if sentiment > 0.5:
                analysis_points.append(f"Very positive social sentiment ({sentiment:.2f})")
            elif sentiment > 0.2:
                analysis_points.append(f"Positive social sentiment ({sentiment:.2f})")
            elif sentiment < -0.5:
                analysis_points.append(f"Very negative social sentiment ({sentiment:.2f})")
            elif sentiment < -0.2:
                analysis_points.append(f"Negative social sentiment ({sentiment:.2f})")
            else:
                analysis_points.append(f"Neutral social sentiment ({sentiment:.2f})")
        
        # Social volume
        if "social_volume" in sentiment_latest:
            volume = sentiment_latest["social_volume"]
            if volume > 10000:
                analysis_points.append(f"Very high social volume with {volume:,} mentions")
            elif volume > 5000:
                analysis_points.append(f"High social volume with {volume:,} mentions")
            elif volume > 1000:
                analysis_points.append(f"Moderate social volume with {volume:,} mentions")
        
        # Bullish/bearish percentages
        if all(k in sentiment_latest for k in ["bullish_percentage", "bearish_percentage"]):
            bullish = sentiment_latest["bullish_percentage"]
            bearish = sentiment_latest["bearish_percentage"]
            
            if bullish > 70:
                analysis_points.append(f"Overwhelmingly bullish sentiment ({bullish:.1f}% bullish vs {bearish:.1f}% bearish)")
            elif bullish > 60:
                analysis_points.append(f"Strongly bullish sentiment ({bullish:.1f}% bullish vs {bearish:.1f}% bearish)")
            elif bearish > 70:
                analysis_points.append(f"Overwhelmingly bearish sentiment ({bearish:.1f}% bearish vs {bullish:.1f}% bullish)")
            elif bearish > 60:
                analysis_points.append(f"Strongly bearish sentiment ({bearish:.1f}% bearish vs {bullish:.1f}% bullish)")
    
    # Check Fear & Greed Index
    if fear_greed_latest:
        value = fear_greed_latest["value"]
        classification = fear_greed_latest["value_classification"]
        
        # Add Fear & Greed analysis
        if classification == "Extreme Fear":
            analysis_points.append(f"Market in Extreme Fear (Fear & Greed Index: {value}) - historically a buying opportunity")
        elif classification == "Fear":
            analysis_points.append(f"Market in Fear (Fear & Greed Index: {value}) - cautious sentiment prevails")
        elif classification == "Greed":
            analysis_points.append(f"Market in Greed (Fear & Greed Index: {value}) - optimistic sentiment")
        elif classification == "Extreme Greed":
            analysis_points.append(f"Market in Extreme Greed (Fear & Greed Index: {value}) - potential sign of market top")
        else:
            analysis_points.append(f"Market sentiment neutral (Fear & Greed Index: {value})")
    
    # If we couldn't generate any analysis points, add a generic one
    if not analysis_points:
        analysis_points.append("Insufficient sentiment data available for detailed analysis")
    
    return analysis_points

def test_query_functions():
    """Test the query functions"""
    print("Testing Advanced Data Query Functions")
    print("===================================")
    
    # Set up test parameters
    symbol = "BTC"
    days = 7
    
    # Test on-chain metrics
    print("\n1. ON-CHAIN METRICS")
    print(query_on_chain_metrics(symbol, days, "text"))
    
    # Test social sentiment
    print("\n2. SOCIAL SENTIMENT")
    print(query_social_sentiment(symbol, days, "text"))
    
    # Test Fear & Greed Index
    print("\n3. FEAR & GREED INDEX")
    print(query_fear_greed_index(days, "text"))
    
    # Test whale transactions
    print("\n4. WHALE TRANSACTIONS")
    print(query_whale_transactions(symbol, days, "text"))
    
    # Test fundamental analysis
    print("\n5. FUNDAMENTAL ANALYSIS")
    print(get_fundamental_analysis(symbol, days, "text"))
    
    # Test sentiment analysis
    print("\n6. SENTIMENT ANALYSIS")
    print(get_sentiment_analysis(symbol, days, "text"))

if __name__ == "__main__":
    # If Santiment API key is provided as argument, use it
    if len(sys.argv) > 1:
        SANTIMENT_API_KEY = sys.argv[1]
    
    # Test the query functions
    test_query_functions()
"""
AutoGen Latest Test

This script tests AutoGen function registration using the latest API.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import AutoGen
try:
    from autogen import ConversableAgent, AssistantAgent, UserProxyAgent, config_list_from_json
except ImportError:
    logger.error("Failed to import AutoGen. Make sure it's installed with 'pip install pyautogen'")
    sys.exit(1)

def get_bitcoin_data(interval: str = "daily") -> str:
    """
    Get Bitcoin price data with the specified interval.
    
    Args:
        interval: Time interval ('hourly', 'daily', 'weekly')
        
    Returns:
        A formatted string with Bitcoin price data
    """
    # Simulated data that would normally come from database
    if interval == "hourly":
        data = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "prices": [
                {"timestamp": "2025-04-06T15:00:00Z", "price": 88291.23},
                {"timestamp": "2025-04-06T16:00:00Z", "price": 88124.77},
                {"timestamp": "2025-04-06T17:00:00Z", "price": 88058.91},
                {"timestamp": "2025-04-06T18:00:00Z", "price": 88081.87}
            ],
            "change_percent": -0.24,
            "volume": 12458.92
        }
    elif interval == "daily":
        data = {
            "symbol": "BTCUSDT",
            "interval": "1d",
            "prices": [
                {"timestamp": "2025-04-03", "price": 85623.45},
                {"timestamp": "2025-04-04", "price": 86730.25},
                {"timestamp": "2025-04-05", "price": 87556.12},
                {"timestamp": "2025-04-06", "price": 88081.87}
            ],
            "change_percent": 2.86,
            "volume": 45789.32
        }
    else:  # weekly
        data = {
            "symbol": "BTCUSDT",
            "interval": "1w",
            "prices": [
                {"timestamp": "2025-03-10", "price": 75432.18},
                {"timestamp": "2025-03-17", "price": 78912.34},
                {"timestamp": "2025-03-24", "price": 82345.67},
                {"timestamp": "2025-03-31", "price": 85678.90},
                {"timestamp": "2025-04-06", "price": 88081.87}
            ],
            "change_percent": 16.77,
            "volume": 187652.43
        }
    
    # Format the response nicely
    result = f"## Bitcoin Price Data ({interval})\n\n"
    result += f"**Symbol**: {data['symbol']}\n"
    result += f"**Interval**: {data['interval']}\n"
    result += f"**Latest Price**: ${data['prices'][-1]['price']:.2f}\n"
    result += f"**Change**: {data['change_percent']:.2f}%\n"
    result += f"**Volume**: {data['volume']:.2f} BTC\n\n"
    
    result += "**Price History**:\n"
    for entry in data['prices']:
        result += f"- {entry['timestamp']}: ${entry['price']:.2f}\n"
    
    result += "\n**Analysis**:\n"
    if data['change_percent'] > 5:
        result += "Bitcoin is showing strong upward momentum in this timeframe.\n"
    elif data['change_percent'] > 0:
        result += "Bitcoin is showing positive but modest gains in this timeframe.\n"
    elif data['change_percent'] > -5:
        result += "Bitcoin is relatively stable with slight negative pressure in this timeframe.\n"
    else:
        result += "Bitcoin is showing significant downward pressure in this timeframe.\n"
    
    return result

def get_technical_indicators(symbol: str = "BTCUSDT") -> str:
    """
    Get technical indicators for a cryptocurrency.
    
    Args:
        symbol: Trading pair symbol
        
    Returns:
        A formatted string with technical indicators
    """
    indicators = {
        "symbol": symbol,
        "timestamp": "2025-04-06T19:00:00Z",
        "indicators": {
            "RSI(14)": 62.5,
            "MACD": {
                "MACD Line": 245.32,
                "Signal Line": 205.67,
                "Histogram": 39.65
            },
            "Bollinger Bands": {
                "Upper": 89750.23,
                "Middle": 87250.45,
                "Lower": 84750.67
            },
            "Moving Averages": {
                "MA(50)": 84234.56,
                "MA(100)": 79567.89,
                "MA(200)": 72345.67
            }
        }
    }
    
    result = f"## Technical Indicators for {symbol}\n\n"
    result += f"**Timestamp**: {indicators['timestamp']}\n\n"
    
    result += "### RSI(14)\n"
    rsi = indicators['indicators']['RSI(14)']
    result += f"Value: {rsi:.1f}\n"
    if rsi > 70:
        result += "Interpretation: Overbought conditions, potential reversal or correction\n"
    elif rsi < 30:
        result += "Interpretation: Oversold conditions, potential reversal or bounce\n"
    else:
        result += "Interpretation: Neutral conditions\n"
    
    result += "\n### MACD\n"
    macd = indicators['indicators']['MACD']
    result += f"MACD Line: {macd['MACD Line']:.2f}\n"
    result += f"Signal Line: {macd['Signal Line']:.2f}\n"
    result += f"Histogram: {macd['Histogram']:.2f}\n"
    if macd['Histogram'] > 0 and macd['MACD Line'] > 0:
        result += "Interpretation: Bullish momentum\n"
    elif macd['Histogram'] < 0 and macd['MACD Line'] < 0:
        result += "Interpretation: Bearish momentum\n"
    elif macd['Histogram'] > 0 and macd['Histogram'] > macd['Histogram']:
        result += "Interpretation: Increasing bullish momentum\n"
    elif macd['Histogram'] < 0 and macd['Histogram'] < macd['Histogram']:
        result += "Interpretation: Increasing bearish momentum\n"
    
    result += "\n### Bollinger Bands\n"
    bb = indicators['indicators']['Bollinger Bands']
    result += f"Upper Band: ${bb['Upper']:.2f}\n"
    result += f"Middle Band: ${bb['Middle']:.2f}\n"
    result += f"Lower Band: ${bb['Lower']:.2f}\n"
    
    price = indicators['indicators']['Bollinger Bands']['Middle']
    if price > bb['Upper']:
        result += "Interpretation: Price above upper band, potential overbought conditions\n"
    elif price < bb['Lower']:
        result += "Interpretation: Price below lower band, potential oversold conditions\n"
    else:
        result += "Interpretation: Price within bands, normal volatility\n"
    
    result += "\n### Moving Averages\n"
    ma = indicators['indicators']['Moving Averages']
    result += f"MA(50): ${ma['MA(50)']:.2f}\n"
    result += f"MA(100): ${ma['MA(100)']:.2f}\n"
    result += f"MA(200): ${ma['MA(200)']:.2f}\n"
    
    if ma['MA(50)'] > ma['MA(100)'] > ma['MA(200)']:
        result += "Interpretation: Strong uptrend with all MAs aligned bullishly\n"
    elif ma['MA(50)'] < ma['MA(100)'] < ma['MA(200)']:
        result += "Interpretation: Strong downtrend with all MAs aligned bearishly\n"
    elif ma['MA(50)'] > ma['MA(100)']:
        result += "Interpretation: Recent bullish crossover of MA(50) above MA(100)\n"
    elif ma['MA(50)'] < ma['MA(100)']:
        result += "Interpretation: Recent bearish crossover of MA(50) below MA(100)\n"
    
    return result

def run_autogen_test():
    """Run a test with the latest AutoGen API"""
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key found in environment variables")
        sys.exit(1)
    
    # Show that we have an API key (first/last 4 chars only)
    logger.info(f"Using API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # Create config
    llm_config = {
        "config_list": [{"model": "gpt-3.5-turbo", "api_key": api_key}],
        "temperature": 0.2,
        "functions": [
            {
                "name": "get_bitcoin_data",
                "description": "Get Bitcoin price data with the specified interval",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "interval": {
                            "type": "string",
                            "enum": ["hourly", "daily", "weekly"],
                            "description": "Time interval for the price data"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_technical_indicators",
                "description": "Get technical indicators for a cryptocurrency",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading pair symbol (e.g., 'BTCUSDT')"
                        }
                    },
                    "required": []
                }
            }
        ]
    }
    
    # Create assistant agent
    assistant = AssistantAgent(
        name="CryptoAnalyst",
        system_message="""You are a cryptocurrency market analyst. 
        You can access Bitcoin price data and technical indicators through function calls.
        Provide clear, concise analysis based on the data you retrieve.""",
        llm_config=llm_config
    )
    
    # Register functions directly
    assistant.register_function(
        function_map={
            "get_bitcoin_data": get_bitcoin_data,
            "get_technical_indicators": get_technical_indicators
        }
    )
    
    # Create user proxy agent
    user = UserProxyAgent(
        name="User",
        code_execution_config=False,
        human_input_mode="TERMINATE"
    )
    
    # Start the conversation
    user.initiate_chat(
        assistant,
        message="Can you analyze Bitcoin's recent price performance and show me some technical indicators?"
    )

if __name__ == "__main__":
    run_autogen_test()
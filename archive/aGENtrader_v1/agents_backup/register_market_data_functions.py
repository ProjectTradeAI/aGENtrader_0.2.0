"""
Register Market Data Functions for AutoGen

This module registers the market data query functions with AutoGen.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import market data functions
try:
    from agents.query_market_data import (
        query_market_data,
        get_market_price,
        get_market_analysis
    )
except ImportError as e:
    logger.error(f"Error importing market data functions: {str(e)}")
    raise ImportError("Market data query functions not available")

def register_market_data_functions(agent):
    """
    Register market data functions with an AutoGen agent.
    
    Args:
        agent: AutoGen agent to register functions with
    """
    function_map = {
        "query_market_data": {
            "name": "query_market_data",
            "description": "Query historical market data for a specific cryptocurrency symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol, e.g., 'BTCUSDT'"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)",
                        "default": "1h"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of data points to retrieve",
                        "default": 24
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (alternative to limit)",
                        "default": None
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "default": "json"
                    }
                },
                "required": ["symbol"]
            },
            "function": query_market_data
        },
        "get_market_price": {
            "name": "get_market_price",
            "description": "Get the latest market price for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol, e.g., 'BTCUSDT'"
                    }
                },
                "required": ["symbol"]
            },
            "function": get_market_price
        },
        "get_market_analysis": {
            "name": "get_market_analysis",
            "description": "Get technical analysis and market statistics for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol, e.g., 'BTCUSDT'"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Time interval (1h, 4h, 1d)",
                        "default": "1d"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back",
                        "default": 30
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "default": "json"
                    }
                },
                "required": ["symbol"]
            },
            "function": get_market_analysis
        }
    }
    
    # Register functions with the agent
    try:
        for func_name, func_config in function_map.items():
            logger.info(f"Registering function: {func_name}")
            agent.register_function(
                function_map=func_config
            )
        logger.info("Successfully registered market data functions")
        return True
    except Exception as e:
        logger.error(f"Error registering market data functions: {str(e)}")
        return False

def register_with_autogen():
    """
    Register market data functions with AutoGen Assistant.
    
    This function is used to register the market data query functions with
    an AutoGen Assistant. It needs to be imported and called in the agent 
    initialization code.
    
    Returns:
        Dictionary mapping function names to their implementations
    """
    return {
        "query_market_data": query_market_data,
        "get_market_price": get_market_price,
        "get_market_analysis": get_market_analysis
    }

# Example implementation for AutoGen
def create_function_mapping():
    """
    Create a function mapping for use with AutoGen.
    
    Returns:
        List of function configurations
    """
    return [
        {
            "name": "query_market_data",
            "description": "Query historical market data for a specific cryptocurrency symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol, e.g., 'BTCUSDT'"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)",
                        "enum": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
                        "default": "1h"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of data points to retrieve",
                        "default": 24
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (alternative to limit)"
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "enum": ["json", "markdown", "text"],
                        "default": "json"
                    }
                },
                "required": ["symbol"]
            }
        },
        {
            "name": "get_market_price",
            "description": "Get the latest market price for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol, e.g., 'BTCUSDT'"
                    }
                },
                "required": ["symbol"]
            }
        },
        {
            "name": "get_market_analysis",
            "description": "Get technical analysis and market statistics for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol, e.g., 'BTCUSDT'"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Time interval (1h, 4h, 1d)",
                        "enum": ["1h", "4h", "1d"],
                        "default": "1d"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back",
                        "default": 30
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "enum": ["json", "markdown", "text"],
                        "default": "json"
                    }
                },
                "required": ["symbol"]
            }
        }
    ]

if __name__ == "__main__":
    # Print the function mapping as JSON (can be used with AutoGen)
    print(json.dumps(create_function_mapping(), indent=2))
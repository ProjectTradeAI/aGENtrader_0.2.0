"""
Register Advanced Data Functions for AutoGen

This module registers advanced data query functions with AutoGen.
These functions provide agents with access to:
- On-chain metrics
- Social sentiment data
- Fear & Greed Index
- Whale transactions
- Fundamental analysis
- Sentiment analysis
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import advanced data functions
try:
    from agents.query_advanced_data import (
        query_on_chain_metrics,
        query_social_sentiment,
        query_fear_greed_index,
        query_whale_transactions,
        get_fundamental_analysis,
        get_sentiment_analysis
    )
except ImportError as e:
    logger.error(f"Error importing advanced data functions: {str(e)}")
    raise ImportError("Advanced data query functions not available")

def register_advanced_data_functions(agent):
    """
    Register advanced data functions with an AutoGen agent.
    
    Args:
        agent: AutoGen agent to register functions with
    """
    function_map = {
        "query_on_chain_metrics": {
            "name": "query_on_chain_metrics",
            "description": "Query on-chain metrics for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol, e.g., 'BTC', 'ETH'"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "default": "json"
                    }
                },
                "required": ["symbol"]
            },
            "function": query_on_chain_metrics
        },
        "query_social_sentiment": {
            "name": "query_social_sentiment",
            "description": "Query social sentiment data for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol, e.g., 'BTC', 'ETH'"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "default": "json"
                    }
                },
                "required": ["symbol"]
            },
            "function": query_social_sentiment
        },
        "query_fear_greed_index": {
            "name": "query_fear_greed_index",
            "description": "Query the Fear & Greed Index for the cryptocurrency market",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "default": "json"
                    }
                },
                "required": []
            },
            "function": query_fear_greed_index
        },
        "query_whale_transactions": {
            "name": "query_whale_transactions",
            "description": "Query whale transaction data for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol, e.g., 'BTC', 'ETH'"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "default": "json"
                    }
                },
                "required": ["symbol"]
            },
            "function": query_whale_transactions
        },
        "get_fundamental_analysis": {
            "name": "get_fundamental_analysis",
            "description": "Get a comprehensive fundamental analysis for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol, e.g., 'BTC', 'ETH'"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data to analyze",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "default": "json"
                    }
                },
                "required": ["symbol"]
            },
            "function": get_fundamental_analysis
        },
        "get_sentiment_analysis": {
            "name": "get_sentiment_analysis",
            "description": "Get a comprehensive sentiment analysis for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol, e.g., 'BTC', 'ETH'"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data to analyze",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "default": "json"
                    }
                },
                "required": ["symbol"]
            },
            "function": get_sentiment_analysis
        }
    }
    
    # Register functions with the agent
    try:
        for func_name, func_config in function_map.items():
            logger.info(f"Registering function: {func_name}")
            agent.register_function(
                function_map=func_config
            )
        logger.info("Successfully registered advanced data functions")
        return True
    except Exception as e:
        logger.error(f"Error registering advanced data functions: {str(e)}")
        return False

def register_with_autogen():
    """
    Register advanced data functions with AutoGen Assistant.
    
    This function is used to register the advanced data query functions with
    an AutoGen Assistant. It needs to be imported and called in the agent 
    initialization code.
    
    Returns:
        Dictionary mapping function names to their implementations
    """
    return {
        "query_on_chain_metrics": query_on_chain_metrics,
        "query_social_sentiment": query_social_sentiment,
        "query_fear_greed_index": query_fear_greed_index,
        "query_whale_transactions": query_whale_transactions,
        "get_fundamental_analysis": get_fundamental_analysis,
        "get_sentiment_analysis": get_sentiment_analysis
    }

def create_function_mapping():
    """
    Create a function mapping for use with AutoGen.
    
    Returns:
        List of function configurations
    """
    return [
        {
            "name": "query_on_chain_metrics",
            "description": "Query on-chain metrics for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol, e.g., 'BTC', 'ETH'"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "enum": ["json", "markdown", "text"],
                        "default": "markdown"
                    }
                },
                "required": ["symbol"]
            }
        },
        {
            "name": "query_social_sentiment",
            "description": "Query social sentiment data for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol, e.g., 'BTC', 'ETH'"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "enum": ["json", "markdown", "text"],
                        "default": "markdown"
                    }
                },
                "required": ["symbol"]
            }
        },
        {
            "name": "query_fear_greed_index",
            "description": "Query the Fear & Greed Index for the cryptocurrency market",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "enum": ["json", "markdown", "text"],
                        "default": "markdown"
                    }
                }
            }
        },
        {
            "name": "query_whale_transactions",
            "description": "Query whale transaction data for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol, e.g., 'BTC', 'ETH'"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "enum": ["json", "markdown", "text"],
                        "default": "markdown"
                    }
                },
                "required": ["symbol"]
            }
        },
        {
            "name": "get_fundamental_analysis",
            "description": "Get a comprehensive fundamental analysis for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol, e.g., 'BTC', 'ETH'"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data to analyze",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "enum": ["json", "markdown", "text"],
                        "default": "markdown"
                    }
                },
                "required": ["symbol"]
            }
        },
        {
            "name": "get_sentiment_analysis",
            "description": "Get a comprehensive sentiment analysis for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol, e.g., 'BTC', 'ETH'"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data to analyze",
                        "default": 7
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "enum": ["json", "markdown", "text"],
                        "default": "markdown"
                    }
                },
                "required": ["symbol"]
            }
        }
    ]

if __name__ == "__main__":
    # Print the function mapping as JSON (can be used with AutoGen)
    print(json.dumps(create_function_mapping(), indent=2))
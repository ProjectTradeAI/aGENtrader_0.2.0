"""
AutoGen Database Integration

Provides tools and utilities for integrating database access with AutoGen agents
and handling serialization of database query results.
"""

import os
import json
import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("autogen_db")

# Import database functions
from agents.database_retrieval_tool import (
    get_latest_price,
    get_recent_market_data,
    get_price_history,
    calculate_moving_average,
    calculate_rsi,
    find_support_resistance,
    get_market_summary,
    detect_patterns,
    calculate_volatility
)

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and Decimal objects"""
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        try:
            from decimal import Decimal
            if isinstance(o, Decimal):
                return float(o)
        except ImportError:
            pass
        return super().default(o)

def serialize_results(results: Any) -> str:
    """
    Serialize results to JSON string
    
    Args:
        results: Results to serialize
        
    Returns:
        JSON string representation of results
    """
    return json.dumps(results, cls=CustomJSONEncoder, indent=2)

def parse_json_response(json_str: Optional[str]) -> Any:
    """
    Parse JSON string response from database functions
    
    Args:
        json_str: JSON string (or None)
        
    Returns:
        Parsed JSON data
    """
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return None

def format_trading_decision(decision_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format trading decision data with standardized fields
    
    Args:
        decision_data: Raw decision data
        
    Returns:
        Formatted decision
    """
    # Default values
    formatted = {
        "action": "HOLD",
        "confidence": 0,
        "reasoning": "No decision data provided",
        "price": 0,
        "risk_level": "medium",
        "timestamp": datetime.now().isoformat()
    }
    
    # Update with provided data (case insensitive for action)
    if decision_data:
        if "action" in decision_data:
            action = decision_data["action"].upper()
            if action in ["BUY", "SELL", "HOLD"]:
                formatted["action"] = action
        
        # Copy other fields
        for field in ["confidence", "reasoning", "price", "risk_level"]:
            if field in decision_data:
                formatted[field] = decision_data[field]
    
    return formatted

def create_market_data_function_map() -> Dict[str, Callable]:
    """
    Create a function map for market data functions to be used by AutoGen agents
    
    Returns:
        Dictionary mapping function names to callables
    """
    def _get_latest_price(symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Get the latest price for a symbol"""
        result = get_latest_price(symbol)
        return parse_json_response(result)
    
    def _get_recent_market_data(symbol: str = "BTCUSDT", limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent market data for a symbol"""
        result = get_recent_market_data(symbol, limit)
        return parse_json_response(result)
    
    def _get_price_history(symbol: str = "BTCUSDT", days: int = 7) -> List[Dict[str, Any]]:
        """Get price history for a symbol"""
        result = get_price_history(symbol, days)
        return parse_json_response(result)
    
    def _calculate_moving_average(symbol: str = "BTCUSDT", period: int = 20) -> Dict[str, Any]:
        """Calculate simple moving average for a symbol"""
        result = calculate_moving_average(symbol, period)
        return parse_json_response(result)
    
    def _calculate_rsi(symbol: str = "BTCUSDT", period: int = 14) -> Dict[str, Any]:
        """Calculate RSI for a symbol"""
        result = calculate_rsi(symbol, period)
        return parse_json_response(result)
    
    def _find_support_resistance(symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Find support and resistance levels for a symbol"""
        result = find_support_resistance(symbol)
        return parse_json_response(result)
    
    def _get_market_summary(symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Get market summary for a symbol"""
        result = get_market_summary(symbol)
        return parse_json_response(result)
    
    def _detect_patterns(symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Detect patterns in price action for a symbol"""
        result = detect_patterns(symbol)
        return parse_json_response(result)
    
    def _calculate_volatility(symbol: str = "BTCUSDT", days: int = 7) -> Dict[str, Any]:
        """Calculate volatility for a symbol"""
        result = calculate_volatility(symbol, days)
        return parse_json_response(result)
    
    return {
        "get_latest_price": _get_latest_price,
        "get_recent_market_data": _get_recent_market_data,
        "get_price_history": _get_price_history,
        "calculate_moving_average": _calculate_moving_average,
        "calculate_rsi": _calculate_rsi,
        "find_support_resistance": _find_support_resistance,
        "get_market_summary": _get_market_summary,
        "detect_patterns": _detect_patterns,
        "calculate_volatility": _calculate_volatility
    }

def create_db_function_specs() -> List[Dict[str, Any]]:
    """
    Create function specifications for database access functions
    
    Returns:
        List of function specifications
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_latest_price",
                "description": "Get the latest price for a cryptocurrency symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The trading symbol (e.g., BTCUSDT)"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_recent_market_data",
                "description": "Get recent market data points for a cryptocurrency symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The trading symbol (e.g., BTCUSDT)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of recent data points to retrieve"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_price_history",
                "description": "Get historical price data for a cryptocurrency symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The trading symbol (e.g., BTCUSDT)"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days of history to retrieve"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_moving_average",
                "description": "Calculate the simple moving average for a cryptocurrency symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The trading symbol (e.g., BTCUSDT)"
                        },
                        "period": {
                            "type": "integer",
                            "description": "Period for calculating the moving average"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_rsi",
                "description": "Calculate the Relative Strength Index for a cryptocurrency symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The trading symbol (e.g., BTCUSDT)"
                        },
                        "period": {
                            "type": "integer",
                            "description": "Period for calculating RSI"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "find_support_resistance",
                "description": "Find support and resistance levels for a cryptocurrency symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The trading symbol (e.g., BTCUSDT)"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_market_summary",
                "description": "Get a comprehensive market summary for a cryptocurrency symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The trading symbol (e.g., BTCUSDT)"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "detect_patterns",
                "description": "Detect common chart patterns in the price action",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The trading symbol (e.g., BTCUSDT)"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_volatility",
                "description": "Calculate the price volatility over a period",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The trading symbol (e.g., BTCUSDT)"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days for volatility calculation"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        }
    ]

def enhance_llm_config(config: Any) -> Dict[str, Any]:
    """
    Enhance LLM configuration with database function specifications
    
    Args:
        config: Base LLM configuration (either a dict or a list of dicts)
        
    Returns:
        Enhanced LLM configuration
    """
    # Add function specifications
    function_specs = create_db_function_specs()
    
    # Handle different config formats
    if isinstance(config, list):
        # For list format, create a proper llm_config dictionary
        enhanced_config = {
            "config_list": config,
            "tools": function_specs
        }
    else:
        # For dictionary format, create a deep copy and add tools
        enhanced_config = config.copy() if config else {}
        enhanced_config["tools"] = function_specs
    
    return enhanced_config

def create_speaker_llm_config(config: Any) -> Dict[str, Any]:
    """
    Create a clean LLM configuration for speaker selection agent.
    This version doesn't include function tools or functions which GroupChatManager 
    doesn't support.
    
    Args:
        config: Base LLM configuration (either a dict or a list of dicts)
        
    Returns:
        Clean LLM configuration for speaker selection
    """
    # Handle different config formats
    if isinstance(config, list):
        # For list format, create a proper llm_config dictionary
        clean_config = {
            "config_list": config
        }
    else:
        # For dictionary format, create a deep copy without tools and functions
        clean_config = config.copy() if config else {}
        if "tools" in clean_config:
            del clean_config["tools"]
        if "functions" in clean_config:
            del clean_config["functions"]
    
    return clean_config
    
def get_integration(config: Any = None) -> Dict[str, Any]:
    """
    Get database integration for AutoGen
    
    Args:
        config: Base LLM configuration (optional) - can be a dict or a list of dicts
        
    Returns:
        Integration configuration with functions
    """
    # Create function map
    function_map = create_market_data_function_map()
    
    # Enhance LLM config if provided
    if config:
        enhanced_config = enhance_llm_config(config)
    else:
        enhanced_config = {"tools": create_db_function_specs()}
    
    # Create the integration result - function_map is kept separate
    # to avoid JSON serialization issues
    return {
        "function_map": function_map,
        "llm_config": enhanced_config,
        "function_specs": create_db_function_specs()
    }
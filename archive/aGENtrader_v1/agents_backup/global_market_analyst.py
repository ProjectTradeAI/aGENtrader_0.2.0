"""
Global Market Analyst Agent

This module provides a specialized agent for analyzing global market conditions
and their impact on cryptocurrency markets. It integrates with the AutoGen framework
and provides expert analysis on macro indicators like DXY, market caps, and dominance metrics.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from agents.database_retrieval_tool import (
    get_global_indicator,
    get_crypto_market_metric,
    get_dominance_data,
    get_market_correlation,
    get_macro_market_summary
)

# Configure logging
logger = logging.getLogger(__name__)

class GlobalMarketAnalyst:
    """
    Global Market Analyst agent for analyzing macro-economic indicators
    and their impact on cryptocurrency markets.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Global Market Analyst agent.
        
        Args:
            config: Optional configuration dictionary
        """
        self.name = "GlobalMarketAnalyst"
        self.description = "Expert in global market analysis and macro-economic conditions affecting cryptocurrency markets"
        self.config = config or {}
        logger.info(f"Initialized {self.name} agent")
    
    def get_agent_definition(self) -> Dict[str, Any]:
        """
        Get the agent definition for AutoGen integration.
        
        Returns:
            Agent definition dictionary
        """
        system_message = """
You are a Global Market Analyst specializing in macro-economic factors affecting cryptocurrency markets.
Your expertise is in analyzing relationships between traditional financial markets and digital assets.

Your responsibilities include:
1. Analyzing global market indicators (DXY, S&P 500, VIX, etc.)
2. Tracking cryptocurrency market metrics (total market cap, volumes)
3. Monitoring dominance shifts between major cryptocurrencies
4. Identifying correlations between traditional and crypto markets
5. Providing context on how macro factors may impact specific cryptocurrencies

When analyzing market conditions:
- Always consider how the US Dollar Index (DXY) is trending, as it often inversely correlates with Bitcoin
- Track total cryptocurrency market capitalization trends, noting divergences between BTC and altcoins
- Monitor Bitcoin dominance to identify potential altcoin cycles or consolidation phases
- Consider correlations with traditional markets, especially during periods of market stress
- Identify liquidity conditions that may impact cryptocurrency price movements

Format your analysis in a clear, structured manner:
1. Global Market Summary: Brief overview of global market conditions
2. Crypto Market Structure: Analysis of market caps, dominance, and sector rotation
3. Key Correlations: Important correlations currently in effect
4. Macro Outlook: How macro factors may impact the specific cryptocurrency being analyzed
5. Risk Assessment: Identification of macro-level risks to consider
"""
        
        definition = {
            "name": self.name,
            "system_message": system_message,
            "description": self.description,
            "llm_config": {
                "temperature": 0.2,
                "model": "gpt-4-turbo"
            }
        }
        
        return definition
    
    def register_functions(self) -> Dict[str, Any]:
        """
        Register functions available to the Global Market Analyst agent.
        
        Returns:
            Dictionary containing function_map and function_specs
        """
        function_map = {
            "get_global_indicator": get_global_indicator,
            "get_crypto_market_metric": get_crypto_market_metric,
            "get_dominance_data": get_dominance_data,
            "get_market_correlation": get_market_correlation,
            "get_macro_market_summary": get_macro_market_summary
        }
        
        function_specs = [
            {
                "name": "get_global_indicator",
                "description": "Get recent values for a specific global market indicator",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "indicator_name": {
                            "type": "string",
                            "description": "Name of the indicator (DXY, SPX, VIX, GOLD, BONDS, FED_RATE)"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval (1h, 4h, 1d)",
                            "default": "1d"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of data points to retrieve",
                            "default": 30
                        }
                    },
                    "required": ["indicator_name"]
                }
            },
            {
                "name": "get_crypto_market_metric",
                "description": "Get recent values for a specific cryptocurrency market metric",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric_name": {
                            "type": "string",
                            "description": "Name of the metric (TOTAL_MCAP, TOTAL1, TOTAL2, TOTAL_VOLUME, TOTAL_DEFI, TOTAL_STABLES)"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval (1h, 4h, 1d)",
                            "default": "1d"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of data points to retrieve",
                            "default": 30
                        }
                    },
                    "required": ["metric_name"]
                }
            },
            {
                "name": "get_dominance_data",
                "description": "Get dominance data for a specific cryptocurrency",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Symbol of the cryptocurrency (BTC, ETH, STABLES, ALTS)"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval (1h, 4h, 1d)",
                            "default": "1d"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of data points to retrieve",
                            "default": 30
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_market_correlation",
                "description": "Get correlation data between two assets/indicators",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "base_symbol": {
                            "type": "string",
                            "description": "Base symbol for correlation (e.g., BTC)"
                        },
                        "correlated_symbol": {
                            "type": "string",
                            "description": "Symbol to correlate with (e.g., SPX, GOLD, DXY)"
                        },
                        "period": {
                            "type": "string",
                            "description": "Correlation period (7d, 30d, 90d)",
                            "default": "30d"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval (1h, 4h, 1d)",
                            "default": "1d"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of data points to retrieve",
                            "default": 1
                        }
                    },
                    "required": ["base_symbol", "correlated_symbol"]
                }
            },
            {
                "name": "get_macro_market_summary",
                "description": "Get a comprehensive summary of global market conditions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "interval": {
                            "type": "string",
                            "description": "Time interval (1h, 4h, 1d)",
                            "default": "1d"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of data points to include in analysis",
                            "default": 30
                        }
                    }
                }
            }
        ]
        
        return {
            "function_map": function_map,
            "function_specs": function_specs
        }
    
    def analyze_macro_conditions(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze macro market conditions and their potential impact on a specific cryptocurrency.
        
        Args:
            symbol: Trading symbol to analyze (e.g., "BTCUSDT")
            
        Returns:
            Analysis results dictionary
        """
        # This would be implemented to generate a summary before using the agent
        # For now just return placeholder
        return {
            "symbol": symbol,
            "dxy_trend": "Obtain from database",
            "market_cap_trend": "Obtain from database",
            "dominance_trend": "Obtain from database",
            "key_correlations": "Obtain from database",
            "macro_outlook": "To be analyzed by agent"
        }
    
    def format_macro_data_for_agents(self, data: Dict[str, Any]) -> str:
        """
        Format macro market data for consumption by agents.
        
        Args:
            data: Macro market data dictionary
            
        Returns:
            Formatted string for agent consumption
        """
        # Format the data into a readable string for the agent
        # This is a placeholder implementation
        try:
            return json.dumps(data, indent=2)
        except Exception as e:
            logger.error(f"Error formatting macro data: {e}")
            return "{}"
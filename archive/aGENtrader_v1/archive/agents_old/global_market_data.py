"""
Global Market Data Access Module

This module provides functions for accessing global market data stored in the database.
It includes functions for retrieving indicators, metrics, and correlation data.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from decimal import Decimal

# Configure logging
logger = logging.getLogger(__name__)

# Import database connector from existing module
try:
    from agents.database_retrieval_tool import get_database_connection, serialize_decimal, serialize_datetime
except ImportError:
    logger.error("Failed to import database connector")
    
    # Fallback implementations to allow the module to load
    def get_database_connection():
        raise NotImplementedError("Database connection not available")
    
    def serialize_decimal(dec):
        if isinstance(dec, Decimal):
            return float(dec)
        return dec
    
    def serialize_datetime(dt):
        if isinstance(dt, datetime):
            return dt.isoformat()
        return dt

def format_global_data(data: Any) -> Any:
    """
    Format global market data for agent consumption.
    
    Args:
        data: Data to format (can be various types)
        
    Returns:
        Formatted data suitable for JSON serialization
    """
    if isinstance(data, list):
        return [format_global_data(item) for item in data]
    elif isinstance(data, dict):
        return {k: format_global_data(v) for k, v in data.items()}
    elif isinstance(data, datetime):
        return serialize_datetime(data)
    elif isinstance(data, Decimal):
        return serialize_decimal(data)
    return data

def get_global_indicator(indicator_name: str, interval: str = "1d", limit: int = 30) -> List[Dict[str, Any]]:
    """
    Get recent values for a specific global market indicator.
    
    Args:
        indicator_name: Name of the indicator (DXY, SPX, VIX, GOLD, BONDS, FED_RATE)
        interval: Time interval (1h, 4h, 1d)
        limit: Number of data points to retrieve
        
    Returns:
        List of indicator data points
    """
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT timestamp, indicator_name, value, source
        FROM global_market_indicators
        WHERE indicator_name = %s AND interval = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        
        cursor.execute(query, (indicator_name, interval, limit))
        rows = cursor.fetchall()
        cursor.close()
        
        result = []
        for row in rows:
            result.append({
                "timestamp": row[0],
                "indicator_name": row[1],
                "value": row[2],
                "source": row[3]
            })
        
        return format_global_data(result)
    
    except Exception as e:
        logger.error(f"Error retrieving global indicator {indicator_name}: {e}")
        return []

def get_crypto_market_metric(metric_name: str, interval: str = "1d", limit: int = 30) -> List[Dict[str, Any]]:
    """
    Get recent values for a specific cryptocurrency market metric.
    
    Args:
        metric_name: Name of the metric (TOTAL_MCAP, TOTAL1, TOTAL2, TOTAL_VOLUME, etc.)
        interval: Time interval (1h, 4h, 1d)
        limit: Number of data points to retrieve
        
    Returns:
        List of metric data points
    """
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT timestamp, metric_name, value
        FROM crypto_market_metrics
        WHERE metric_name = %s AND interval = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        
        cursor.execute(query, (metric_name, interval, limit))
        rows = cursor.fetchall()
        cursor.close()
        
        result = []
        for row in rows:
            result.append({
                "timestamp": row[0],
                "metric_name": row[1],
                "value": row[2]
            })
        
        return format_global_data(result)
    
    except Exception as e:
        logger.error(f"Error retrieving crypto market metric {metric_name}: {e}")
        return []

def get_dominance_data(symbol: str, interval: str = "1d", limit: int = 30) -> List[Dict[str, Any]]:
    """
    Get dominance data for a specific cryptocurrency.
    
    Args:
        symbol: Symbol of the cryptocurrency (BTC, ETH, STABLES, ALTS)
        interval: Time interval (1h, 4h, 1d)
        limit: Number of data points to retrieve
        
    Returns:
        List of dominance data points
    """
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT timestamp, symbol, dominance_percentage
        FROM dominance_metrics
        WHERE symbol = %s AND interval = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        
        cursor.execute(query, (symbol, interval, limit))
        rows = cursor.fetchall()
        cursor.close()
        
        result = []
        for row in rows:
            result.append({
                "timestamp": row[0],
                "symbol": row[1],
                "dominance_percentage": row[2]
            })
        
        return format_global_data(result)
    
    except Exception as e:
        logger.error(f"Error retrieving dominance data for {symbol}: {e}")
        return []

def get_market_correlation(base_symbol: str, correlated_symbol: str, 
                         period: str = "30d", interval: str = "1d", 
                         limit: int = 1) -> List[Dict[str, Any]]:
    """
    Get correlation data between two assets/indicators.
    
    Args:
        base_symbol: Base symbol for correlation (e.g., BTC)
        correlated_symbol: Symbol to correlate with (e.g., SPX, GOLD, DXY)
        period: Correlation period (7d, 30d, 90d)
        interval: Time interval (1h, 4h, 1d)
        limit: Number of data points to retrieve
        
    Returns:
        List of correlation data points
    """
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT timestamp, base_symbol, correlated_symbol, correlation_coefficient, period
        FROM market_correlations
        WHERE base_symbol = %s AND correlated_symbol = %s AND period = %s AND interval = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        
        cursor.execute(query, (base_symbol, correlated_symbol, period, interval, limit))
        rows = cursor.fetchall()
        cursor.close()
        
        result = []
        for row in rows:
            result.append({
                "timestamp": row[0],
                "base_symbol": row[1],
                "correlated_symbol": row[2],
                "correlation_coefficient": row[3],
                "period": row[4]
            })
        
        return format_global_data(result)
    
    except Exception as e:
        logger.error(f"Error retrieving correlation between {base_symbol} and {correlated_symbol}: {e}")
        return []

def get_macro_market_summary(interval: str = "1d", limit: int = 30) -> Dict[str, Any]:
    """
    Get a comprehensive summary of global market conditions.
    
    Args:
        interval: Time interval (1h, 4h, 1d)
        limit: Number of data points to include in analysis
        
    Returns:
        Dictionary containing global market summary
    """
    try:
        # Get key indicators
        dxy_data = get_global_indicator("DXY", interval, limit)
        spx_data = get_global_indicator("SPX", interval, limit)
        vix_data = get_global_indicator("VIX", interval, limit)
        
        # Get crypto market metrics
        total_mcap = get_crypto_market_metric("TOTAL_MCAP", interval, limit)
        total1 = get_crypto_market_metric("TOTAL1", interval, limit)
        total2 = get_crypto_market_metric("TOTAL2", interval, limit)
        
        # Get dominance metrics
        btc_dominance = get_dominance_data("BTC", interval, limit)
        eth_dominance = get_dominance_data("ETH", interval, limit)
        
        # Get key correlations
        btc_dxy_corr = get_market_correlation("BTC", "DXY", "30d", interval)
        btc_spx_corr = get_market_correlation("BTC", "SPX", "30d", interval)
        
        # Calculate trends
        def calculate_trend(data_list, value_key="value"):
            if not data_list or len(data_list) < 2:
                return "unknown"
            
            latest = data_list[0].get(value_key, 0)
            oldest = data_list[-1].get(value_key, 0)
            
            if latest > oldest * 1.05:  # 5% increase
                return "strongly bullish"
            elif latest > oldest * 1.01:  # 1-5% increase
                return "bullish"
            elif latest < oldest * 0.95:  # 5% decrease
                return "strongly bearish"
            elif latest < oldest * 0.99:  # 1-5% decrease
                return "bearish"
            else:
                return "neutral"
        
        # Compile the summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "interval": interval,
            "global_indicators": {
                "dxy": {
                    "latest": dxy_data[0]["value"] if dxy_data else None,
                    "trend": calculate_trend(dxy_data)
                },
                "spx": {
                    "latest": spx_data[0]["value"] if spx_data else None,
                    "trend": calculate_trend(spx_data)
                },
                "vix": {
                    "latest": vix_data[0]["value"] if vix_data else None,
                    "trend": calculate_trend(vix_data)
                }
            },
            "crypto_metrics": {
                "total_market_cap": {
                    "latest": total_mcap[0]["value"] if total_mcap else None,
                    "trend": calculate_trend(total_mcap)
                },
                "total1": {
                    "latest": total1[0]["value"] if total1 else None,
                    "trend": calculate_trend(total1)
                },
                "total2": {
                    "latest": total2[0]["value"] if total2 else None,
                    "trend": calculate_trend(total2)
                }
            },
            "dominance": {
                "btc": {
                    "latest": btc_dominance[0]["dominance_percentage"] if btc_dominance else None,
                    "trend": calculate_trend(btc_dominance, "dominance_percentage")
                },
                "eth": {
                    "latest": eth_dominance[0]["dominance_percentage"] if eth_dominance else None,
                    "trend": calculate_trend(eth_dominance, "dominance_percentage")
                }
            },
            "correlations": {
                "btc_dxy": btc_dxy_corr[0]["correlation_coefficient"] if btc_dxy_corr else None,
                "btc_spx": btc_spx_corr[0]["correlation_coefficient"] if btc_spx_corr else None
            }
        }
        
        # Add market state analysis
        if dxy_data and total_mcap:
            dxy_trend = calculate_trend(dxy_data)
            mcap_trend = calculate_trend(total_mcap)
            
            if dxy_trend.endswith("bullish") and mcap_trend.endswith("bearish"):
                summary["market_state"] = "Risk-off - Strong dollar pressuring crypto"
            elif dxy_trend.endswith("bearish") and mcap_trend.endswith("bullish"):
                summary["market_state"] = "Risk-on - Weaker dollar supporting crypto"
            elif dxy_trend.endswith("bullish") and mcap_trend.endswith("bullish"):
                summary["market_state"] = "Decoupling - Crypto showing strength despite dollar"
            elif dxy_trend.endswith("bearish") and mcap_trend.endswith("bearish"):
                summary["market_state"] = "Anomalous - Both dollar and crypto weakening"
            else:
                summary["market_state"] = "Neutral - No clear macro correlation"
        
        return format_global_data(summary)
    
    except Exception as e:
        logger.error(f"Error generating macro market summary: {e}")
        return {
            "error": "Failed to generate market summary",
            "timestamp": datetime.now().isoformat()
        }

def update_database_retrieval_tool():
    """
    Function to update the database_retrieval_tool.py module to include the global market data functions.
    This should be called during the system setup process.
    """
    # This would dynamically update the database_retrieval_tool module to include our new functions
    # For the purposes of this implementation, we'll just note that this needs to be done manually
    logger.info("Global market data functions need to be integrated into database_retrieval_tool.py")
    
    # In a real implementation, this could involve:
    # 1. Creating a new version of the database_retrieval_tool.py file
    # 2. Appending our new functions to it
    # 3. Saving the updated file
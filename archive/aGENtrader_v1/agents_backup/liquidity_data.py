"""
Liquidity Data Access Module

This module provides functions for retrieving and analyzing liquidity-related data
from the database. It extends the database_retrieval_tool.py with additional
functionality for the Liquidity Analyst agent.
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union, Tuple

import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Import from existing database_retrieval_tool to reuse functionality
from agents.database_retrieval_tool import (
    get_db_connection, 
    CustomJSONEncoder
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("liquidity_data")

def get_exchange_flows(symbol: str, exchange: Optional[str] = None, 
                     interval: str = "1d", limit: int = 7) -> Union[str, None]:
    """
    Get exchange flow data for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT" or "BTC")
        exchange: Exchange name (or None for all exchanges)
        interval: Data interval (e.g., "1d", "1h")
        limit: Number of data points to retrieve
        
    Returns:
        Exchange flow data as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Build query based on parameters
            query = """
                SELECT timestamp, symbol, exchange, inflow, outflow, net_flow, interval
                FROM exchange_flows
                WHERE symbol = %s AND interval = %s
            """
            params = [symbol, interval]
            
            # Add exchange filter if specified
            if exchange:
                query += " AND exchange = %s"
                params.append(exchange)
            
            # Add ordering and limit
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            # Execute query
            cur.execute(query, params)
            
            results = cur.fetchall()
            if results:
                # Format response
                response = {
                    "symbol": symbol,
                    "exchange": exchange if exchange else "all",
                    "interval": interval,
                    "data": [dict(row) for row in results],
                    "count": len(results)
                }
                
                # Calculate net flow aggregate
                net_flow_total = sum(float(row["net_flow"]) for row in results)
                inflow_total = sum(float(row["inflow"]) for row in results)
                outflow_total = sum(float(row["outflow"]) for row in results)
                
                response["aggregates"] = {
                    "net_flow_total": net_flow_total,
                    "inflow_total": inflow_total,
                    "outflow_total": outflow_total,
                    "period": f"Last {limit} {interval} intervals"
                }
                
                # Convert to JSON string
                return json.dumps(response, cls=CustomJSONEncoder)
            
            return json.dumps({
                "symbol": symbol,
                "exchange": exchange if exchange else "all",
                "interval": interval,
                "data": [],
                "count": 0
            })
    except Exception as e:
        logger.error(f"Error retrieving exchange flows: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_funding_rates(symbol: str, exchange: Optional[str] = None, 
                    interval: str = "8h", limit: int = 10) -> Union[str, None]:
    """
    Get funding rate data for a perpetual futures symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        exchange: Exchange name (or None for all exchanges)
        interval: Data interval (typically "8h" for funding rates)
        limit: Number of data points to retrieve
        
    Returns:
        Funding rate data as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Build query based on parameters
            query = """
                SELECT timestamp, symbol, exchange, funding_rate, next_funding_time, 
                       predicted_rate, interval
                FROM funding_rates
                WHERE symbol = %s AND interval = %s
            """
            params = [symbol, interval]
            
            # Add exchange filter if specified
            if exchange:
                query += " AND exchange = %s"
                params.append(exchange)
            
            # Add ordering and limit
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            # Execute query
            cur.execute(query, params)
            
            results = cur.fetchall()
            if results:
                # Format response
                response = {
                    "symbol": symbol,
                    "exchange": exchange if exchange else "all",
                    "interval": interval,
                    "data": [dict(row) for row in results],
                    "count": len(results)
                }
                
                # Calculate average funding rate
                avg_funding_rate = sum(float(row["funding_rate"]) for row in results) / len(results)
                response["average_funding_rate"] = avg_funding_rate
                
                # Calculate annualized rate (assuming 3 funding events per day)
                annualized_rate = (1 + avg_funding_rate) ** (365 * 3) - 1
                response["annualized_rate"] = annualized_rate
                
                # Add most recent funding rate
                if results:
                    response["latest_funding_rate"] = float(results[0]["funding_rate"])
                    response["latest_timestamp"] = results[0]["timestamp"]
                
                # Convert to JSON string
                return json.dumps(response, cls=CustomJSONEncoder)
            
            return json.dumps({
                "symbol": symbol,
                "exchange": exchange if exchange else "all",
                "interval": interval,
                "data": [],
                "count": 0
            })
    except Exception as e:
        logger.error(f"Error retrieving funding rates: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_market_depth(symbol: str, exchange: Optional[str] = None, 
                   depth_level: Optional[float] = None, 
                   interval: str = "5m", limit: int = 12) -> Union[str, None]:
    """
    Get market depth data for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        exchange: Exchange name (or None for all exchanges)
        depth_level: Depth level to query (or None for all levels)
        interval: Data interval (e.g., "5m", "15m")
        limit: Number of data points to retrieve
        
    Returns:
        Market depth data as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Build query based on parameters
            query = """
                SELECT timestamp, symbol, exchange, depth_level, bid_depth, 
                       ask_depth, bid_ask_ratio, interval
                FROM market_depth
                WHERE symbol = %s AND interval = %s
            """
            params = [symbol, interval]
            
            # Add exchange filter if specified
            if exchange:
                query += " AND exchange = %s"
                params.append(exchange)
            
            # Add depth level filter if specified
            if depth_level is not None:
                query += " AND depth_level = %s"
                params.append(depth_level)
            
            # Add ordering and limit
            query += " ORDER BY timestamp DESC, depth_level ASC LIMIT %s"
            params.append(limit)
            
            # Execute query
            cur.execute(query, params)
            
            results = cur.fetchall()
            if results:
                # Format response
                response = {
                    "symbol": symbol,
                    "exchange": exchange if exchange else "all",
                    "depth_level": depth_level,
                    "interval": interval,
                    "data": [dict(row) for row in results],
                    "count": len(results)
                }
                
                # Calculate average bid/ask ratio
                if depth_level is not None:
                    avg_bid_ask_ratio = sum(float(row["bid_ask_ratio"]) for row in results) / len(results)
                    response["average_bid_ask_ratio"] = avg_bid_ask_ratio
                
                # Convert to JSON string
                return json.dumps(response, cls=CustomJSONEncoder)
            
            return json.dumps({
                "symbol": symbol,
                "exchange": exchange if exchange else "all",
                "depth_level": depth_level,
                "interval": interval,
                "data": [],
                "count": 0
            })
    except Exception as e:
        logger.error(f"Error retrieving market depth: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_futures_basis(symbol: str, exchange: Optional[str] = None, 
                    contract_type: Optional[str] = None, 
                    interval: str = "1h", limit: int = 24) -> Union[str, None]:
    """
    Get futures basis data for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        exchange: Exchange name (or None for all exchanges)
        contract_type: Contract type (e.g., "quarterly", "perpetual")
        interval: Data interval (e.g., "1h", "4h")
        limit: Number of data points to retrieve
        
    Returns:
        Futures basis data as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Build query based on parameters
            query = """
                SELECT timestamp, symbol, exchange, contract_type, expiry_date, 
                       basis_points, annualized_basis, interval
                FROM futures_basis
                WHERE symbol = %s AND interval = %s
            """
            params = [symbol, interval]
            
            # Add exchange filter if specified
            if exchange:
                query += " AND exchange = %s"
                params.append(exchange)
            
            # Add contract type filter if specified
            if contract_type:
                query += " AND contract_type = %s"
                params.append(contract_type)
            
            # Add ordering and limit
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            # Execute query
            cur.execute(query, params)
            
            results = cur.fetchall()
            if results:
                # Format response
                response = {
                    "symbol": symbol,
                    "exchange": exchange if exchange else "all",
                    "contract_type": contract_type if contract_type else "all",
                    "interval": interval,
                    "data": [dict(row) for row in results],
                    "count": len(results)
                }
                
                # Calculate average basis
                avg_basis_points = sum(float(row["basis_points"]) for row in results) / len(results)
                avg_annualized_basis = sum(float(row["annualized_basis"]) for row in results) / len(results)
                
                response["average_basis_points"] = avg_basis_points
                response["average_annualized_basis"] = avg_annualized_basis
                
                # Add trend (increasing or decreasing)
                if len(results) > 1:
                    latest_basis = float(results[0]["basis_points"])
                    oldest_basis = float(results[-1]["basis_points"])
                    basis_change = latest_basis - oldest_basis
                    
                    response["basis_change"] = basis_change
                    response["basis_trend"] = "increasing" if basis_change > 0 else "decreasing" if basis_change < 0 else "stable"
                
                # Convert to JSON string
                return json.dumps(response, cls=CustomJSONEncoder)
            
            return json.dumps({
                "symbol": symbol,
                "exchange": exchange if exchange else "all",
                "contract_type": contract_type if contract_type else "all",
                "interval": interval,
                "data": [],
                "count": 0
            })
    except Exception as e:
        logger.error(f"Error retrieving futures basis: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_volume_profile(symbol: str, exchange: Optional[str] = None, 
                     time_period: str = "1d", 
                     interval: str = "1h", limit: int = 10) -> Union[str, None]:
    """
    Get volume profile data for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        exchange: Exchange name (or None for all exchanges)
        time_period: Time period for the volume profile (e.g., "1d", "1w")
        interval: Data interval (e.g., "1h")
        limit: Number of price levels to retrieve
        
    Returns:
        Volume profile data as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Build query based on parameters
            query = """
                SELECT timestamp, symbol, exchange, price_level, volume, 
                       is_buying, interval, time_period
                FROM volume_profile
                WHERE symbol = %s AND interval = %s AND time_period = %s
            """
            params = [symbol, interval, time_period]
            
            # Add exchange filter if specified
            if exchange:
                query += " AND exchange = %s"
                params.append(exchange)
            
            # Add ordering and limit
            query += " ORDER BY volume DESC LIMIT %s"
            params.append(limit)
            
            # Execute query
            cur.execute(query, params)
            
            results = cur.fetchall()
            if results:
                # Format response
                response = {
                    "symbol": symbol,
                    "exchange": exchange if exchange else "all",
                    "time_period": time_period,
                    "interval": interval,
                    "price_levels": [dict(row) for row in results],
                    "count": len(results)
                }
                
                # Find price level with highest volume (point of control)
                poc = max(results, key=lambda x: float(x["volume"]))
                response["point_of_control"] = {
                    "price_level": float(poc["price_level"]),
                    "volume": float(poc["volume"])
                }
                
                # Calculate buying vs selling volume
                buy_volume = sum(float(row["volume"]) for row in results if row["is_buying"])
                sell_volume = sum(float(row["volume"]) for row in results if not row["is_buying"])
                total_volume = buy_volume + sell_volume
                
                response["volume_distribution"] = {
                    "buy_volume": buy_volume,
                    "sell_volume": sell_volume,
                    "total_volume": total_volume,
                    "buy_percentage": (buy_volume / total_volume * 100) if total_volume > 0 else 0,
                    "sell_percentage": (sell_volume / total_volume * 100) if total_volume > 0 else 0
                }
                
                # Convert to JSON string
                return json.dumps(response, cls=CustomJSONEncoder)
            
            return json.dumps({
                "symbol": symbol,
                "exchange": exchange if exchange else "all",
                "time_period": time_period,
                "interval": interval,
                "price_levels": [],
                "count": 0
            })
    except Exception as e:
        logger.error(f"Error retrieving volume profile: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_liquidity_summary(symbol: str, exchange: Optional[str] = None, 
                         interval: str = "1d") -> Union[str, None]:
    """
    Get a comprehensive liquidity summary for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        exchange: Exchange name (or None for all exchanges)
        interval: Data interval (e.g., "1d")
        
    Returns:
        Liquidity summary as a JSON string or None if error
    """
    try:
        # Get latest exchange flow data
        exchange_flow_json = get_exchange_flows(symbol, exchange, interval, 1)
        exchange_flow = json.loads(exchange_flow_json) if exchange_flow_json else {"data": []}
        
        # Get funding rate data
        funding_rate_json = get_funding_rates(symbol, exchange, "8h", 3)
        funding_rate = json.loads(funding_rate_json) if funding_rate_json else {"data": []}
        
        # Get market depth data
        market_depth_json = get_market_depth(symbol, exchange, None, "5m", 1)
        market_depth = json.loads(market_depth_json) if market_depth_json else {"data": []}
        
        # Get futures basis data
        futures_basis_json = get_futures_basis(symbol, exchange, None, "1h", 1)
        futures_basis = json.loads(futures_basis_json) if futures_basis_json else {"data": []}
        
        # Compile summary
        summary = {
            "symbol": symbol,
            "exchange": exchange if exchange else "all",
            "timestamp": datetime.now().isoformat(),
            "liquidity_metrics": {}
        }
        
        # Add exchange flow metrics if available
        if exchange_flow and exchange_flow.get("data"):
            latest_flow = exchange_flow["data"][0]
            summary["liquidity_metrics"]["exchange_flow"] = {
                "timestamp": latest_flow.get("timestamp"),
                "inflow": latest_flow.get("inflow"),
                "outflow": latest_flow.get("outflow"),
                "net_flow": latest_flow.get("net_flow"),
                "flow_interpretation": "accumulation" if float(latest_flow.get("net_flow", 0)) < 0 else "distribution"
            }
        
        # Add funding rate metrics if available
        if funding_rate and funding_rate.get("data"):
            summary["liquidity_metrics"]["funding_rate"] = {
                "latest_rate": funding_rate.get("latest_funding_rate"),
                "average_rate": funding_rate.get("average_funding_rate"),
                "annualized_rate": funding_rate.get("annualized_rate"),
                "rate_interpretation": "bullish" if funding_rate.get("latest_funding_rate", 0) > 0 else "bearish"
            }
        
        # Add market depth metrics if available
        if market_depth and market_depth.get("data"):
            depth_data = []
            for row in market_depth.get("data", []):
                depth_data.append({
                    "depth_level": row.get("depth_level"),
                    "bid_depth": row.get("bid_depth"),
                    "ask_depth": row.get("ask_depth"),
                    "bid_ask_ratio": row.get("bid_ask_ratio")
                })
            
            if depth_data:
                # Calculate bid and ask imbalance
                total_bid = sum(float(row.get("bid_depth", 0)) for row in depth_data)
                total_ask = sum(float(row.get("ask_depth", 0)) for row in depth_data)
                
                summary["liquidity_metrics"]["market_depth"] = {
                    "timestamp": market_depth.get("data", [{}])[0].get("timestamp") if market_depth.get("data") else None,
                    "total_bid_depth": total_bid,
                    "total_ask_depth": total_ask,
                    "overall_bid_ask_ratio": total_bid / total_ask if total_ask > 0 else 0,
                    "depth_interpretation": "buy pressure" if total_bid > total_ask else "sell pressure" if total_bid < total_ask else "balanced"
                }
        
        # Add futures basis metrics if available
        if futures_basis and futures_basis.get("data"):
            latest_basis = futures_basis.get("data", [{}])[0]
            summary["liquidity_metrics"]["futures_basis"] = {
                "timestamp": latest_basis.get("timestamp"),
                "basis_points": latest_basis.get("basis_points"),
                "annualized_basis": latest_basis.get("annualized_basis"),
                "contract_type": latest_basis.get("contract_type"),
                "basis_interpretation": "bullish" if float(latest_basis.get("basis_points", 0)) > 0 else "bearish"
            }
        
        # Add overall liquidity interpretation
        bullish_signals = 0
        bearish_signals = 0
        
        # Count bullish/bearish signals from exchange flow
        if summary.get("liquidity_metrics", {}).get("exchange_flow", {}).get("flow_interpretation") == "accumulation":
            bullish_signals += 1
        elif summary.get("liquidity_metrics", {}).get("exchange_flow", {}).get("flow_interpretation") == "distribution":
            bearish_signals += 1
        
        # Count bullish/bearish signals from funding rate
        if summary.get("liquidity_metrics", {}).get("funding_rate", {}).get("rate_interpretation") == "bullish":
            bullish_signals += 1
        elif summary.get("liquidity_metrics", {}).get("funding_rate", {}).get("rate_interpretation") == "bearish":
            bearish_signals += 1
        
        # Count bullish/bearish signals from market depth
        if summary.get("liquidity_metrics", {}).get("market_depth", {}).get("depth_interpretation") == "buy pressure":
            bullish_signals += 1
        elif summary.get("liquidity_metrics", {}).get("market_depth", {}).get("depth_interpretation") == "sell pressure":
            bearish_signals += 1
        
        # Count bullish/bearish signals from futures basis
        if summary.get("liquidity_metrics", {}).get("futures_basis", {}).get("basis_interpretation") == "bullish":
            bullish_signals += 1
        elif summary.get("liquidity_metrics", {}).get("futures_basis", {}).get("basis_interpretation") == "bearish":
            bearish_signals += 1
        
        # Overall liquidity sentiment
        if bullish_signals > bearish_signals:
            liquidity_sentiment = "bullish"
        elif bearish_signals > bullish_signals:
            liquidity_sentiment = "bearish"
        else:
            liquidity_sentiment = "neutral"
        
        summary["overall_liquidity_sentiment"] = liquidity_sentiment
        summary["liquidity_signals"] = {
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
            "total_signals": bullish_signals + bearish_signals
        }
        
        # Convert to JSON string
        return json.dumps(summary, cls=CustomJSONEncoder)
    except Exception as e:
        logger.error(f"Error generating liquidity summary: {str(e)}")
        return None

# Functions to be added to DatabaseRetrievalTool class
# These will be used to extend the existing database retrieval tool
def get_tool_extension_functions():
    """
    Get functions to be added to the DatabaseRetrievalTool class.
    
    Returns:
        Dictionary of function names and implementations
    """
    return {
        "get_exchange_flows": get_exchange_flows,
        "get_funding_rates": get_funding_rates,
        "get_market_depth": get_market_depth,
        "get_futures_basis": get_futures_basis,
        "get_volume_profile": get_volume_profile,
        "get_liquidity_summary": get_liquidity_summary
    }
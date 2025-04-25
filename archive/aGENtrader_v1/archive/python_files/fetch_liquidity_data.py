#!/usr/bin/env python3
"""
Fetch Liquidity Data

This script fetches historical liquidity data from various APIs and stores it in the database.
The data sources include:
1. Exchange flows
2. Funding rates
3. Market depth
4. Futures basis
5. Volume profiles

The script supports both historical backfill and incremental updates.
"""

import os
import sys
import json
import time
import logging
import argparse
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union

import requests
import psycopg2
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define API configuration
# In a real implementation, these would be actual API endpoints with authentication
API_CONFIG = {
    "exchange_flows": {
        "url": "https://api.example.com/v1/exchange_flows",
        "key_param": "api_key",
        "symbol_param": "symbol",
        "exchange_param": "exchange",
        "interval_param": "interval",
        "limit_param": "limit"
    },
    "funding_rates": {
        "url": "https://api.example.com/v1/funding_rates",
        "key_param": "api_key",
        "symbol_param": "symbol",
        "exchange_param": "exchange",
        "interval_param": "interval",
        "limit_param": "limit"
    },
    "market_depth": {
        "url": "https://api.example.com/v1/market_depth",
        "key_param": "api_key",
        "symbol_param": "symbol",
        "exchange_param": "exchange",
        "interval_param": "interval",
        "limit_param": "limit"
    },
    "futures_basis": {
        "url": "https://api.example.com/v1/futures_basis",
        "key_param": "api_key",
        "symbol_param": "symbol",
        "exchange_param": "exchange",
        "interval_param": "interval",
        "limit_param": "limit"
    },
    "volume_profile": {
        "url": "https://api.example.com/v1/volume_profile",
        "key_param": "api_key",
        "symbol_param": "symbol",
        "exchange_param": "exchange",
        "interval_param": "interval",
        "limit_param": "limit"
    }
}

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Fetch and store liquidity data")
    
    parser.add_argument(
        "--data-type",
        type=str,
        choices=["exchange_flows", "funding_rates", "market_depth", "futures_basis", "volume_profile", "all"],
        default="all",
        help="Type of liquidity data to fetch (default: all)"
    )
    
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTCUSDT",
        help="Trading symbol (default: BTCUSDT)"
    )
    
    parser.add_argument(
        "--exchange",
        type=str,
        default="binance",
        help="Exchange name (default: binance)"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days of historical data to fetch (default: 30)"
    )
    
    parser.add_argument(
        "--interval",
        type=str,
        default="1d",
        help="Data interval (default: 1d)"
    )
    
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Perform historical backfill"
    )
    
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Simulate API calls with synthetic data (for testing)"
    )
    
    return parser.parse_args()

def get_database_connection():
    """Get a connection to the PostgreSQL database"""
    try:
        DATABASE_URL = os.environ.get("DATABASE_URL")
        if not DATABASE_URL:
            logger.error("DATABASE_URL environment variable not set")
            return None
        
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Use transactions
        logger.info(f"Connected to database {DATABASE_URL[:35]}...")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def fetch_exchange_flows(symbol: str, exchange: str, days: int, interval: str, simulate: bool) -> List[Dict[str, Any]]:
    """
    Fetch exchange flow data from API.
    
    Args:
        symbol: Trading symbol
        exchange: Exchange name
        days: Number of days of historical data
        interval: Data interval
        simulate: Whether to simulate API calls
        
    Returns:
        List of exchange flow data points
    """
    if simulate:
        # Generate simulated data for testing
        logger.info(f"Simulating exchange flow data for {symbol} on {exchange}")
        
        data = []
        now = datetime.now()
        
        for i in range(days):
            timestamp = now - timedelta(days=i)
            
            # Generate random but realistic values
            inflow = random.uniform(100, 10000)
            outflow = random.uniform(100, 10000)
            net_flow = inflow - outflow
            
            data.append({
                "timestamp": timestamp.isoformat(),
                "symbol": symbol,
                "exchange": exchange,
                "inflow": inflow,
                "outflow": outflow,
                "net_flow": net_flow,
                "interval": interval
            })
        
        return data
    else:
        # In a real implementation, this would make API calls to fetch actual data
        logger.warning("Real API integration not implemented. Use --simulate for testing.")
        return []

def fetch_funding_rates(symbol: str, exchange: str, days: int, interval: str, simulate: bool) -> List[Dict[str, Any]]:
    """
    Fetch funding rate data from API.
    
    Args:
        symbol: Trading symbol
        exchange: Exchange name
        days: Number of days of historical data
        interval: Data interval
        simulate: Whether to simulate API calls
        
    Returns:
        List of funding rate data points
    """
    if simulate:
        # Generate simulated data for testing
        logger.info(f"Simulating funding rate data for {symbol} on {exchange}")
        
        data = []
        now = datetime.now()
        
        # Funding interval is typically 8h
        actual_interval = "8h"
        hours_per_day = 24
        intervals_per_day = hours_per_day / 8
        total_intervals = int(days * intervals_per_day)
        
        for i in range(total_intervals):
            timestamp = now - timedelta(hours=i * 8)
            next_funding_time = timestamp + timedelta(hours=8)
            
            # Generate random but realistic values
            # Funding rates typically range from -0.1% to 0.1%
            funding_rate = random.uniform(-0.001, 0.001)
            predicted_rate = random.uniform(-0.001, 0.001)
            
            data.append({
                "timestamp": timestamp.isoformat(),
                "symbol": symbol,
                "exchange": exchange,
                "funding_rate": funding_rate,
                "next_funding_time": next_funding_time.isoformat(),
                "predicted_rate": predicted_rate,
                "interval": actual_interval
            })
        
        return data
    else:
        # In a real implementation, this would make API calls to fetch actual data
        logger.warning("Real API integration not implemented. Use --simulate for testing.")
        return []

def fetch_market_depth(symbol: str, exchange: str, days: int, interval: str, simulate: bool) -> List[Dict[str, Any]]:
    """
    Fetch market depth data from API.
    
    Args:
        symbol: Trading symbol
        exchange: Exchange name
        days: Number of days of historical data
        interval: Data interval
        simulate: Whether to simulate API calls
        
    Returns:
        List of market depth data points
    """
    if simulate:
        # Generate simulated data for testing
        logger.info(f"Simulating market depth data for {symbol} on {exchange}")
        
        data = []
        now = datetime.now()
        
        # Typical intervals for market depth are 5m or 15m
        actual_interval = "5m" if interval in ["1m", "5m"] else "15m"
        minutes_per_day = 24 * 60
        intervals_per_day = minutes_per_day / int(actual_interval.replace("m", ""))
        total_intervals = min(100, int(days * intervals_per_day))  # Limit to 100 data points for simulation
        
        # Define depth levels (typically percentages away from mid price)
        depth_levels = [0.1, 0.5, 1.0, 2.0, 5.0]
        
        for i in range(total_intervals):
            timestamp = now - timedelta(minutes=i * int(actual_interval.replace("m", "")))
            
            for depth_level in depth_levels:
                # Generate random but realistic values
                bid_depth = random.uniform(10, 100) * (6 - depth_level)  # More liquidity near the mid price
                ask_depth = random.uniform(10, 100) * (6 - depth_level)
                bid_ask_ratio = bid_depth / ask_depth if ask_depth > 0 else 1.0
                
                data.append({
                    "timestamp": timestamp.isoformat(),
                    "symbol": symbol,
                    "exchange": exchange,
                    "depth_level": depth_level,
                    "bid_depth": bid_depth,
                    "ask_depth": ask_depth,
                    "bid_ask_ratio": bid_ask_ratio,
                    "interval": actual_interval
                })
        
        return data
    else:
        # In a real implementation, this would make API calls to fetch actual data
        logger.warning("Real API integration not implemented. Use --simulate for testing.")
        return []

def fetch_futures_basis(symbol: str, exchange: str, days: int, interval: str, simulate: bool) -> List[Dict[str, Any]]:
    """
    Fetch futures basis data from API.
    
    Args:
        symbol: Trading symbol
        exchange: Exchange name
        days: Number of days of historical data
        interval: Data interval
        simulate: Whether to simulate API calls
        
    Returns:
        List of futures basis data points
    """
    if simulate:
        # Generate simulated data for testing
        logger.info(f"Simulating futures basis data for {symbol} on {exchange}")
        
        data = []
        now = datetime.now()
        
        # Define common futures contract types
        contract_types = ["quarterly", "bi-quarterly", "perpetual"]
        
        # Determine appropriate interval
        actual_interval = interval
        if interval == "1d":
            intervals_per_day = 1
        elif interval == "4h":
            intervals_per_day = 6
        elif interval == "1h":
            intervals_per_day = 24
        else:
            intervals_per_day = 24
            actual_interval = "1h"
        
        total_intervals = min(100, int(days * intervals_per_day))  # Limit to 100 data points for simulation
        
        for i in range(total_intervals):
            timestamp = now - timedelta(hours=i * (24 / intervals_per_day))
            
            for contract_type in contract_types:
                # Set expiry date for quarterly contracts
                expiry_date = None
                if contract_type == "quarterly":
                    # Last Friday of the quarter
                    quarter_end = datetime(timestamp.year, ((timestamp.month - 1) // 3 + 1) * 3 + 1, 1)
                    expiry_date = quarter_end - timedelta(days=1)
                    while expiry_date.weekday() != 4:  # 4 is Friday
                        expiry_date -= timedelta(days=1)
                elif contract_type == "bi-quarterly":
                    # Last Friday of the next quarter
                    quarter_end = datetime(timestamp.year, ((timestamp.month - 1) // 3 + 2) * 3 + 1, 1)
                    expiry_date = quarter_end - timedelta(days=1)
                    while expiry_date.weekday() != 4:  # 4 is Friday
                        expiry_date -= timedelta(days=1)
                
                # Generate random but realistic values
                if contract_type == "perpetual":
                    basis_points = random.uniform(-20, 20)  # Perpetuals tend to have smaller basis
                else:
                    basis_points = random.uniform(0, 200)  # Quarterly futures typically have a premium
                
                # Annualized basis depends on days to expiry
                annualized_basis = basis_points * 365 / 100  # Simplified calculation
                
                data.append({
                    "timestamp": timestamp.isoformat(),
                    "symbol": symbol,
                    "exchange": exchange,
                    "contract_type": contract_type,
                    "expiry_date": expiry_date.isoformat() if expiry_date else None,
                    "basis_points": basis_points,
                    "annualized_basis": annualized_basis,
                    "interval": actual_interval
                })
        
        return data
    else:
        # In a real implementation, this would make API calls to fetch actual data
        logger.warning("Real API integration not implemented. Use --simulate for testing.")
        return []

def fetch_volume_profile(symbol: str, exchange: str, days: int, interval: str, simulate: bool) -> List[Dict[str, Any]]:
    """
    Fetch volume profile data from API.
    
    Args:
        symbol: Trading symbol
        exchange: Exchange name
        days: Number of days of historical data
        interval: Data interval
        simulate: Whether to simulate API calls
        
    Returns:
        List of volume profile data points
    """
    if simulate:
        # Generate simulated data for testing
        logger.info(f"Simulating volume profile data for {symbol} on {exchange}")
        
        data = []
        now = datetime.now()
        
        # For volume profile, we need to define price levels
        # Assume current price is around 50000 for BTC
        current_price = 50000 if "BTC" in symbol else 2000 if "ETH" in symbol else 100
        
        # Define price levels as percentage deviations from current price
        price_deviations = [-5, -2, -1, -0.5, 0, 0.5, 1, 2, 5]
        
        # Define time periods for volume profiles
        time_periods = ["1d", "1w"]
        
        for time_period in time_periods:
            for i in range(min(7, days)):  # Limit to 7 days for simulation
                timestamp = now - timedelta(days=i)
                
                for deviation in price_deviations:
                    price_level = current_price * (1 + deviation / 100)
                    
                    # Volume tends to be highest near the current price
                    volume_multiplier = 1 - abs(deviation) / 10
                    volume = random.uniform(10, 1000) * volume_multiplier
                    
                    # 50% chance of being a buy vs sell
                    is_buying = random.random() > 0.5
                    
                    data.append({
                        "timestamp": timestamp.isoformat(),
                        "symbol": symbol,
                        "exchange": exchange,
                        "price_level": price_level,
                        "volume": volume,
                        "is_buying": is_buying,
                        "interval": interval,
                        "time_period": time_period
                    })
        
        return data
    else:
        # In a real implementation, this would make API calls to fetch actual data
        logger.warning("Real API integration not implemented. Use --simulate for testing.")
        return []

def store_exchange_flows(conn, data: List[Dict[str, Any]]) -> int:
    """
    Store exchange flow data in the database.
    
    Args:
        conn: Database connection
        data: List of exchange flow data points
        
    Returns:
        Number of records inserted
    """
    try:
        inserted = 0
        
        with conn.cursor() as cur:
            # Prepare data for insertion
            values = []
            for item in data:
                values.append((
                    item["timestamp"],
                    item["symbol"],
                    item["exchange"],
                    item["inflow"],
                    item["outflow"],
                    item["net_flow"],
                    item["interval"]
                ))
            
            # Insert data using execute_values for efficiency
            if values:
                execute_values(
                    cur,
                    """
                    INSERT INTO exchange_flows 
                    (timestamp, symbol, exchange, inflow, outflow, net_flow, interval)
                    VALUES %s
                    ON CONFLICT (timestamp, symbol, exchange, interval) DO NOTHING
                    """,
                    values
                )
                
                inserted = len(values)
        
        return inserted
    except Exception as e:
        logger.error(f"Error storing exchange flow data: {str(e)}")
        conn.rollback()
        return 0

def store_funding_rates(conn, data: List[Dict[str, Any]]) -> int:
    """
    Store funding rate data in the database.
    
    Args:
        conn: Database connection
        data: List of funding rate data points
        
    Returns:
        Number of records inserted
    """
    try:
        inserted = 0
        
        with conn.cursor() as cur:
            # Prepare data for insertion
            values = []
            for item in data:
                values.append((
                    item["timestamp"],
                    item["symbol"],
                    item["exchange"],
                    item["funding_rate"],
                    item["next_funding_time"],
                    item.get("predicted_rate"),
                    item["interval"]
                ))
            
            # Insert data using execute_values for efficiency
            if values:
                execute_values(
                    cur,
                    """
                    INSERT INTO funding_rates 
                    (timestamp, symbol, exchange, funding_rate, next_funding_time, predicted_rate, interval)
                    VALUES %s
                    ON CONFLICT (timestamp, symbol, exchange, interval) DO NOTHING
                    """,
                    values
                )
                
                inserted = len(values)
        
        return inserted
    except Exception as e:
        logger.error(f"Error storing funding rate data: {str(e)}")
        conn.rollback()
        return 0

def store_market_depth(conn, data: List[Dict[str, Any]]) -> int:
    """
    Store market depth data in the database.
    
    Args:
        conn: Database connection
        data: List of market depth data points
        
    Returns:
        Number of records inserted
    """
    try:
        inserted = 0
        
        with conn.cursor() as cur:
            # Prepare data for insertion
            values = []
            for item in data:
                values.append((
                    item["timestamp"],
                    item["symbol"],
                    item["exchange"],
                    item["depth_level"],
                    item["bid_depth"],
                    item["ask_depth"],
                    item["bid_ask_ratio"],
                    item["interval"]
                ))
            
            # Insert data using execute_values for efficiency
            if values:
                execute_values(
                    cur,
                    """
                    INSERT INTO market_depth 
                    (timestamp, symbol, exchange, depth_level, bid_depth, ask_depth, bid_ask_ratio, interval)
                    VALUES %s
                    ON CONFLICT (timestamp, symbol, exchange, depth_level, interval) DO NOTHING
                    """,
                    values
                )
                
                inserted = len(values)
        
        return inserted
    except Exception as e:
        logger.error(f"Error storing market depth data: {str(e)}")
        conn.rollback()
        return 0

def store_futures_basis(conn, data: List[Dict[str, Any]]) -> int:
    """
    Store futures basis data in the database.
    
    Args:
        conn: Database connection
        data: List of futures basis data points
        
    Returns:
        Number of records inserted
    """
    try:
        inserted = 0
        
        with conn.cursor() as cur:
            # Prepare data for insertion
            values = []
            for item in data:
                values.append((
                    item["timestamp"],
                    item["symbol"],
                    item["exchange"],
                    item["contract_type"],
                    item["expiry_date"],
                    item["basis_points"],
                    item["annualized_basis"],
                    item["interval"]
                ))
            
            # Insert data using execute_values for efficiency
            if values:
                execute_values(
                    cur,
                    """
                    INSERT INTO futures_basis 
                    (timestamp, symbol, exchange, contract_type, expiry_date, basis_points, annualized_basis, interval)
                    VALUES %s
                    ON CONFLICT (timestamp, symbol, exchange, contract_type, interval) DO NOTHING
                    """,
                    values
                )
                
                inserted = len(values)
        
        return inserted
    except Exception as e:
        logger.error(f"Error storing futures basis data: {str(e)}")
        conn.rollback()
        return 0

def store_volume_profile(conn, data: List[Dict[str, Any]]) -> int:
    """
    Store volume profile data in the database.
    
    Args:
        conn: Database connection
        data: List of volume profile data points
        
    Returns:
        Number of records inserted
    """
    try:
        inserted = 0
        
        with conn.cursor() as cur:
            # Prepare data for insertion
            values = []
            for item in data:
                values.append((
                    item["timestamp"],
                    item["symbol"],
                    item["exchange"],
                    item["price_level"],
                    item["volume"],
                    item["is_buying"],
                    item["interval"],
                    item["time_period"]
                ))
            
            # Insert data using execute_values for efficiency
            if values:
                execute_values(
                    cur,
                    """
                    INSERT INTO volume_profile 
                    (timestamp, symbol, exchange, price_level, volume, is_buying, interval, time_period)
                    VALUES %s
                    ON CONFLICT (timestamp, symbol, exchange, price_level, interval, time_period) DO NOTHING
                    """,
                    values
                )
                
                inserted = len(values)
        
        return inserted
    except Exception as e:
        logger.error(f"Error storing volume profile data: {str(e)}")
        conn.rollback()
        return 0

def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    logger.info(f"Fetching liquidity data for {args.symbol} on {args.exchange}")
    logger.info(f"Data type: {args.data_type}")
    logger.info(f"Days: {args.days}")
    logger.info(f"Interval: {args.interval}")
    logger.info(f"Backfill: {args.backfill}")
    logger.info(f"Simulate: {args.simulate}")
    
    # Connect to database
    conn = get_database_connection()
    if not conn:
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    try:
        # Process each data type
        data_types = ["exchange_flows", "funding_rates", "market_depth", "futures_basis", "volume_profile"]
        if args.data_type != "all":
            data_types = [args.data_type]
        
        for data_type in data_types:
            logger.info(f"Processing {data_type}...")
            
            # Fetch data
            if data_type == "exchange_flows":
                data = fetch_exchange_flows(args.symbol, args.exchange, args.days, args.interval, args.simulate)
                inserted = store_exchange_flows(conn, data)
            elif data_type == "funding_rates":
                data = fetch_funding_rates(args.symbol, args.exchange, args.days, args.interval, args.simulate)
                inserted = store_funding_rates(conn, data)
            elif data_type == "market_depth":
                data = fetch_market_depth(args.symbol, args.exchange, args.days, args.interval, args.simulate)
                inserted = store_market_depth(conn, data)
            elif data_type == "futures_basis":
                data = fetch_futures_basis(args.symbol, args.exchange, args.days, args.interval, args.simulate)
                inserted = store_futures_basis(conn, data)
            elif data_type == "volume_profile":
                data = fetch_volume_profile(args.symbol, args.exchange, args.days, args.interval, args.simulate)
                inserted = store_volume_profile(conn, data)
            
            logger.info(f"Inserted {inserted} {data_type} records")
        
        # Commit the transaction
        conn.commit()
        
        logger.info("Liquidity data fetch and store complete")
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
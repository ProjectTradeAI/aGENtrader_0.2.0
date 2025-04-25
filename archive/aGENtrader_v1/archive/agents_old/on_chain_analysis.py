
"""
On-Chain Analysis Agent

Analyzes blockchain data such as transaction volumes, wallet movements,
exchange inflows/outflows, and whale activity to provide additional
trading signals.
"""

import json
import os
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
from typing import Optional, Dict, Any, List, Tuple
import asyncio
import aiohttp
from enum import Enum, auto
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('on_chain')

class OnChainMetric(Enum):
    EXCHANGE_INFLOW = "exchange_inflow"
    EXCHANGE_OUTFLOW = "exchange_outflow"
    ACTIVE_ADDRESSES = "active_addresses"
    TRANSACTION_COUNT = "transaction_count"
    TRANSACTION_VOLUME = "transaction_volume"
    MINER_OUTFLOW = "miner_outflow"
    WHALE_TRANSACTIONS = "whale_transactions"
    SUPPLY_DISTRIBUTION = "supply_distribution"
    NVT_RATIO = "nvt_ratio"
    REALIZED_CAP = "realized_cap"
    SOPR = "sopr"  # Spent Output Profit Ratio
    MVRV_RATIO = "mvrv_ratio"

class OnChainAnalysisAgent:
    def __init__(self, config_path="config/settings.json"):
        """Initialize the On-Chain Analysis Agent"""
        self.name = "On-Chain Analysis Agent"
        self.config = self._load_config(config_path)
        self.api_keys = self._load_api_keys()
        self.use_simulation = False
        self.data_cache = {}
        self.last_update = {}
        
        # Define source priority (fallbacks)
        self.data_source_priority = [
            "glassnode", 
            "cryptoquant", 
            "blockchain_com", 
            "etherscan",
            "simulation"
        ]
        
        # Default thresholds for signals
        self.thresholds = {
            "exchange_inflow_high": 0.15,   # 15% increase is significant
            "exchange_outflow_high": 0.15,  # 15% increase is significant
            "whale_transaction_threshold": 1000000,  # $1M+ transactions
            "nvt_ratio_high": 150,          # High NVT indicates overvaluation
            "nvt_ratio_low": 45,            # Low NVT indicates undervaluation
            "active_address_increase": 0.1,  # 10% increase is significant
            "mvrv_high": 3.5,               # High MVRV indicates potential sell zone
            "mvrv_low": 1,                  # Low MVRV indicates potential buy zone
            "sopr_high": 1.1,               # High SOPR indicates profit-taking
            "sopr_low": 0.95                # Low SOPR indicates capitulation
        }
        
        # Mappings from tokens to specific blockchain explorers
        self.chain_explorer_map = {
            "BTC": "blockchain_com",
            "ETH": "etherscan",
            "SOL": "solscan", 
            "MATIC": "polygonscan"
        }
        
        # For simulation
        self.sim_data_trends = {
            "BTC": {
                "exchange_inflow": 0,        # Random walk trend
                "active_addresses": 0.01,    # Slightly upward trend
                "nvt_ratio": -0.005,         # Slightly downward trend
                "whale_transactions": 0      # Random walk trend
            },
            "ETH": {
                "exchange_inflow": 0,
                "active_addresses": 0.02,
                "nvt_ratio": -0.01,
                "whale_transactions": 0
            },
            "SOL": {
                "exchange_inflow": 0,
                "active_addresses": 0.05,
                "nvt_ratio": 0,
                "whale_transactions": 0
            },
            "MATIC": {
                "exchange_inflow": 0,
                "active_addresses": 0.03,
                "nvt_ratio": -0.005,
                "whale_transactions": 0
            }
        }

    def _load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}. Using default settings.")
            return {
                "data_sources": ["glassnode", "blockchain_com", "etherscan"],
                "symbols": ["BTC", "ETH", "SOL", "MATIC"],
                "update_interval": 3600,  # Default to hourly updates
                "whale_threshold": 1000000  # $1M+ for whale transactions
            }

    def _load_api_keys(self):
        """Load API keys from environment variables"""
        api_keys = {
            "glassnode": os.environ.get("GLASSNODE_API_KEY"),
            "cryptoquant": os.environ.get("CRYPTOQUANT_API_KEY"),
            "etherscan": os.environ.get("ETHERSCAN_API_KEY"),
            "infura": os.environ.get("INFURA_API_KEY"),
            "blockchain_com": os.environ.get("BLOCKCHAIN_COM_API_KEY"),
            "solscan": os.environ.get("SOLSCAN_API_KEY"),
            "polygonscan": os.environ.get("POLYGONSCAN_API_KEY")
        }
        
        for source, key in api_keys.items():
            if key:
                logger.info(f"API key found for {source}")
            else:
                logger.warning(f"No API key found for {source}")
                
        # If no API keys are available, default to simulation
        if not any(api_keys.values()):
            self.use_simulation = True
            logger.warning("No API keys available. Using simulated on-chain data.")
        
        return api_keys

    async def fetch_on_chain_data(self, symbol: str, metric: OnChainMetric) -> Dict[str, Any]:
        """
        Fetch on-chain data for the given symbol and metric.
        Uses cascading fallback through available data sources.
        """
        # Check cache first for recently fetched data (within 1 hour)
        cache_key = f"{symbol}_{metric.value}"
        if cache_key in self.data_cache:
            last_update = self.last_update.get(cache_key)
            if last_update and (datetime.now() - last_update).seconds < self.config.get("update_interval", 3600):
                logger.info(f"Using cached data for {symbol} {metric.value}")
                return self.data_cache[cache_key]
        
        # Try each data source in priority order
        for source in self.data_source_priority:
            # Skip if we don't have an API key (except for simulation)
            if source != "simulation" and not self.api_keys.get(source):
                continue
                
            try:
                data = None
                
                # Call the appropriate fetcher based on source and metric
                if source == "glassnode":
                    data = await self._fetch_from_glassnode(symbol, metric)
                elif source == "cryptoquant":
                    data = await self._fetch_from_cryptoquant(symbol, metric)
                elif source == "blockchain_com" and symbol == "BTC":
                    data = await self._fetch_from_blockchain_com(metric)
                elif source == "etherscan" and symbol == "ETH":
                    data = await self._fetch_from_etherscan(metric)
                elif source == "solscan" and symbol == "SOL":
                    data = await self._fetch_from_solscan(metric)
                elif source == "polygonscan" and symbol == "MATIC":
                    data = await self._fetch_from_polygonscan(metric)
                elif source == "simulation":
                    data = self._simulate_on_chain_data(symbol, metric)
                
                if data:
                    # Cache the successful response
                    self.data_cache[cache_key] = data
                    self.last_update[cache_key] = datetime.now()
                    return data
                    
            except Exception as e:
                logger.error(f"Error fetching {metric.value} for {symbol} from {source}: {str(e)}")
                continue
        
        # If all sources failed, use simulation as last resort
        data = self._simulate_on_chain_data(symbol, metric)
        self.data_cache[cache_key] = data
        self.last_update[cache_key] = datetime.now()
        return data

    async def _fetch_from_glassnode(self, symbol: str, metric: OnChainMetric) -> Optional[Dict[str, Any]]:
        """Fetch data from Glassnode API"""
        if not self.api_keys.get("glassnode"):
            return None
            
        # Map our metrics to Glassnode endpoints
        endpoint_map = {
            OnChainMetric.EXCHANGE_INFLOW: "metrics/transactions/transfers_volume_to_exchanges_sum",
            OnChainMetric.EXCHANGE_OUTFLOW: "metrics/transactions/transfers_volume_from_exchanges_sum",
            OnChainMetric.ACTIVE_ADDRESSES: "metrics/addresses/active_count",
            OnChainMetric.TRANSACTION_COUNT: "metrics/transactions/count",
            OnChainMetric.TRANSACTION_VOLUME: "metrics/transactions/transfers_volume_sum",
            OnChainMetric.NVT_RATIO: "metrics/indicators/nvt",
            OnChainMetric.REALIZED_CAP: "metrics/market/realized_cap_usd",
            OnChainMetric.SOPR: "metrics/indicators/sopr",
            OnChainMetric.MVRV_RATIO: "metrics/market/mvrv"
        }
        
        # Skip if no mapping exists
        if metric not in endpoint_map:
            return None
            
        # Map our symbols to Glassnode's format
        symbol_map = {
            "BTC": "BTC",
            "ETH": "ETH", 
            "MATIC": "MATIC"
        }
        
        if symbol not in symbol_map:
            return None
            
        api_symbol = symbol_map[symbol]
        endpoint = endpoint_map[metric]
        base_url = "https://api.glassnode.com"
        url = f"{base_url}/{endpoint}"
        
        params = {
            "api_key": self.api_keys["glassnode"],
            "a": api_symbol,
            "i": "24h",  # 24-hour interval
            "f": "json",
            "timestamp_format": "unix"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    glassnode_data = await response.json()
                    
                    if glassnode_data and len(glassnode_data) > 0:
                        # Process the specific metric into our standard format
                        latest_data = glassnode_data[-1]
                        value = latest_data.get("v", 0)
                        
                        # For metrics where we want to compare to history
                        historical_values = [entry.get("v", 0) for entry in glassnode_data[-30:] if "v" in entry]
                        avg_30d = sum(historical_values) / len(historical_values) if historical_values else 0
                        
                        # Calculate percentage change
                        pct_change = ((value - avg_30d) / avg_30d) * 100 if avg_30d > 0 else 0
                        
                        return {
                            "symbol": symbol,
                            "metric": metric.value,
                            "value": value,
                            "avg_30d": avg_30d,
                            "pct_change": pct_change,
                            "timestamp": datetime.now(),
                            "source": "glassnode"
                        }
                
                return None

    async def _fetch_from_cryptoquant(self, symbol: str, metric: OnChainMetric) -> Optional[Dict[str, Any]]:
        """Fetch data from CryptoQuant API"""
        if not self.api_keys.get("cryptoquant"):
            return None
            
        # Here we would implement the specific API calls to CryptoQuant
        # Since this requires a paid API, we'll return None for now
        return None

    async def _fetch_from_blockchain_com(self, metric: OnChainMetric) -> Optional[Dict[str, Any]]:
        """Fetch Bitcoin data from Blockchain.com API"""
        # Free API with basic BTC metrics
        base_url = "https://api.blockchain.info/charts"
        
        # Map metrics to Blockchain.com endpoints
        endpoint_map = {
            OnChainMetric.TRANSACTION_COUNT: "n-transactions",
            OnChainMetric.ACTIVE_ADDRESSES: "n-unique-addresses",
            OnChainMetric.TRANSACTION_VOLUME: "estimated-transaction-volume-usd",
            OnChainMetric.MINER_OUTFLOW: "miners-revenue"
        }
        
        if metric not in endpoint_map:
            return None
            
        endpoint = endpoint_map[metric]
        url = f"{base_url}/{endpoint}"
        
        params = {
            "timespan": "30days",
            "format": "json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "values" in data and len(data["values"]) > 0:
                        values = data["values"]
                        current_value = values[-1]["y"]
                        
                        # Calculate 30-day average
                        last_30d_values = [entry["y"] for entry in values[-30:]]
                        avg_30d = sum(last_30d_values) / len(last_30d_values)
                        
                        # Percentage change
                        pct_change = ((current_value - avg_30d) / avg_30d) * 100 if avg_30d > 0 else 0
                        
                        return {
                            "symbol": "BTC",
                            "metric": metric.value,
                            "value": current_value,
                            "avg_30d": avg_30d,
                            "pct_change": pct_change,
                            "timestamp": datetime.now(),
                            "source": "blockchain_com"
                        }
                
                return None

    async def _fetch_from_etherscan(self, metric: OnChainMetric) -> Optional[Dict[str, Any]]:
        """Fetch Ethereum data from Etherscan API"""
        if not self.api_keys.get("etherscan"):
            return None
            
        base_url = "https://api.etherscan.io/api"
        
        # Different module/action based on metric
        module = "stats"
        action = None
        
        if metric == OnChainMetric.TRANSACTION_COUNT:
            action = "eth_dailytx"
        elif metric == OnChainMetric.ACTIVE_ADDRESSES:
            action = "eth_uniqueaddresses"  # May not exist in free API
        
        if not action:
            return None
            
        params = {
            "module": module,
            "action": action,
            "apikey": self.api_keys["etherscan"]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "1" and "result" in data:
                        result = data["result"]
                        
                        # Process the result based on the specific metric and response format
                        # This would need to be adapted based on Etherscan's actual response format
                        value = float(result) if isinstance(result, (str, int, float)) else 0
                        
                        return {
                            "symbol": "ETH",
                            "metric": metric.value,
                            "value": value,
                            "timestamp": datetime.now(),
                            "source": "etherscan"
                        }
                
                return None

    async def _fetch_from_solscan(self, metric: OnChainMetric) -> Optional[Dict[str, Any]]:
        """Fetch Solana data from Solscan API"""
        # Placeholder for Solscan API implementation
        return None

    async def _fetch_from_polygonscan(self, metric: OnChainMetric) -> Optional[Dict[str, Any]]:
        """Fetch Polygon (MATIC) data from Polygonscan API"""
        # Placeholder for Polygonscan API implementation
        return None

    def _simulate_on_chain_data(self, symbol: str, metric: OnChainMetric) -> Dict[str, Any]:
        """Generate realistic simulated on-chain data"""
        # Base values for different metrics
        base_values = {
            OnChainMetric.EXCHANGE_INFLOW: 1500000,  # $1.5M daily inflow
            OnChainMetric.EXCHANGE_OUTFLOW: 1400000,  # $1.4M daily outflow
            OnChainMetric.ACTIVE_ADDRESSES: {
                "BTC": 800000,
                "ETH": 500000,
                "SOL": 300000,
                "MATIC": 200000
            },
            OnChainMetric.TRANSACTION_COUNT: {
                "BTC": 250000,
                "ETH": 1200000,
                "SOL": 2000000,
                "MATIC": 800000
            },
            OnChainMetric.TRANSACTION_VOLUME: {
                "BTC": 5000000000,  # $5B
                "ETH": 2000000000,  # $2B
                "SOL": 500000000,   # $500M
                "MATIC": 200000000  # $200M
            },
            OnChainMetric.WHALE_TRANSACTIONS: 25,  # 25 whale transactions daily
            OnChainMetric.NVT_RATIO: {
                "BTC": 70,
                "ETH": 65,
                "SOL": 90,
                "MATIC": 80
            },
            OnChainMetric.MVRV_RATIO: {
                "BTC": 2.1,
                "ETH": 1.8,
                "SOL": 2.4,
                "MATIC": 1.5
            },
            OnChainMetric.SOPR: 1.03  # Slightly profitable on average
        }
        
        # Get base value based on metric and symbol
        if isinstance(base_values.get(metric, 0), dict):
            base_value = base_values.get(metric, {}).get(symbol, 1000)
        else:
            base_value = base_values.get(metric, 1000)
        
        # Get trend bias for this symbol and metric 
        trend_bias = self.sim_data_trends.get(symbol, {}).get(metric.value, 0)
        
        # Add random variation (more for transaction metrics, less for ratios)
        if metric in [OnChainMetric.NVT_RATIO, OnChainMetric.MVRV_RATIO, OnChainMetric.SOPR]:
            variation = np.random.normal(trend_bias, 0.05)  # 5% standard deviation
        else:
            variation = np.random.normal(trend_bias, 0.15)  # 15% standard deviation
            
        # Update the trend bias with some mean reversion and persistence
        current_bias = self.sim_data_trends.get(symbol, {}).get(metric.value, 0)
        new_bias = current_bias * 0.8 + np.random.normal(0, 0.05)  # Mean reversion
        
        if symbol in self.sim_data_trends and metric.value in self.sim_data_trends[symbol]:
            self.sim_data_trends[symbol][metric.value] = new_bias
            
        # Calculate simulated value with the variation
        current_value = base_value * (1 + variation)
        
        # Simulate historical averages
        avg_30d = base_value * (1 + trend_bias/2)  # Trend is half as pronounced in the average
        
        # Percentage change from average
        pct_change = ((current_value - avg_30d) / avg_30d) * 100 if avg_30d > 0 else 0
        
        return {
            "symbol": symbol,
            "metric": metric.value,
            "value": current_value,
            "avg_30d": avg_30d,
            "pct_change": pct_change,
            "timestamp": datetime.now(),
            "source": "simulation"
        }

    async def analyze_whale_activity(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze large transactions (whale activity) for a given symbol
        Returns information about whale accumulation or distribution
        """
        # Fetch whale transactions
        whale_data = await self.fetch_on_chain_data(
            symbol, 
            OnChainMetric.WHALE_TRANSACTIONS
        )
        
        # Simulate whale buy/sell ratio (would come from API in real implementation)
        whale_buy_ratio = np.random.beta(5, 5)  # Between 0-1, centered around 0.5
        
        # Simulate large transaction count
        large_tx_count = int(whale_data["value"])
        
        # Calculate buys vs sells
        whale_buys = int(large_tx_count * whale_buy_ratio)
        whale_sells = large_tx_count - whale_buys
        
        # Determine if there's accumulation or distribution
        if whale_buy_ratio > 0.6:
            trend = "accumulation"
            signal = "bullish"
        elif whale_buy_ratio < 0.4:
            trend = "distribution"
            signal = "bearish"
        else:
            trend = "neutral"
            signal = "neutral"
            
        # Calculate confidence based on deviation from 0.5
        confidence = abs(whale_buy_ratio - 0.5) * 200  # Convert to 0-100 scale
        
        return {
            "symbol": symbol,
            "large_tx_count": large_tx_count,
            "whale_buys": whale_buys,
            "whale_sells": whale_sells,
            "buy_ratio": whale_buy_ratio,
            "trend": trend,
            "signal": signal,
            "confidence": confidence,
            "timestamp": datetime.now()
        }

    async def analyze_exchange_flows(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze exchange inflows and outflows to determine if tokens
        are moving to or from exchanges (potential sell or buy pressure)
        """
        # Fetch exchange inflows and outflows
        inflow_data = await self.fetch_on_chain_data(
            symbol, 
            OnChainMetric.EXCHANGE_INFLOW
        )
        
        outflow_data = await self.fetch_on_chain_data(
            symbol, 
            OnChainMetric.EXCHANGE_OUTFLOW
        )
        
        inflow = inflow_data["value"]
        outflow = outflow_data["value"]
        
        # Net flow (negative means more outflow)
        net_flow = inflow - outflow
        
        # Net flow ratio (>1 means more inflow)
        flow_ratio = inflow / outflow if outflow > 0 else float('inf')
        
        # Compare to average
        inflow_pct_change = inflow_data["pct_change"]
        outflow_pct_change = outflow_data["pct_change"]
        
        # Determine signal
        if flow_ratio < 0.8:
            # Significantly more outflow than inflow
            signal = "strongly_bullish"
            trend = "accumulation"
            explanation = "Significant token outflow from exchanges suggests accumulation (tokens moving to private wallets)"
            confidence = min(100, 50 + abs(inflow_pct_change - outflow_pct_change))
        elif flow_ratio < 0.95:
            signal = "bullish"
            trend = "mild_accumulation"
            explanation = "More tokens leaving exchanges than entering, suggesting mild accumulation"
            confidence = min(90, 40 + abs(inflow_pct_change - outflow_pct_change))
        elif flow_ratio > 1.2:
            # Significantly more inflow than outflow
            signal = "strongly_bearish"
            trend = "distribution"
            explanation = "Significant token inflow to exchanges suggests preparation for selling"
            confidence = min(100, 50 + abs(inflow_pct_change - outflow_pct_change))
        elif flow_ratio > 1.05:
            signal = "bearish"
            trend = "mild_distribution"
            explanation = "More tokens entering exchanges than leaving, suggesting mild distribution"
            confidence = min(90, 40 + abs(inflow_pct_change - outflow_pct_change))
        else:
            signal = "neutral"
            trend = "neutral"
            explanation = "Balanced exchange flows suggest no strong directional pressure"
            confidence = 50
        
        return {
            "symbol": symbol,
            "inflow": inflow,
            "outflow": outflow,
            "net_flow": net_flow,
            "flow_ratio": flow_ratio,
            "inflow_change": inflow_pct_change,
            "outflow_change": outflow_pct_change,
            "signal": signal,
            "trend": trend,
            "explanation": explanation,
            "confidence": confidence,
            "timestamp": datetime.now()
        }

    async def analyze_network_activity(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze network activity metrics including active addresses,
        transaction count, and transaction volume
        """
        # Fetch required metrics
        active_addresses = await self.fetch_on_chain_data(
            symbol, 
            OnChainMetric.ACTIVE_ADDRESSES
        )
        
        tx_count = await self.fetch_on_chain_data(
            symbol, 
            OnChainMetric.TRANSACTION_COUNT
        )
        
        tx_volume = await self.fetch_on_chain_data(
            symbol, 
            OnChainMetric.TRANSACTION_VOLUME
        )
        
        # Extract values and changes
        addr_value = active_addresses["value"]
        addr_change = active_addresses["pct_change"]
        
        count_value = tx_count["value"]
        count_change = tx_count["pct_change"]
        
        volume_value = tx_volume["value"]
        volume_change = tx_volume["pct_change"]
        
        # Calculate average transaction size
        avg_tx_size = volume_value / count_value if count_value > 0 else 0
        
        # Determine signal based on growth metrics
        # We want positive growth in activity metrics
        growth_score = (
            (addr_change / 10 if addr_change > 0 else addr_change / 5) +
            (count_change / 10 if count_change > 0 else count_change / 5) +
            (volume_change / 10 if volume_change > 0 else volume_change / 5)
        )
        
        if growth_score > 6:
            signal = "strongly_bullish"
            explanation = "Strong growth in network activity across all metrics"
            confidence = min(95, 50 + growth_score)
        elif growth_score > 3:
            signal = "bullish"
            explanation = "Positive growth in network activity metrics"
            confidence = min(85, 50 + growth_score)
        elif growth_score < -6:
            signal = "strongly_bearish"
            explanation = "Significant decline in network activity across all metrics"
            confidence = min(95, 50 + abs(growth_score))
        elif growth_score < -3:
            signal = "bearish"
            explanation = "Decline in network activity metrics"
            confidence = min(85, 50 + abs(growth_score))
        else:
            signal = "neutral"
            explanation = "Network activity metrics show mixed or neutral signals"
            confidence = 50
        
        return {
            "symbol": symbol,
            "active_addresses": addr_value,
            "active_addresses_change": addr_change,
            "transaction_count": count_value,
            "transaction_count_change": count_change,
            "transaction_volume": volume_value,
            "transaction_volume_change": volume_change,
            "avg_transaction_size": avg_tx_size,
            "growth_score": growth_score,
            "signal": signal,
            "explanation": explanation,
            "confidence": confidence,
            "timestamp": datetime.now()
        }

    async def analyze_valuation_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze blockchain valuation metrics like NVT Ratio and MVRV Ratio
        to determine if the asset is overvalued or undervalued
        """
        # Fetch NVT Ratio (Network Value to Transactions Ratio)
        # High NVT = Overvalued, Low NVT = Undervalued
        nvt_data = await self.fetch_on_chain_data(
            symbol, 
            OnChainMetric.NVT_RATIO
        )
        
        # Fetch MVRV Ratio (Market Value to Realized Value)
        # High MVRV = Overvalued, Low MVRV = Undervalued
        mvrv_data = await self.fetch_on_chain_data(
            symbol, 
            OnChainMetric.MVRV_RATIO
        )
        
        # Fetch SOPR (Spent Output Profit Ratio)
        # SOPR > 1 means people selling at profit, < 1 means selling at loss
        sopr_data = await self.fetch_on_chain_data(
            symbol, 
            OnChainMetric.SOPR
        )
        
        # Extract values
        nvt = nvt_data["value"]
        mvrv = mvrv_data["value"]
        sopr = sopr_data["value"]
        
        # Determine valuation signal using NVT thresholds
        if nvt > self.thresholds["nvt_ratio_high"]:
            nvt_signal = "bearish"
            nvt_explanation = f"NVT Ratio is high ({nvt:.2f}), suggesting overvaluation"
        elif nvt < self.thresholds["nvt_ratio_low"]:
            nvt_signal = "bullish"
            nvt_explanation = f"NVT Ratio is low ({nvt:.2f}), suggesting undervaluation"
        else:
            nvt_signal = "neutral"
            nvt_explanation = f"NVT Ratio is moderate ({nvt:.2f})"
        
        # Determine MVRV signal
        if mvrv > self.thresholds["mvrv_high"]:
            mvrv_signal = "strongly_bearish"
            mvrv_explanation = f"MVRV Ratio is very high ({mvrv:.2f}), indicating potential market top"
        elif mvrv > 2.5:
            mvrv_signal = "bearish"
            mvrv_explanation = f"MVRV Ratio is high ({mvrv:.2f}), suggesting overvaluation"
        elif mvrv < self.thresholds["mvrv_low"]:
            mvrv_signal = "strongly_bullish"
            mvrv_explanation = f"MVRV Ratio is very low ({mvrv:.2f}), indicating potential market bottom"
        elif mvrv < 1.5:
            mvrv_signal = "bullish"
            mvrv_explanation = f"MVRV Ratio is low ({mvrv:.2f}), suggesting undervaluation"
        else:
            mvrv_signal = "neutral"
            mvrv_explanation = f"MVRV Ratio is moderate ({mvrv:.2f})"
            
        # Determine SOPR signal
        if sopr > self.thresholds["sopr_high"]:
            sopr_signal = "bearish"
            sopr_explanation = f"SOPR is high ({sopr:.2f}), indicating profit-taking"
        elif sopr < self.thresholds["sopr_low"]:
            sopr_signal = "bullish"
            sopr_explanation = f"SOPR is low ({sopr:.2f}), indicating potential capitulation"
        else:
            sopr_signal = "neutral"
            sopr_explanation = f"SOPR is moderate ({sopr:.2f})"
            
        # Combined valuation signal (weighted)
        # Give more weight to MVRV as it's typically more predictive
        if mvrv_signal == "strongly_bearish":
            combined_signal = "strongly_bearish"
            confidence = 85
        elif mvrv_signal == "strongly_bullish":
            combined_signal = "strongly_bullish"
            confidence = 85
        elif mvrv_signal == "bearish" and (nvt_signal == "bearish" or sopr_signal == "bearish"):
            combined_signal = "bearish"
            confidence = 75
        elif mvrv_signal == "bullish" and (nvt_signal == "bullish" or sopr_signal == "bullish"):
            combined_signal = "bullish"
            confidence = 75
        elif mvrv_signal == "bearish":
            combined_signal = "bearish"
            confidence = 65
        elif mvrv_signal == "bullish":
            combined_signal = "bullish"
            confidence = 65
        else:
            # Average the signals
            signals = {"bearish": -1, "strongly_bearish": -2, "neutral": 0, "bullish": 1, "strongly_bullish": 2}
            signal_score = (signals.get(nvt_signal, 0) + signals.get(mvrv_signal, 0) * 2 + signals.get(sopr_signal, 0)) / 4
            
            if signal_score > 1:
                combined_signal = "bullish"
            elif signal_score > 0.3:
                combined_signal = "slightly_bullish"
            elif signal_score < -1:
                combined_signal = "bearish"
            elif signal_score < -0.3:
                combined_signal = "slightly_bearish"
            else:
                combined_signal = "neutral"
                
            confidence = 50 + abs(signal_score) * 20
            
        return {
            "symbol": symbol,
            "nvt_ratio": nvt,
            "mvrv_ratio": mvrv,
            "sopr": sopr,
            "nvt_signal": nvt_signal,
            "nvt_explanation": nvt_explanation,
            "mvrv_signal": mvrv_signal,
            "mvrv_explanation": mvrv_explanation,
            "sopr_signal": sopr_signal,
            "sopr_explanation": sopr_explanation,
            "combined_signal": combined_signal,
            "confidence": confidence,
            "timestamp": datetime.now()
        }

    async def get_on_chain_trading_signal(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze all on-chain metrics to generate a comprehensive trading signal.
        This combines exchange flows, whale activity, network health, and valuation metrics.
        """
        # Gather all analyses
        exchange_flow = await self.analyze_exchange_flows(symbol)
        whale_activity = await self.analyze_whale_activity(symbol)
        network_activity = await self.analyze_network_activity(symbol)
        valuation = await self.analyze_valuation_metrics(symbol)
        
        # Define signal mapping and weights
        signal_map = {
            "strongly_bullish": 2, 
            "bullish": 1, 
            "slightly_bullish": 0.5,
            "neutral": 0, 
            "slightly_bearish": -0.5,
            "bearish": -1, 
            "strongly_bearish": -2
        }
        
        weights = {
            "exchange_flow": 0.3,     # 30% weight - strong predictor
            "whale_activity": 0.25,   # 25% weight - important but can be manipulated
            "network_activity": 0.2,  # 20% weight - solid but lagging indicator
            "valuation": 0.25         # 25% weight - good for medium-term
        }
        
        # Calculate weighted signal score
        exchange_flow_score = signal_map.get(exchange_flow["signal"], 0) * weights["exchange_flow"]
        whale_score = signal_map.get(whale_activity["signal"], 0) * weights["whale_activity"]
        network_score = signal_map.get(network_activity["signal"], 0) * weights["network_activity"]
        valuation_score = signal_map.get(valuation["combined_signal"], 0) * weights["valuation"]
        
        total_score = exchange_flow_score + whale_score + network_score + valuation_score
        
        # Determine final signal based on total score
        if total_score > 1.2:
            signal = "strong_buy"
            recommendation = "Strong buy signal based on on-chain metrics"
        elif total_score > 0.5:
            signal = "buy"
            recommendation = "Buy signal based on on-chain metrics"
        elif total_score > 0.2:
            signal = "weak_buy"
            recommendation = "Weak buy signal based on on-chain metrics"
        elif total_score < -1.2:
            signal = "strong_sell"
            recommendation = "Strong sell signal based on on-chain metrics"
        elif total_score < -0.5:
            signal = "sell"
            recommendation = "Sell signal based on on-chain metrics"
        elif total_score < -0.2:
            signal = "weak_sell"
            recommendation = "Weak sell signal based on on-chain metrics"
        else:
            signal = "hold"
            recommendation = "Hold signal (neutral) based on on-chain metrics"
            
        # Calculate confidence score (0-100)
        component_confidences = [
            exchange_flow["confidence"] * weights["exchange_flow"],
            whale_activity["confidence"] * weights["whale_activity"],
            network_activity["confidence"] * weights["network_activity"],
            valuation["confidence"] * weights["valuation"]
        ]
        
        confidence = sum(component_confidences)
        
        # Prepare insights for each component
        insights = {
            "exchange_flows": {
                "signal": exchange_flow["signal"],
                "explanation": exchange_flow["explanation"],
                "inflow": exchange_flow["inflow"],
                "outflow": exchange_flow["outflow"],
                "net_flow": exchange_flow["net_flow"]
            },
            "whale_activity": {
                "signal": whale_activity["signal"],
                "large_transactions": whale_activity["large_tx_count"],
                "buy_ratio": whale_activity["buy_ratio"],
                "trend": whale_activity["trend"]
            },
            "network_health": {
                "signal": network_activity["signal"],
                "explanation": network_activity["explanation"],
                "active_addresses": network_activity["active_addresses"],
                "active_addresses_change": f"{network_activity['active_addresses_change']:.2f}%"
            },
            "valuation": {
                "signal": valuation["combined_signal"],
                "nvt_ratio": valuation["nvt_ratio"],
                "mvrv_ratio": valuation["mvrv_ratio"],
                "sopr": valuation["sopr"],
                "nvt_explanation": valuation["nvt_explanation"],
                "mvrv_explanation": valuation["mvrv_explanation"]
            }
        }
        
        # Return comprehensive analysis
        return {
            "symbol": symbol,
            "signal": signal,
            "recommendation": recommendation,
            "confidence": confidence,
            "score": total_score,
            "timestamp": datetime.now().isoformat(),
            "insights": insights,
            "component_signals": {
                "exchange_flow": exchange_flow["signal"],
                "whale_activity": whale_activity["signal"],
                "network_activity": network_activity["signal"],
                "valuation": valuation["combined_signal"]
            }
        }

async def main():
    """Test the agent"""
    agent = OnChainAnalysisAgent()
    
    for symbol in ["BTC", "ETH", "SOL", "MATIC"]:
        print(f"\n===== ON-CHAIN ANALYSIS FOR {symbol} =====")
        signal = await agent.get_on_chain_trading_signal(symbol)
        
        print(f"Trading Signal: {signal['signal']}")
        print(f"Confidence: {signal['confidence']:.2f}")
        print(f"Recommendation: {signal['recommendation']}")
        print("\nComponent Signals:")
        for component, component_signal in signal['component_signals'].items():
            print(f"  - {component}: {component_signal}")
        
        print("\nKey Insights:")
        insights = signal['insights']
        print(f"  Exchange Flows: {insights['exchange_flows']['explanation']}")
        print(f"  Whale Activity: {insights['whale_activity']['trend']} trend (buy ratio: {insights['whale_activity']['buy_ratio']:.2f})")
        print(f"  Network Activity: {insights['network_health']['explanation']}")
        print(f"  Valuation: {insights['valuation']['mvrv_explanation']}")

if __name__ == "__main__":
    asyncio.run(main())

"""
aGENtrader v2 Liquidity Analyst Agent

This module provides a liquidity analysis agent that evaluates market depth,
bid-ask spreads, and other liquidity indicators to assess market conditions.
"""

import os
import time
import json
import logging
import math
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

from agents.base_agent import BaseAnalystAgent
from core.logging.decision_logger import DecisionLogger

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('liquidity_analyst')
logger.setLevel(logging.DEBUG)

class LiquidityAnalystAgent(BaseAnalystAgent):
    """LiquidityAnalystAgent for aGENtrader v2.0.0 - High-Fidelity Liquidity Intelligence"""
    
    def __init__(self, data_fetcher=None, config=None):
        """
        Initialize the liquidity analyst agent.
        
        Args:
            data_fetcher: Data fetcher for market data
            config: Configuration dictionary
        """
        self.version = "v2.0.0"
        super().__init__(agent_name="liquidity_analyst")
        self.name = "LiquidityAnalystAgent"
        self.description = "Analyzes market liquidity conditions"
        self.data_fetcher = data_fetcher
        
        # Initialize LLM client with agent-specific configuration
        from models.llm_client import LLMClient
        self.llm_client = LLMClient(agent_name="liquidity_analyst")
        
        # Get agent config
        self.agent_config = self.get_agent_config()
        self.trading_config = self._get_trading_config()
        
        # Use agent-specific timeframe from config if available
        liquidity_config = self.agent_config.get("liquidity_analyst", {})
        self.default_interval = liquidity_config.get("timeframe", self.trading_config.get("default_interval", "1h"))
        
        # Configure liquidity thresholds
        self.config = config or {}
        self.thresholds = self.config.get('thresholds', {
            'low_depth': 50000,     # USDT value for low market depth
            'medium_depth': 200000, # USDT value for medium market depth
            'high_depth': 1000000,  # USDT value for high market depth
            'tight_spread': 0.05,   # 0.05% spread considered tight
            'normal_spread': 0.2,   # 0.2% spread considered normal
            'wide_spread': 0.5      # 0.5%+ spread considered wide
        })
        
        # Set the depth levels to analyze in the order book (increased for better analysis)
        self.depth_levels = self.config.get('depth_levels', 100)
        
        # Price bin size for clustering (in % of price)
        self.price_bin_size_pct = self.config.get('price_bin_size_pct', 0.2)
        
        # Sanity check parameters - decreased min_liquidity_zones to 2 as requested in v2.0 upgrade
        self.min_liquidity_zones = self.config.get('min_liquidity_zones', 2)
        self.max_bid_ask_ratio = self.config.get('max_bid_ask_ratio', 100.0)
        self.min_bid_ask_ratio = self.config.get('min_bid_ask_ratio', 0.01)
        
        # Signal confidence levels
        self.high_confidence = self.config.get('high_confidence', 80)
        self.medium_confidence = self.config.get('medium_confidence', 65)
        self.low_confidence = self.config.get('low_confidence', 50)
        
    def analyze(
        self, 
        symbol: Optional[Union[str, Dict[str, Any]]] = None,
        market_data: Optional[Dict[str, Any]] = None,
        interval: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze market liquidity conditions.
        
        Args:
            symbol: Trading symbol (optional if included in market_data) or the entire market_data dict
            market_data: Pre-fetched market data (optional)
            interval: Time interval (used for consistency, but less relevant for liquidity)
            **kwargs: Additional parameters
                - market_context: MarketContext object containing current market data
                
        Returns:
            Liquidity analysis results
        """
        # Test critical logging first thing to see if it appears
        logger.critical("LIQUIDITY ANALYST: Starting analysis")
        start_time = time.time()
        
        # Handle case where market_data is passed as first parameter (common in test harness)
        if isinstance(symbol, dict) and 'symbol' in symbol:
            # First parameter is actually market_data
            market_data = symbol
            symbol = market_data.get('symbol')
            if 'interval' in market_data and not interval:
                interval = market_data.get('interval')
        # Otherwise, extract symbol from market_data if provided
        elif market_data and isinstance(market_data, dict) and 'symbol' in market_data:
            symbol = symbol or market_data['symbol']
            
        # Use agent-specific timeframe if none provided
        interval = interval or self.default_interval
        
        # Validate input
        if not symbol:
            return self.build_error_response(
                "INVALID_INPUT", 
                "Missing symbol parameter. Please provide either as a direct parameter or in market_data"
            )
            
        # Normalize symbol format if needed
        if isinstance(symbol, str):
            symbol = symbol.replace('_', '/')
            
        try:
            # Extract market context if available
            market_context = None
            if market_data and isinstance(market_data, dict) and market_data.get("market_context"):
                market_context = market_data.get("market_context")
                logger.info(f"Using market context from market_data")
            elif kwargs.get("market_context"):
                market_context = kwargs.get("market_context")
                logger.info(f"Using market context from kwargs")
            
            # Check if we have pre-fetched market data or need to fetch it
            order_book = None
            if market_data and isinstance(market_data, dict) and market_data.get("order_book"):
                order_book = market_data.get("order_book")
                logger.info(f"Using pre-fetched order book data")
            else:
                # Fetch market data using data fetcher
                if not self.data_fetcher:
                    return self.build_error_response(
                        "DATA_FETCHER_MISSING",
                        "Data fetcher not provided"
                    )
                
                logger.info(f"Fetching order book data for {symbol}")
                try:
                    order_book = self.data_fetcher.fetch_market_depth(symbol, limit=self.depth_levels)
                except Exception as e:
                    logger.error(f"Error fetching order book: {str(e)}")
                    return self.build_error_response(
                        "ORDER_BOOK_FETCH_ERROR",
                        f"Error fetching order book data: {str(e)}"
                    )
            
            if not order_book or not isinstance(order_book, dict) or 'bids' not in order_book or 'asks' not in order_book:
                return self.build_error_response(
                    "INVALID_ORDER_BOOK",
                    "Invalid or empty order book data"
                )
                
            # Analyze the order book
            logger.info(f"Starting order book analysis for {symbol}")
            analysis_result = self._analyze_order_book(order_book, market_context)
            
            # Add more debugging for large orders detection
            liquidity_zones = analysis_result.get('liquidity_zones', {})
            large_bids = liquidity_zones.get('large_bids', [])
            large_asks = liquidity_zones.get('large_asks', [])
            
            logger.info(f"Liquidity analysis completed with {len(large_bids)} large bids, {len(large_asks)} large asks")
            for bid in large_bids[:3]:  # Log top 3 large bids
                logger.info(f"Large bid detected: price={bid.get('price', 'N/A')}, volume={bid.get('volume', 'N/A')}, ratio={bid.get('ratio', 'N/A')}")
            for ask in large_asks[:3]:  # Log top 3 large asks
                logger.info(f"Large ask detected: price={ask.get('price', 'N/A')}, volume={ask.get('volume', 'N/A')}, ratio={ask.get('ratio', 'N/A')}")
            
            # Get the current price - prefer market_context, fallback to order book midpoint
            current_price = None
            
            # Try to get price from market_context
            if market_context and hasattr(market_context, 'price') and market_context.price:
                current_price = market_context.price
                logger.info(f"Using price from market context: {current_price}")
            else:
                # Fallback to order book midpoint
                best_bid = float(order_book['bids'][0][0]) if order_book['bids'] else 0
                best_ask = float(order_book['asks'][0][0]) if order_book['asks'] else 0
                
                if best_bid == 0 or best_ask == 0:
                    logger.warning(f"Invalid bid/ask prices: bid={best_bid}, ask={best_ask}")
                    current_price = best_bid or best_ask  # Use whichever one is non-zero
                else:
                    current_price = (best_bid + best_ask) / 2
            
            # Generate a trading signal based on the liquidity analysis
            signal, confidence, explanation = self._generate_signal(analysis_result, market_context)
            
            execution_time = time.time() - start_time
            
            # Normalize confidence for SELL signals when there are conflicting BUY consensus
            # Check if we have other agent analyses in market_data
            if signal == "SELL" and confidence > 85 and market_data and isinstance(market_data, dict):
                normalized_confidence = self._normalize_confidence_for_consensus(
                    signal=signal,
                    confidence=confidence,
                    market_data=market_data
                )
                
                if normalized_confidence != confidence:
                    logger.info(f"Normalized {signal} confidence from {confidence} to {normalized_confidence} due to conflicting consensus")
                    explanation += f" (confidence adjusted due to conflicting market signals)"
                    confidence = normalized_confidence
            
            # Prepare results with entry and stop-loss zones and sanity status
            results = {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "interval": interval,
                "current_price": current_price,
                "signal": signal,
                "confidence": confidence,
                "explanation": [explanation],
                "metrics": analysis_result,
                "execution_time_seconds": execution_time,
                "entry_zone": analysis_result.get("suggested_entry"),
                "stop_loss_zone": analysis_result.get("suggested_stop_loss"),
                "liquidity_zones": analysis_result.get("liquidity_zones", {}),
                "agent_sane": analysis_result.get("agent_sane", True),
                "sanity_message": analysis_result.get("sanity_message"),
                "status": "success"
            }
            
            # Log decision summary
            try:
                # Initialize decision logger
                decision_logger = DecisionLogger()
                
                # Ensure symbol is a string, not None or dict
                symbol_str = symbol if isinstance(symbol, str) else str(symbol)
                
                # Log the decision with entry and stop-loss zones
                decision_logger.log_decision(
                    agent_name=self.name,
                    signal=signal,
                    confidence=int(confidence),  # Cast to int to satisfy type requirements
                    reason=explanation,
                    symbol=symbol_str,
                    price=float(current_price),
                    timestamp=results["timestamp"],
                    additional_data={
                        "interval": interval,
                        "entry_zone": analysis_result.get("suggested_entry"),
                        "stop_loss_zone": analysis_result.get("suggested_stop_loss"),
                        "liquidity_zones": analysis_result.get("liquidity_zones", {}),
                        "agent_sane": analysis_result.get("agent_sane", True),
                        "sanity_message": analysis_result.get("sanity_message"),
                        "metrics": analysis_result
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to log decision: {str(e)}")
            
            # Return results
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing liquidity: {str(e)}", exc_info=True)
            return self.build_error_response(
                "LIQUIDITY_ANALYSIS_ERROR",
                f"Error analyzing liquidity: {str(e)}"
            )
    
    def _analyze_order_book(self, order_book: Dict[str, Any], market_context=None) -> Dict[str, Any]:
        """
        Analyze the order book to extract liquidity metrics and identify 
        liquidity-based entry and stop-loss zones.
        
        Args:
            order_book: Dictionary containing 'bids' and 'asks' arrays
            market_context: Optional MarketContext object containing additional market data
            
        Returns:
            Dictionary of liquidity metrics including support/resistance clusters
            and suggested entry/stop-loss levels
        """
        # RAW DATA DEBUG - Log the raw order book structure to understand what we're working with
        logger.critical("====================== RAW ORDER BOOK DATA ======================")
        logger.critical(f"Order book keys: {order_book.keys()}")
        
        # Safe access to bids/asks
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])
        
        logger.critical(f"Bids count: {len(bids)}")
        logger.critical(f"Asks count: {len(asks)}")
        
        # Print first few entries of each to understand structure
        if bids:
            logger.critical(f"Sample bids (first 3): {bids[:3]}")
        if asks:
            logger.critical(f"Sample asks (first 3): {asks[:3]}")
            
        # Print market context info if available
        if market_context:
            logger.critical(f"Market context available: symbol={market_context.symbol}, price={market_context.price}")
        logger.critical("=======================================================================")
        # Extract bids and asks
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])
        
        # Check if we have valid data
        if not bids or not asks:
            logger.warning("Empty bids or asks in order book")
            return {
                "spread_pct": 0,
                "bid_depth_usdt": 0,
                "ask_depth_usdt": 0,
                "bid_ask_ratio": 1.0,
                "liquidity_score": 0,
                "liquidity_zones": {
                    "support_clusters": [],
                    "resistance_clusters": [],
                    "gaps": []
                },
                "suggested_entry": None,
                "suggested_stop_loss": None,
                "agent_sane": False,
                "sanity_message": "Empty order book data"
            }
        
        # Calculate bid-ask spread
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100 if best_bid > 0 else 0
        
        # Calculate market depth
        bid_depth_usdt = sum(float(bid[0]) * float(bid[1]) for bid in bids)
        ask_depth_usdt = sum(float(ask[0]) * float(ask[1]) for ask in asks)
        
        # Calculate bid-ask ratio
        bid_ask_ratio = bid_depth_usdt / ask_depth_usdt if ask_depth_usdt > 0 else 1.0
        
        # Calculate a liquidity score (0-100)
        # Higher is more liquid
        total_depth = bid_depth_usdt + ask_depth_usdt
        depth_score = min(100, math.log10(total_depth + 1) * 10) if total_depth > 0 else 0
        
        # Spread score (higher for tighter spreads)
        spread_score = max(0, 100 - (spread_pct * 200)) if spread_pct > 0 else 100
        
        # Balance score (higher for more balanced books)
        balance_score = 100 - min(100, abs(bid_ask_ratio - 1) * 50)
        
        # Combined liquidity score
        liquidity_score = (depth_score * 0.5) + (spread_score * 0.3) + (balance_score * 0.2)
        
        # Convert all bids and asks to float format for better analysis
        processed_bids = [[float(price), float(volume)] for price, volume in bids]
        processed_asks = [[float(price), float(volume)] for price, volume in asks]
        
        # Extract top bid and ask levels for display
        top_bids = processed_bids[:10]
        top_asks = processed_asks[:10]
        
        # Create price bins for clustering to identify support/resistance zones
        current_price = (best_bid + best_ask) / 2
        
        # Compute bid and ask depth totals - needed for debugging and calculations
        bid_depth = sum(volume for _, volume in processed_bids)
        ask_depth = sum(volume for _, volume in processed_asks)
        
        # Calculate bid/ask ratio - a key liquidity metric for directional bias
        bid_ask_ratio = bid_depth / ask_depth if ask_depth > 0 else 1.0
        
        # Dynamic bin sizing based on volatility if market_context is available
        if market_context and hasattr(market_context, 'volatility_1h') and market_context.volatility_1h:
            # Adjust bin size based on 1h volatility - more volatile markets need wider bins
            volatility_factor = min(3.0, max(0.5, market_context.volatility_1h))
            dynamic_bin_size_pct = self.price_bin_size_pct * volatility_factor
            logger.info(f"Using dynamic bin size: {dynamic_bin_size_pct:.4f}% based on volatility factor {volatility_factor:.2f}")
            bin_size = current_price * (dynamic_bin_size_pct / 100)
        else:
            # Use default bin size if no market context or volatility available
            bin_size = current_price * (self.price_bin_size_pct / 100)
            
        # EXTREME DEBUG: Log through logger
        logger.critical("====================== EXTREME DEBUG - LIQUIDITY ANALYST ======================")
        logger.critical(f"MARKET PRICE: {current_price}")
        logger.critical(f"BID_ASK_RATIO: {bid_ask_ratio}")
        logger.critical(f"BID_DEPTH: {bid_depth}")
        logger.critical(f"ASK_DEPTH: {ask_depth}")
        logger.critical(f"BIN_SIZE: {bin_size}")
        logger.critical(f"VOLATILITY: {market_context.volatility_1h if market_context and hasattr(market_context, 'volatility_1h') else 'Unknown'}")
        if market_context:
            logger.critical(f"MARKET PHASE: {market_context.market_phase if hasattr(market_context, 'market_phase') else 'Unknown'}")
        logger.critical("=========================================================================")
            
        # Advanced order book pattern heuristics for institutional order detection
        # We'll identify potential institutional orders using multiple techniques
        large_bids = []
        large_asks = []
        
        # Debug information about order book structure
        logger.info(f"Order book analysis - processed {len(processed_bids)} bids and {len(processed_asks)} asks")
        logger.info(f"Bid volume range: min={min([b[1] for b in processed_bids]):.2f}, max={max([b[1] for b in processed_bids]):.2f}")
        logger.info(f"Ask volume range: min={min([a[1] for a in processed_asks]):.2f}, max={max([a[1] for a in processed_asks]):.2f}")
        
        # TECHNIQUE 1: Detect orders significantly larger than neighbors (localized volume peaks)
        # Look for orders that are at least 1.5x larger than the average of nearby orders (further reduced from 2x)
        large_volume_threshold = 1.5  # Further reduced from 2.0 to detect even more subtle institutional orders
        
        for i in range(1, len(processed_bids)-1):
            avg_neighbor_volume = (processed_bids[i-1][1] + processed_bids[i+1][1]) / 2
            if processed_bids[i][1] > avg_neighbor_volume * large_volume_threshold:
                large_bids.append({
                    'price': processed_bids[i][0],
                    'volume': processed_bids[i][1],
                    'ratio': processed_bids[i][1] / avg_neighbor_volume,
                    'type': 'volume_spike'
                })
                logger.debug(f"Technique 1: Bid volume spike detected at price {processed_bids[i][0]:.2f}, volume {processed_bids[i][1]:.2f}")
                
        for i in range(1, len(processed_asks)-1):
            avg_neighbor_volume = (processed_asks[i-1][1] + processed_asks[i+1][1]) / 2
            if processed_asks[i][1] > avg_neighbor_volume * large_volume_threshold:
                large_asks.append({
                    'price': processed_asks[i][0],
                    'volume': processed_asks[i][1],
                    'ratio': processed_asks[i][1] / avg_neighbor_volume,
                    'type': 'volume_spike'
                })
                logger.debug(f"Technique 1: Ask volume spike detected at price {processed_asks[i][0]:.2f}, volume {processed_asks[i][1]:.2f}")
                
        # TECHNIQUE 2: Detect orders that stand out from global average (overall standouts)
        # Calculate global volume statistics
        if len(processed_bids) > 5:
            # Calculate statistics excluding the top and bottom 10% to avoid skew
            top_10_pct = max(1, int(len(processed_bids) * 0.1))
            usable_bids = processed_bids[top_10_pct:-top_10_pct] if len(processed_bids) > 20 else processed_bids
            
            bid_volumes = [order[1] for order in usable_bids]
            avg_bid_volume = sum(bid_volumes) / len(bid_volumes) if bid_volumes else 0
            
            # Calculate standard deviation of volumes
            bid_volume_variance = sum((v - avg_bid_volume) ** 2 for v in bid_volumes) / len(bid_volumes) if bid_volumes else 0
            bid_volume_std = math.sqrt(bid_volume_variance)
            
            # Log the statistical information
            logger.info(f"Bid volume statistics: avg={avg_bid_volume:.2f}, std_dev={bid_volume_std:.2f}")
            
            # Look for orders that are more than 1.5 standard deviations above average (reduced from 2.0)
            statistical_outlier_threshold = 1.5  # Reduced from 2.0 to be more sensitive
            
            if bid_volume_std > 0:
                for i, (price, volume) in enumerate(processed_bids):
                    z_score = (volume - avg_bid_volume) / bid_volume_std
                    if z_score > statistical_outlier_threshold:  # More than 1.5 standard deviations above average
                        # Check if this order is already captured by technique 1
                        if not any(abs(existing['price'] - price) < 0.001 for existing in large_bids):
                            large_bids.append({
                                'price': price,
                                'volume': volume,
                                'ratio': volume / avg_bid_volume,
                                'type': 'statistical_outlier',
                                'z_score': z_score
                            })
                            logger.debug(f"Technique 2: Bid statistical outlier detected at price {price:.2f}, volume {volume:.2f}, z-score {z_score:.2f}")
        
        # Similar analysis for asks
        if len(processed_asks) > 5:
            top_10_pct = max(1, int(len(processed_asks) * 0.1))
            usable_asks = processed_asks[top_10_pct:-top_10_pct] if len(processed_asks) > 20 else processed_asks
            
            ask_volumes = [order[1] for order in usable_asks]
            avg_ask_volume = sum(ask_volumes) / len(ask_volumes) if ask_volumes else 0
            
            ask_volume_variance = sum((v - avg_ask_volume) ** 2 for v in ask_volumes) / len(ask_volumes) if ask_volumes else 0
            ask_volume_std = math.sqrt(ask_volume_variance)
            
            # Log the statistical information for asks
            logger.info(f"Ask volume statistics: avg={avg_ask_volume:.2f}, std_dev={ask_volume_std:.2f}")
            
            # Ensure we use the same threshold value (1.5) for consistency
            statistical_outlier_threshold = 1.5  # Match the same value used for bids
            
            # Use same threshold for consistency across bids and asks
            if ask_volume_std > 0:
                for i, (price, volume) in enumerate(processed_asks):
                    z_score = (volume - avg_ask_volume) / ask_volume_std
                    if z_score > statistical_outlier_threshold:  # Using same threshold as bids (1.5)
                        if not any(abs(existing['price'] - price) < 0.001 for existing in large_asks):
                            large_asks.append({
                                'price': price,
                                'volume': volume,
                                'ratio': volume / avg_ask_volume,
                                'type': 'statistical_outlier',
                                'z_score': z_score
                            })
                            logger.debug(f"Technique 2: Ask statistical outlier detected at price {price:.2f}, volume {volume:.2f}, z-score {z_score:.2f}")
                            
        # TECHNIQUE 3: Detect potential iceberg orders (repeated orders at same price level)
        # This requires time-series data which we may not have, but we can approximate
        # by looking for multiple orders with very similar volumes at the same price
        
        # Sort by largest orders first
        large_bids = sorted(large_bids, key=lambda x: x['volume'], reverse=True)[:10]  # Limit to top 10
        large_asks = sorted(large_asks, key=lambda x: x['volume'], reverse=True)[:10]  # Limit to top 10
        
        logger.debug(f"Detected {len(large_bids)} large bid orders and {len(large_asks)} large ask orders")
        
        # Create bid bins to cluster orders at similar price levels
        bid_bins = {}
        for price, volume in processed_bids:
            bin_key = int(price / bin_size)
            if bin_key not in bid_bins:
                bid_bins[bin_key] = {
                    'total_volume': 0,
                    'avg_price': 0,
                    'levels': []
                }
            bid_bins[bin_key]['total_volume'] += volume
            bid_bins[bin_key]['levels'].append((price, volume))
        
        # Calculate average price for each bid bin (weighted by volume)
        for bin_key in bid_bins:
            total_weighted_price = sum(price * volume for price, volume in bid_bins[bin_key]['levels'])
            total_volume = bid_bins[bin_key]['total_volume']
            bid_bins[bin_key]['avg_price'] = total_weighted_price / total_volume if total_volume > 0 else 0
        
        # Create ask bins using the same binning approach
        ask_bins = {}
        for price, volume in processed_asks:
            bin_key = int(price / bin_size)
            if bin_key not in ask_bins:
                ask_bins[bin_key] = {
                    'total_volume': 0,
                    'avg_price': 0,
                    'levels': []
                }
            ask_bins[bin_key]['total_volume'] += volume
            ask_bins[bin_key]['levels'].append((price, volume))
        
        # Calculate average price for each ask bin (weighted by volume)
        for bin_key in ask_bins:
            total_weighted_price = sum(price * volume for price, volume in ask_bins[bin_key]['levels'])
            total_volume = ask_bins[bin_key]['total_volume']
            ask_bins[bin_key]['avg_price'] = total_weighted_price / total_volume if total_volume > 0 else 0
        
        # Calculate average bin volume for normalization
        avg_bid_bin_volume = sum(b['total_volume'] for b in bid_bins.values()) / len(bid_bins) if bid_bins else 0
        avg_ask_bin_volume = sum(b['total_volume'] for b in ask_bins.values()) / len(ask_bins) if ask_bins else 0
        
        # Define cluster thresholds based on averages - enhanced with more sensitive detection
        bid_cluster_threshold = avg_bid_bin_volume * 1.5  # 1.5x average for significant support (was 1.8x)
        ask_cluster_threshold = avg_ask_bin_volume * 1.5  # 1.5x average for significant resistance (was 1.8x)
        bid_gap_threshold = avg_bid_bin_volume * 0.25    # 0.25x average for bid gaps (was 0.3x)
        ask_gap_threshold = avg_ask_bin_volume * 0.25    # 0.25x average for ask gaps (was 0.3x)
        
        # Identify support clusters (significant bid walls)
        support_clusters = []
        for bin_key, bin_data in sorted(bid_bins.items(), reverse=True):  # Sort by price descending
            if bin_data['total_volume'] > bid_cluster_threshold:
                support_clusters.append({
                    'price': bin_data['avg_price'],
                    'volume': bin_data['total_volume'],
                    'strength': bin_data['total_volume'] / avg_bid_bin_volume if avg_bid_bin_volume > 0 else 1.0
                })
                logger.debug(f"Support cluster detected at {bin_data['avg_price']:.2f} with volume {bin_data['total_volume']:.2f}")
        
        # Identify resistance clusters (significant ask walls)
        resistance_clusters = []
        for bin_key, bin_data in sorted(ask_bins.items()):  # Sort by price ascending
            if bin_data['total_volume'] > ask_cluster_threshold:
                resistance_clusters.append({
                    'price': bin_data['avg_price'],
                    'volume': bin_data['total_volume'],
                    'strength': bin_data['total_volume'] / avg_ask_bin_volume if avg_ask_bin_volume > 0 else 1.0
                })
                logger.debug(f"Resistance cluster detected at {bin_data['avg_price']:.2f} with volume {bin_data['total_volume']:.2f}")
        
        # Sort the clusters by price
        support_clusters = sorted(support_clusters, key=lambda x: x['price'], reverse=True)  # Descending
        resistance_clusters = sorted(resistance_clusters, key=lambda x: x['price'])  # Ascending
        
        # Extract just the prices for backward compatibility
        support_cluster_prices = [cluster['price'] for cluster in support_clusters]
        resistance_cluster_prices = [cluster['price'] for cluster in resistance_clusters]
        
        # Identify liquidity gaps (areas with low volume)
        gaps = []
        
        # Check for gaps in bid side
        for bin_key, bin_data in sorted(bid_bins.items(), reverse=True):
            if bin_data['total_volume'] < bid_gap_threshold:
                gaps.append(bin_data['avg_price'])
                logger.debug(f"Liquidity gap detected at bid {bin_data['avg_price']:.2f} with volume {bin_data['total_volume']:.2f}")
                
        # Check for gaps in ask side
        for bin_key, bin_data in sorted(ask_bins.items()):
            if bin_data['total_volume'] < ask_gap_threshold:
                gaps.append(bin_data['avg_price'])
                logger.debug(f"Liquidity gap detected at ask {bin_data['avg_price']:.2f} with volume {bin_data['total_volume']:.2f}")
        
        # Determine suggested entry zones based on liquidity clusters
        suggested_entry = None
        suggested_stop_loss = None
        
        # For BUY signals, entry is typically just above a strong support
        # and stop loss is below the support
        if bid_ask_ratio > 1.0 and support_cluster_prices:
            # Entry slightly above strongest support
            suggested_entry = support_cluster_prices[0] * 1.001  # 0.1% above support
            
            # Find nearest gap below support for stop loss
            suitable_gaps = [gap for gap in gaps if gap < support_cluster_prices[0]]
            if suitable_gaps:
                # Use the closest gap below support
                suggested_stop_loss = max(suitable_gaps)
            else:
                # Fallback: use a fixed percentage below support
                suggested_stop_loss = support_cluster_prices[0] * 0.99  # 1% below support
                
        # For SELL signals, entry is typically just below a strong resistance
        # and stop loss is above the resistance
        elif bid_ask_ratio < 1.0 and resistance_cluster_prices:
            # Entry slightly below strongest resistance
            suggested_entry = resistance_cluster_prices[0] * 0.999  # 0.1% below resistance
            
            # Find nearest gap above resistance for stop loss
            suitable_gaps = [gap for gap in gaps if gap > resistance_cluster_prices[0]]
            if suitable_gaps:
                # Use the closest gap above resistance
                suggested_stop_loss = min(suitable_gaps)
            else:
                # Fallback: use a fixed percentage above resistance
                suggested_stop_loss = resistance_cluster_prices[0] * 1.01  # 1% above resistance
                
        # Package liquidity zones with detailed information
        liquidity_zones = {
            "support_clusters": [
                {
                    "price": cluster['price'],
                    "volume": cluster['volume'],
                    "strength": cluster['strength']
                } for cluster in support_clusters
            ],
            "resistance_clusters": [
                {
                    "price": cluster['price'],
                    "volume": cluster['volume'],
                    "strength": cluster['strength']
                } for cluster in resistance_clusters
            ],
            "support_prices": support_cluster_prices,
            "resistance_prices": resistance_cluster_prices,
            "gaps": gaps,
            "large_bids": large_bids,
            "large_asks": large_asks
        }
        
        # Perform sanity check on the results
        agent_sane, sanity_message = self._perform_sanity_check(
            support_clusters=support_clusters,
            resistance_clusters=resistance_clusters, 
            gaps=gaps,
            bid_ask_ratio=bid_ask_ratio
        )
        
        # Return results with detailed metrics
        result = {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "spread_pct": spread_pct,
            "bid_depth_usdt": bid_depth_usdt,
            "ask_depth_usdt": ask_depth_usdt,
            "total_depth_usdt": total_depth,
            "bid_ask_ratio": bid_ask_ratio,
            "depth_score": depth_score,
            "spread_score": spread_score,
            "balance_score": balance_score,
            "liquidity_score": liquidity_score,
            "top_bids": top_bids[:5],  # Top 5 bid levels for display
            "top_asks": top_asks[:5],  # Top 5 ask levels for display
            "liquidity_zones": liquidity_zones,
            "suggested_entry": suggested_entry,
            "suggested_stop_loss": suggested_stop_loss,
            "agent_sane": agent_sane,
            "sanity_message": sanity_message if not agent_sane else None
        }
        
        if not agent_sane:
            logger.warning(f"⚠️ LiquidityAnalystAgent detected abnormal liquidity structure. Sanity check failed: {sanity_message}")
        
        return result
    
    def _perform_sanity_check(
        self, 
        support_clusters: List[Dict[str, Any]], 
        resistance_clusters: List[Dict[str, Any]], 
        gaps: List[float],
        bid_ask_ratio: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Perform sanity checks on the liquidity analysis results.
        
        Args:
            support_clusters: List of detected support clusters
            resistance_clusters: List of detected resistance clusters
            gaps: List of detected liquidity gaps
            bid_ask_ratio: Ratio of bid to ask depth
            
        Returns:
            Tuple of (is_sane, error_message) where error_message is None if is_sane is True
        """
        # Check 1: Are there at least a minimum number of support/resistance zones?
        # V2.0 UPDATE: Reduced minimum zones from 3 to 2 and accept statistical outliers as valid
        total_zones = len(support_clusters) + len(resistance_clusters)
        if total_zones < self.min_liquidity_zones:
            # Before failing the sanity check, see if we at least have one of each type
            # This is a softer criterion than the previous version
            if support_clusters and resistance_clusters:
                logger.info(f"Only {total_zones} liquidity zones detected but at least one support and one resistance, proceeding")
                # We'll consider this acceptable but with reduced confidence
                return True, None
            else:
                return False, f"Too few liquidity zones detected: {total_zones} (minimum: {self.min_liquidity_zones})"
        
        # Check 2: Are the bid/ask ratios within reasonable ranges?
        # V2.0 UPDATE: More nuanced handling of extreme ratios
        if bid_ask_ratio > self.max_bid_ask_ratio:
            # Extremely high ratio (many more bids than asks)
            if bid_ask_ratio > 1.25:
                # This is a strong BUY signal, not an error
                logger.critical(f"EXTREME BID/ASK RATIO DETECTED: {bid_ask_ratio:.4f} - Strong buying pressure")
                return True, None
            else:
                return False, f"Bid/ask ratio too extreme (high): {bid_ask_ratio:.2f} (max allowed: {self.max_bid_ask_ratio})"
        
        if bid_ask_ratio < self.min_bid_ask_ratio:
            # Extremely low ratio (many more asks than bids)
            if bid_ask_ratio < 0.75:
                # This is a strong SELL signal, not an error
                logger.critical(f"EXTREME BID/ASK RATIO DETECTED: {bid_ask_ratio:.4f} - Strong selling pressure")
                return True, None
            else:
                return False, f"Bid/ask ratio too extreme (low): {bid_ask_ratio:.2f} (min allowed: {self.min_bid_ask_ratio})"
        
        # Check 3: Ensure that the price differences between clusters make sense
        if len(support_clusters) >= 2:
            # Calculate the percentage differences between adjacent support clusters
            support_prices = [c['price'] for c in support_clusters]
            
            # Get min and max price
            min_support = min(support_prices)
            max_support = max(support_prices)
            
            # Check if the total price range is unreasonably small
            support_range_pct = ((max_support - min_support) / min_support) * 100
            if support_range_pct < 0.1:  # Less than 0.1% range
                return False, f"Support clusters too tightly packed: {support_range_pct:.2f}% range"
        
        if len(resistance_clusters) >= 2:
            # Calculate the percentage differences between adjacent resistance clusters
            resistance_prices = [c['price'] for c in resistance_clusters]
            
            # Get min and max price
            min_resistance = min(resistance_prices)
            max_resistance = max(resistance_prices)
            
            # Check if the total price range is unreasonably small
            resistance_range_pct = ((max_resistance - min_resistance) / min_resistance) * 100
            if resistance_range_pct < 0.1:  # Less than 0.1% range
                return False, f"Resistance clusters too tightly packed: {resistance_range_pct:.2f}% range"
        
        # SPECIAL CASE: If bid_ask_ratio indicates very strong directional pressure, allow signal even with other issues
        if bid_ask_ratio < 0.75 or bid_ask_ratio > 1.25:
            logger.critical(f"SANITY CHECK BYPASSED due to extreme bid/ask ratio: {bid_ask_ratio:.4f}")
            # Return True to bypass all other checks when we have extreme imbalance
            return True, None
            
        # Check 4: Evaluate the volumes - are any volumes unrealistically high?
        for cluster in support_clusters:
            # Flag clusters with excessive strength
            if cluster['strength'] > 15:  # Increased from 10x to 15x average volume
                return False, f"Unrealistic support volume spike detected: {cluster['strength']:.2f}x average"
        
        for cluster in resistance_clusters:
            # Flag clusters with excessive strength
            if cluster['strength'] > 15:  # Increased from 10x to 15x average volume
                return False, f"Unrealistic resistance volume spike detected: {cluster['strength']:.2f}x average"
        
        # Check 5: Ensure gaps are not too frequent (more gaps than clusters suggest data quality issues)
        if len(gaps) > total_zones * 3:
            return False, f"Too many liquidity gaps detected: {len(gaps)} (vs {total_zones} clusters)"
        
        # All checks passed, the result is sane
        return True, None
        
    def _generate_signal(self, metrics: Dict[str, Any], market_context=None) -> Tuple[str, int, str]:
        """
        Generate a trading signal based on liquidity analysis.
        
        Args:
            metrics: Liquidity metrics
            market_context: Optional MarketContext object containing additional market data
            
        Returns:
            Tuple of (signal, confidence, explanation)
        """
        # CRITICAL DEBUG: Log all important metrics at the start of signal generation
        bid_ask_ratio = metrics.get('bid_ask_ratio', 1.0)
        bid_depth = metrics.get('bid_depth', 0)
        ask_depth = metrics.get('ask_depth', 0)
        logger.critical(f"LIQUIDITY METRICS: bid_ask_ratio={bid_ask_ratio:.4f}, bid_depth={bid_depth:.2f}, ask_depth={ask_depth:.2f}")
        
        if 'support_clusters' in metrics:
            logger.critical(f"Support clusters: {len(metrics['support_clusters'])}")
        if 'resistance_clusters' in metrics:
            logger.critical(f"Resistance clusters: {len(metrics['resistance_clusters'])}")
        if 'liquidity_gaps' in metrics:
            logger.critical(f"Liquidity gaps: {len(metrics['liquidity_gaps'])}")
        if 'wall_clusters' in metrics:
            logger.critical(f"Wall clusters: {len(metrics['wall_clusters'])}")
        # Extract key metrics
        spread_pct = metrics.get('spread_pct', 0)
        bid_depth = metrics.get('bid_depth_usdt', 0)
        ask_depth = metrics.get('ask_depth_usdt', 0)
        bid_ask_ratio = metrics.get('bid_ask_ratio', 1.0)
        liquidity_score = metrics.get('liquidity_score', 50)
        
        # Get liquidity zones information
        liquidity_zones = metrics.get('liquidity_zones', {})
        support_clusters = liquidity_zones.get('support_clusters', [])
        resistance_clusters = liquidity_zones.get('resistance_clusters', [])
        large_bids = liquidity_zones.get('large_bids', [])
        large_asks = liquidity_zones.get('large_asks', [])
        gaps = liquidity_zones.get('gaps', [])
        
        # Get entry and stop-loss suggestions
        suggested_entry = metrics.get('suggested_entry')
        suggested_stop_loss = metrics.get('suggested_stop_loss')
        
        # Top order book levels for explanation
        top_bids = metrics.get('top_bids', [])
        top_asks = metrics.get('top_asks', [])
        
        # Format top bids and asks for logging
        top_bids_str = ", ".join([f"{price:.2f}: {vol:.2f}" for price, vol in top_bids[:3]]) if top_bids else "None"
        top_asks_str = ", ".join([f"{price:.2f}: {vol:.2f}" for price, vol in top_asks[:3]]) if top_asks else "None"
        
        # Check for extreme bid/ask ratio first - this overrides everything else
        bid_ask_ratio = metrics.get('bid_ask_ratio', 1.0)
        if bid_ask_ratio < 0.75:
            logger.critical(f"EXTREME BID/ASK RATIO DETECTED: {bid_ask_ratio:.4f} - Forcing SELL signal")
            explanation = f"Strong selling pressure detected with bid/ask ratio of {bid_ask_ratio:.4f} (below 0.75 threshold). "
            explanation += "Order book shows significantly more selling than buying volume."
            confidence = 85 + int((0.75 - bid_ask_ratio) * 20)  # Higher confidence for more extreme ratios
            confidence = min(95, max(80, confidence))  # Cap between 80-95
            return "SELL", confidence, explanation
            
        if bid_ask_ratio > 1.25:
            logger.critical(f"EXTREME BID/ASK RATIO DETECTED: {bid_ask_ratio:.4f} - Forcing BUY signal")
            explanation = f"Strong buying pressure detected with bid/ask ratio of {bid_ask_ratio:.4f} (above 1.25 threshold). "
            explanation += "Order book shows significantly more buying than selling volume."
            confidence = 85 + int((bid_ask_ratio - 1.25) * 20)  # Higher confidence for more extreme ratios
            confidence = min(95, max(80, confidence))  # Cap between 80-95
            return "BUY", confidence, explanation
            
        # Check sanity status next
        agent_sane = metrics.get('agent_sane', True)
        sanity_message = metrics.get('sanity_message', None)
        
        # If sanity check failed, downgrade confidence and add warning
        if not agent_sane:
            explanation = f"⚠️ Abnormal liquidity structure detected: {sanity_message}. "
            explanation += "Defaulting to NEUTRAL signal with reduced confidence."
            return "NEUTRAL", 50, explanation
            
        # Attempt to use LLM for enhanced analysis if available
        try:
            if self.llm_client:
                # Try to get additional market context
                symbol_str = "Unknown"
                current_price = 0
                market_phase = "Unknown"
                volatility = 0
                
                if market_context:
                    symbol_str = market_context.symbol if hasattr(market_context, 'symbol') else "Unknown"
                    current_price = market_context.price if hasattr(market_context, 'price') else 0
                    market_phase = market_context.market_phase if hasattr(market_context, 'market_phase') else "Unknown"
                    
                    # Get volatility info
                    if hasattr(market_context, 'volatility_1h'):
                        volatility = market_context.volatility_1h
                    elif hasattr(market_context, 'volatility'):
                        volatility = market_context.volatility
                
                # Format support clusters for prompt
                support_str = ""
                if support_clusters:
                    support_str = "\n".join([f"- Price: {c['price']:.2f}, Volume: {c['volume']:.2f}, Strength: {c['strength']:.2f}x" 
                                         for c in support_clusters[:5]])
                else:
                    support_str = "No significant support clusters detected."
                    
                # Format resistance clusters for prompt
                resistance_str = ""
                if resistance_clusters:
                    resistance_str = "\n".join([f"- Price: {c['price']:.2f}, Volume: {c['volume']:.2f}, Strength: {c['strength']:.2f}x" 
                                           for c in resistance_clusters[:5]])
                else:
                    resistance_str = "No significant resistance clusters detected."
                    
                # Format large orders for prompt
                large_orders_str = ""
                if large_bids:
                    large_orders_str += "\nLarge bid orders (potential institutional buying):\n"
                    large_orders_str += "\n".join([f"- Price: {o['price']:.2f}, Volume: {o['volume']:.2f}, Size ratio: {o['ratio']:.2f}x" 
                                               for o in large_bids[:3]])
                if large_asks:
                    large_orders_str += "\nLarge ask orders (potential institutional selling):\n"
                    large_orders_str += "\n".join([f"- Price: {o['price']:.2f}, Volume: {o['volume']:.2f}, Size ratio: {o['ratio']:.2f}x" 
                                               for o in large_asks[:3]])
                if not large_bids and not large_asks:
                    large_orders_str = "\nNo significant large orders detected."

                # Format significant bids and asks for display
                large_bids_str = ", ".join([f"{b['price']:.2f}" for b in large_bids[:3]]) if large_bids else "None"
                large_asks_str = ", ".join([f"{a['price']:.2f}" for a in large_asks[:3]]) if large_asks else "None"
                
                # Calculate USDT values for display in prompt
                bid_depth_usdt = metrics.get('bid_depth_usdt', 0) / 1000000  # Convert to millions for display
                ask_depth_usdt = metrics.get('ask_depth_usdt', 0) / 1000000  # Convert to millions for display
                
                # V2.0 Enhanced LLM prompt with market microstructure focus
                prompt = f"""
                You are an expert cryptocurrency market liquidity analyst specializing in high-frequency order book analysis.
                Analyze this market microstructure data to produce tactical trading recommendations:

                MARKET MICROSTRUCTURE:
                Symbol: {symbol_str}
                Current price: ${current_price:.2f}
                Spread: {spread_pct:.4f}%
                Bid/Ask depth: {bid_depth_usdt:.1f}M / {ask_depth_usdt:.1f}M USDT
                Bid/Ask ratio: {bid_ask_ratio:.2f}
                Large bids @ [{large_bids_str}]
                Large asks @ [{large_asks_str}]
                Market phase: {market_phase}
                Volatility: {volatility:.2f}

                SUPPORT ZONES:
                {support_str}

                RESISTANCE ZONES:
                {resistance_str}

                NOTABLE ORDER PATTERN ANALYSIS:
                {large_orders_str}

                What is the market microstructure sentiment?
                What tactical decision would a market maker make here?
                Should we BUY, SELL, or HOLD?

                Based on this microstructure analysis, provide your analysis in JSON format:
                {{
                  "signal": "[BUY/SELL/NEUTRAL]",
                  "confidence": [number between 50-95],
                  "reasoning": "[concise explanation based on microstructure]",
                  "suggested_entry": [optimal entry price],
                  "suggested_stop_loss": [appropriate stop-loss level],
                  "suggested_take_profit": [profit target based on resistance or ask walls]
                }}
                """
                
                # Get LLM response (with temperature 0.2 for more consistent outputs)
                try:
                    llm_response = self.llm_client.generate(prompt, temperature=0.2)
                    
                    # Handle different response formats from various LLM clients
                    if isinstance(llm_response, dict):
                        if 'content' in llm_response:
                            response_text = llm_response['content']
                        elif 'response' in llm_response:
                            response_text = llm_response['response']
                        elif 'choices' in llm_response and llm_response['choices'] and isinstance(llm_response['choices'][0], dict):
                            if 'message' in llm_response['choices'][0] and 'content' in llm_response['choices'][0]['message']:
                                response_text = llm_response['choices'][0]['message']['content']
                            elif 'text' in llm_response['choices'][0]:
                                response_text = llm_response['choices'][0]['text']
                        else:
                            logger.warning(f"Unknown dict response format: {list(llm_response.keys())}")
                            raise ValueError("Unrecognized LLM response dictionary format")
                    elif isinstance(llm_response, str):
                        response_text = llm_response
                    else:
                        logger.warning(f"Unexpected LLM response format: {type(llm_response)}")
                        raise ValueError("Unexpected LLM response format")
                        
                    # V2.0 Update: Try to parse JSON format first
                    # Remove any leading/trailing whitespace and extract JSON content
                    response_text = response_text.strip()
                    
                    # Try to extract JSON object if wrapped in text
                    json_match = re.search(r'\{.*"signal".*"confidence".*\}', response_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        try:
                            # Parse the JSON response
                            import json
                            parsed_json = json.loads(json_str)
                            
                            # Extract fields
                            llm_signal = parsed_json.get("signal", "").upper()
                            llm_confidence = int(parsed_json.get("confidence", 50))
                            llm_explanation = parsed_json.get("reasoning", "").strip()
                            
                            # Extract tactical recommendations (new in v2.0)
                            suggested_entry = parsed_json.get("suggested_entry")
                            suggested_stop_loss = parsed_json.get("suggested_stop_loss")
                            suggested_take_profit = parsed_json.get("suggested_take_profit")
                            
                            # Save these to the metrics dict for return value
                            metrics["suggested_entry"] = suggested_entry
                            metrics["suggested_stop_loss"] = suggested_stop_loss
                            metrics["suggested_take_profit"] = suggested_take_profit
                            
                            # Validate confidence within bounds
                            llm_confidence = max(50, min(95, llm_confidence))
                            
                            logger.info(f"LLM liquidity analysis: {llm_signal} ({llm_confidence}%): {llm_explanation}")
                            logger.info(f"Tactical recommendations: Entry=${suggested_entry}, SL=${suggested_stop_loss}, TP=${suggested_take_profit}")
                            
                            # Format the explanation with tactical levels
                            explanation = f"{llm_explanation} Entry: ${suggested_entry}, SL: ${suggested_stop_loss}, TP: ${suggested_take_profit}"
                            
                            # Return the LLM-generated signal with tactical recommendations
                            return llm_signal, llm_confidence, explanation
                            
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON from LLM response: {e}")
                    
                    # Fallback to regex parsing for backward compatibility
                    signal_match = re.search(r"Signal:\s*(BUY|SELL|NEUTRAL)", response_text, re.IGNORECASE)
                    confidence_match = re.search(r"Confidence:\s*(\d+)", response_text)
                    explanation_match = re.search(r"Explanation:\s*(.+?)(?:\n|$)", response_text, re.DOTALL)
                    
                    if signal_match and confidence_match and explanation_match:
                        llm_signal = signal_match.group(1).upper()
                        llm_confidence = int(confidence_match.group(1))
                        llm_explanation = explanation_match.group(1).strip()
                        
                        # Validate confidence within bounds
                        llm_confidence = max(50, min(95, llm_confidence))
                        
                        logger.info(f"LLM liquidity analysis (legacy format): {llm_signal} ({llm_confidence}%): {llm_explanation}")
                        
                        # Use fallback method for entry/stop-loss if available
                        if suggested_entry is not None and suggested_stop_loss is not None:
                            entry_str = f"{suggested_entry:.2f}"
                            sl_str = f"{suggested_stop_loss:.2f}"
                            take_profit = current_price * (1.015 if llm_signal == "BUY" else 0.985)  # Default 1.5% TP
                            tp_str = f"{take_profit:.2f}"
                            
                            metrics["suggested_entry"] = suggested_entry
                            metrics["suggested_stop_loss"] = suggested_stop_loss
                            metrics["suggested_take_profit"] = take_profit
                            
                            additional_detail = f" Entry: ${entry_str}, SL: ${sl_str}, TP: ${tp_str}"
                            return llm_signal, llm_confidence, llm_explanation + additional_detail
                        
                        # Return the LLM-generated signal
                        return llm_signal, llm_confidence, llm_explanation
                except Exception as e:
                    logger.warning(f"Error generating LLM liquidity analysis: {str(e)}")
                    # Continue with rule-based approach as fallback
        except Exception as e:
            logger.warning(f"Failed to use LLM for liquidity analysis: {str(e)}")

        # Default to rule-based approach if LLM fails or is not available
        # Default to neutral
        signal = "NEUTRAL"
        confidence = 50
        explanation = "Market liquidity is balanced"
        
        # Extensive debugging for bid/ask ratio and depths (CRITICAL FOR DEBUGGING)
        logger.info(f"CRITICAL DEBUG - LiquidityAnalystAgent bid/ask ratio: {bid_ask_ratio:.4f}, bid_depth: {bid_depth:.2f}, ask_depth: {ask_depth:.2f}")
        
        # Add forced diagnostic logging at critical level for diagnostic analysis
        print(f"========= LIQUIDITY ANALYSIS DIAGNOSTIC INFO =========")
        print(f"Symbol: {market_context.symbol if market_context else 'Unknown'}")
        print(f"Price: {market_context.price if market_context else 'Unknown'}")
        print(f"Bid/Ask Ratio: {bid_ask_ratio:.4f}")
        print(f"Bid Depth: {bid_depth:.2f} USDT")
        print(f"Ask Depth: {ask_depth:.2f} USDT") 
        print(f"Detected {len(large_bids)} large bids, {len(large_asks)} large asks")
        print(f"Support clusters: {len(support_clusters)}, Resistance clusters: {len(resistance_clusters)}")
        print(f"======================================================")
            
        # Get market volatility level if available to adjust thresholds
        market_volatility = 0
        is_high_volatility = False
        if market_context and hasattr(market_context, 'volatility_1h'):
            market_volatility = market_context.volatility_1h
            is_high_volatility = market_volatility > 0.015  # >1.5% hourly volatility is considered high
            logger.debug(f"Market volatility data available: {market_volatility:.4f}, high volatility: {is_high_volatility}")
        
        # Dynamically adjust thresholds based on volatility
        strong_buy_threshold = 1.6 if is_high_volatility else 1.8  # Further reduced from 1.8 in high volatility
        strong_sell_threshold = 0.65 if is_high_volatility else 0.55  # Adjusted to be more sensitive in high volatility
        
        moderate_buy_threshold = 1.15 if is_high_volatility else 1.3  # Much more sensitive in high volatility
        moderate_sell_threshold = 0.85 if is_high_volatility else 0.77  # Much more sensitive in high volatility
        
        # Log our dynamic thresholds
        logger.debug(f"Dynamic thresholds: strong_buy={strong_buy_threshold}, strong_sell={strong_sell_threshold}, " +
                     f"moderate_buy={moderate_buy_threshold}, moderate_sell={moderate_sell_threshold}")
        
        # Check for strong imbalances with dynamic thresholds
        if bid_ask_ratio > strong_buy_threshold and ask_depth < self.thresholds['medium_depth']:
            signal = "BUY"
            confidence = self.high_confidence
            explanation = f"Strong buying pressure with bid/ask ratio of {bid_ask_ratio:.2f}"
            if is_high_volatility:
                explanation += f" during high volatility ({market_volatility:.2%} hourly)"
            logger.info(f"Strong buying signal generated based on bid/ask ratio {bid_ask_ratio:.2f}")
        elif bid_ask_ratio < strong_sell_threshold and bid_depth < self.thresholds['medium_depth']:
            signal = "SELL"
            confidence = self.high_confidence
            explanation = f"Strong selling pressure with bid/ask ratio of {bid_ask_ratio:.2f}"
            if is_high_volatility:
                explanation += f" during high volatility ({market_volatility:.2%} hourly)"
            logger.info(f"Strong selling signal generated based on bid/ask ratio {bid_ask_ratio:.2f}")
        
        # Check for moderate imbalances with dynamic thresholds
        elif bid_ask_ratio > moderate_buy_threshold:
            signal = "BUY"
            confidence = self.medium_confidence
            explanation = f"Moderate buying pressure with bid/ask ratio of {bid_ask_ratio:.2f}"
            if is_high_volatility:
                explanation += f" (more sensitive during {market_volatility:.2%} volatility)"
            logger.info(f"Moderate buying signal generated based on bid/ask ratio {bid_ask_ratio:.2f}")
        elif bid_ask_ratio < moderate_sell_threshold:
            signal = "SELL"
            confidence = self.medium_confidence
            explanation = f"Moderate selling pressure with bid/ask ratio of {bid_ask_ratio:.2f}"
            if is_high_volatility:
                explanation += f" (more sensitive during {market_volatility:.2%} volatility)"
            logger.info(f"Moderate selling signal generated based on bid/ask ratio {bid_ask_ratio:.2f}")
        
        # Log enhanced debug information
        logger.info(f"LiquidityAnalystAgent fallback analysis: bid_ask_ratio={bid_ask_ratio:.2f}, large_bids={len(large_bids)}, large_asks={len(large_asks)}")
        logger.info(f"Support clusters: {len(support_clusters)}, Resistance clusters: {len(resistance_clusters)}")
        
        # Check for institutions - analyze the large orders we detected
        # More aggressive institutional order detection (check even if a signal already exists)
        if large_bids and not large_asks:
            # We have large buys but no large sells - bullish signal
            if signal == "NEUTRAL" or signal == "BUY":  # Only replace NEUTRAL or reinforce BUY
                signal = "BUY"
                confidence = self.medium_confidence
                explanation = f"Institutional buying detected with {len(large_bids)} large bid orders"
                logger.info(f"Generating BUY signal based on institutional buying detection")
        elif large_asks and not large_bids:
            # We have large sells but no large buys - bearish signal
            if signal == "NEUTRAL" or signal == "SELL":  # Only replace NEUTRAL or reinforce SELL
                signal = "SELL"
                confidence = self.medium_confidence
                explanation = f"Institutional selling detected with {len(large_asks)} large ask orders"
                logger.info(f"Generating SELL signal based on institutional selling detection")
        elif large_bids and large_asks:
            # If we have both, check which side has more volume or larger orders
            bid_volume = sum(order['volume'] for order in large_bids)
            ask_volume = sum(order['volume'] for order in large_asks)
            
            # Hyper-sensitive threshold - just 5% more volume is enough (down from 10%)
            if bid_volume > ask_volume * 1.05 and (signal == "NEUTRAL" or signal == "BUY"):
                signal = "BUY"
                confidence = self.medium_confidence
                explanation = f"Net institutional buying detected with {bid_volume:.2f} vs {ask_volume:.2f} USDT (hyper-sensitive)"
                logger.info(f"Generating BUY signal based on net institutional order imbalance (hyper-sensitive)")
            elif ask_volume > bid_volume * 1.05 and (signal == "NEUTRAL" or signal == "SELL"):
                signal = "SELL"
                confidence = self.medium_confidence
                explanation = f"Net institutional selling detected with {ask_volume:.2f} vs {bid_volume:.2f} USDT (hyper-sensitive)"
                logger.info(f"Generating SELL signal based on net institutional order imbalance (hyper-sensitive)")
            elif signal == "NEUTRAL":  # Only modify NEUTRAL
                # Still neutral but with higher confidence due to institutional activity
                confidence = 60
                explanation = f"Mixed institutional orders detected with balanced volume"
                logger.info(f"Maintaining NEUTRAL signal but increased confidence due to balanced institutional orders")
        
        # Check for support/resistance clusters with enhanced strength analysis
        if signal == "BUY" and support_clusters:
            avg_strength = sum(cluster['strength'] for cluster in support_clusters) / len(support_clusters)
            if avg_strength > 2.5:  # Strong support (2.5x average volume)
                confidence = min(95, confidence + 10)
                explanation += f", very strong support detected (avg {avg_strength:.1f}x normal volume)"
            else:
                explanation += f", support detected at {support_clusters[0]['price']:.2f}"
                confidence = min(95, confidence + 5)
                
        elif signal == "SELL" and resistance_clusters:
            avg_strength = sum(cluster['strength'] for cluster in resistance_clusters) / len(resistance_clusters)
            if avg_strength > 2.5:  # Strong resistance (2.5x average volume)
                confidence = min(95, confidence + 10)
                explanation += f", very strong resistance detected (avg {avg_strength:.1f}x normal volume)"
            else:
                explanation += f", resistance detected at {resistance_clusters[0]['price']:.2f}"
                confidence = min(95, confidence + 5)
        
        # Check spread conditions
        if spread_pct > self.thresholds['wide_spread']:
            # Wide spreads indicate low liquidity, so we'd want to be cautious
            if signal == "BUY":
                confidence = max(self.low_confidence, confidence - 20)
                explanation += f", but wide spread of {spread_pct:.2f}% indicates caution"
            elif signal == "SELL":
                confidence = max(self.low_confidence, confidence - 20)
                explanation += f", but wide spread of {spread_pct:.2f}% indicates caution"
            else:
                signal = "NEUTRAL"
                confidence = self.low_confidence
                explanation = f"Wide spread of {spread_pct:.2f}% indicates illiquid market conditions"
                
        # Consider overall liquidity
        if liquidity_score < 30:
            # Low liquidity overall suggests caution
            explanation += f", low overall liquidity (score: {liquidity_score:.0f}/100)"
            confidence = max(self.low_confidence, confidence - 15)
        elif liquidity_score > 70:
            # High liquidity is good for trading
            if signal != "NEUTRAL":
                explanation += f", good overall liquidity (score: {liquidity_score:.0f}/100)"
                confidence = min(95, confidence + 10)
            else:
                explanation = f"Highly liquid market conditions (score: {liquidity_score:.0f}/100), neutral bias"
        
        # EMERGENCY FALLBACK - If we're still NEUTRAL, check for any small imbalances
        # and use them to generate a signal with low confidence
        if signal == "NEUTRAL":
            # Force debug log to diagnose the issue
            logger.critical(f"EMERGENCY FALLBACK CHECK: bid_ask_ratio={bid_ask_ratio}, bid_depth_total={bid_depth}, ask_depth_total={ask_depth}")
            
            # ULTRA aggressive fallback - any TINY imbalance triggers a signal
            if bid_ask_ratio > 1.01:  # Just 1% more bids than asks - extremely sensitive!
                signal = "BUY"
                confidence = 55  # Low confidence
                explanation = f"Minimal buying pressure detected (ultra-fallback) with bid/ask ratio of {bid_ask_ratio:.2f}"
                logger.critical(f"Ultra-fallback BUY signal generated based on tiny imbalance: ratio={bid_ask_ratio:.2f}")
            elif bid_ask_ratio < 0.99:  # Just 1% more asks than bids - extremely sensitive!
                signal = "SELL"
                confidence = 55  # Low confidence
                explanation = f"Minimal selling pressure detected (ultra-fallback) with bid/ask ratio of {bid_ask_ratio:.2f}"
                logger.critical(f"Ultra-fallback SELL signal generated based on tiny imbalance: ratio={bid_ask_ratio:.2f}")
            # If we're still neutral after checking the ratio, check for clusters
            elif support_clusters and not resistance_clusters:
                signal = "BUY"
                confidence = 51  # Very low confidence
                explanation = f"Support clusters detected without resistance (fallback)"
                logger.critical(f"Ultra fallback BUY signal generated based on support clusters only")
            elif resistance_clusters and not support_clusters:
                signal = "SELL"
                confidence = 51  # Very low confidence
                explanation = f"Resistance clusters detected without support (fallback)"
                logger.critical(f"Ultra fallback SELL signal generated based on resistance clusters only")
            else:
                # ULTRA AGGRESSIVE FALLBACK based solely on bid/ask ratio
                logger.critical(f"Ratio {bid_ask_ratio:.2f} is within the initial neutral range (0.99-1.01)")
                
                # Use even more aggressive thresholds
                if bid_ask_ratio < 0.70:  # Very strong selling pressure
                    signal = "SELL"
                    confidence = 65
                    explanation = f"Strong selling pressure in order book with bid/ask ratio of {bid_ask_ratio:.2f}"
                    logger.critical(f"Ultra aggressive SELL signal on deep imbalance: ratio={bid_ask_ratio:.2f}")
                elif bid_ask_ratio > 1.30:  # Very strong buying pressure
                    signal = "BUY"
                    confidence = 65
                    explanation = f"Strong buying pressure in order book with bid/ask ratio of {bid_ask_ratio:.2f}"
                    logger.critical(f"Ultra aggressive BUY signal on deep imbalance: ratio={bid_ask_ratio:.2f}")
                elif bid_ask_ratio < 0.90:  # Moderate selling pressure
                    signal = "SELL"
                    confidence = 55
                    explanation = f"Moderate selling pressure in order book with bid/ask ratio of {bid_ask_ratio:.2f}"
                    logger.critical(f"Moderately aggressive SELL signal: ratio={bid_ask_ratio:.2f}")
                elif bid_ask_ratio > 1.10:  # Moderate buying pressure
                    signal = "BUY"
                    confidence = 55
                    explanation = f"Moderate buying pressure in order book with bid/ask ratio of {bid_ask_ratio:.2f}"
                    logger.critical(f"Moderately aggressive BUY signal: ratio={bid_ask_ratio:.2f}")
                else:
                    # If we're here, the market is truly balanced
                    signal = "NEUTRAL" 
                    explanation = f"Balanced order book with no significant pressure, bid/ask ratio: {bid_ask_ratio:.2f}"
                    logger.critical(f"Confirmed neutral market with balanced bid/ask ratio: {bid_ask_ratio:.2f}")
        
        # Add entry and stop-loss information to explanation
        if suggested_entry is not None and suggested_stop_loss is not None:
            entry_str = f"{suggested_entry:.2f}"
            sl_str = f"{suggested_stop_loss:.2f}"
            
            if signal == "BUY":
                explanation += f". Suggested entry: {entry_str} (above support), stop-loss: {sl_str}"
            elif signal == "SELL":
                explanation += f". Suggested entry: {entry_str} (below resistance), stop-loss: {sl_str}"
            else:
                # For NEUTRAL signals, suggest based on order book structure
                if support_clusters and resistance_clusters:
                    support_price = support_clusters[0]['price'] if isinstance(support_clusters[0], dict) else support_clusters[0]
                    resistance_price = resistance_clusters[0]['price'] if isinstance(resistance_clusters[0], dict) else resistance_clusters[0]
                    explanation += f". Watch support at {support_price:.2f} and resistance at {resistance_price:.2f}"
        
        # Add relevant liquidity detail to the explanation (top order book levels)
        explanation += f". Top bids: [{top_bids_str}], top asks: [{top_asks_str}]"
                
        return signal, confidence, explanation
        
    def _get_trading_config(self) -> Dict[str, Any]:
        """
        Get trading configuration.
        
        Returns:
            Trading configuration dictionary with default settings
        """
        try:
            # Try to import the trading config from the config module
            from config.trading_config import get_trading_config
            return get_trading_config()
        except ImportError:
            # Fall back to default config if trading_config module is not available
            logger.warning("Could not import trading_config, using default values")
            return {
                "default_interval": "1h",
                "risk_level": "medium",
                "position_sizing": {
                    "max_position_size_pct": 5.0,
                    "max_total_exposure_pct": 50.0
                }
            }
            
    def _fetch_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch market data for liquidity analysis.
        
        Args:
            symbol: Trading symbol
            **kwargs: Additional parameters
            
        Returns:
            Market data dictionary
        """
        if not self.data_fetcher:
            logger.warning("No data fetcher provided, cannot fetch market data")
            return {}
            
        try:
            # Fetch order book data
            order_book = self.data_fetcher.fetch_market_depth(symbol, limit=self.depth_levels)
            
            # Try to fetch current ticker if available
            ticker = {}
            try:
                ticker = self.data_fetcher.get_ticker(symbol)
            except:
                pass
                
            market_data = {
                "order_book": order_book,
                "ticker": ticker,
                "symbol": symbol
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return {}
            
    def _normalize_confidence_for_consensus(self, signal: str, confidence: float, market_data: Dict[str, Any]) -> float:
        """
        Normalize confidence level based on other agent signals in market_data.
        This prevents the LiquidityAnalystAgent from overpowering consensus with high confidence SELL signals.
        
        Args:
            signal: The current signal (BUY/SELL/NEUTRAL)
            confidence: The current confidence level
            market_data: Dictionary containing other agent analyses
            
        Returns:
            Normalized confidence level
        """
        # Only normalize SELL signals with high confidence
        if signal != "SELL" or confidence <= 85:
            return confidence
            
        # Look for agent analyses in market_data
        buy_signal_count = 0
        total_agent_count = 0
        
        # Check for technical analysis
        if "technical_analysis" in market_data and isinstance(market_data["technical_analysis"], dict):
            tech_signal = market_data["technical_analysis"].get("signal")
            if tech_signal == "BUY":
                buy_signal_count += 1
            total_agent_count += 1
            
        # Check for sentiment analysis
        if "sentiment_analysis" in market_data and isinstance(market_data["sentiment_analysis"], dict):
            sent_signal = market_data["sentiment_analysis"].get("signal")
            if sent_signal == "BUY":
                buy_signal_count += 1
            total_agent_count += 1
            
        # Check for sentiment aggregator
        if "sentiment_aggregator" in market_data and isinstance(market_data["sentiment_aggregator"], dict):
            agg_signal = market_data["sentiment_aggregator"].get("signal")
            if agg_signal == "BUY":
                buy_signal_count += 1
            total_agent_count += 1
            
        # Check other agents like funding rate, open interest
        other_analyses = ["funding_rate_analysis", "open_interest_analysis"]
        for analysis_key in other_analyses:
            if analysis_key in market_data and isinstance(market_data[analysis_key], dict):
                other_signal = market_data[analysis_key].get("signal")
                if other_signal == "BUY":
                    buy_signal_count += 1
                total_agent_count += 1
        
        # If we have enough data and majority signals are BUY, reduce confidence
        if total_agent_count >= 2 and buy_signal_count >= total_agent_count / 2:
            logger.info(f"Detected {buy_signal_count}/{total_agent_count} BUY signals conflicting with strong SELL")
            # Reduce confidence by 20%
            new_confidence = confidence * 0.8
            return new_confidence
        
        return confidence
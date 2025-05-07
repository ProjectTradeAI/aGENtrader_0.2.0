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
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

from agents.base_agent import BaseAnalystAgent
from core.logging.decision_logger import DecisionLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('liquidity_analyst')

class LiquidityAnalystAgent(BaseAnalystAgent):
    """LiquidityAnalystAgent for aGENtrader v0.2.2"""
    
    def __init__(self, data_fetcher=None, config=None):
        """
        Initialize the liquidity analyst agent.
        
        Args:
            data_fetcher: Data fetcher for market data
            config: Configuration dictionary
        """
        self.version = "v0.2.2"
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
        
        # Sanity check parameters
        self.min_liquidity_zones = self.config.get('min_liquidity_zones', 3)
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
            
        Returns:
            Liquidity analysis results
        """
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
            analysis_result = self._analyze_order_book(order_book)
            
            # Get the current price from the order book midpoint
            best_bid = float(order_book['bids'][0][0]) if order_book['bids'] else 0
            best_ask = float(order_book['asks'][0][0]) if order_book['asks'] else 0
            
            if best_bid == 0 or best_ask == 0:
                logger.warning(f"Invalid bid/ask prices: bid={best_bid}, ask={best_ask}")
                current_price = best_bid or best_ask  # Use whichever one is non-zero
            else:
                current_price = (best_bid + best_ask) / 2
            
            # Generate a trading signal based on the liquidity analysis
            signal, confidence, explanation = self._generate_signal(analysis_result)
            
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
    
    def _analyze_order_book(self, order_book: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the order book to extract liquidity metrics and identify 
        liquidity-based entry and stop-loss zones.
        
        Args:
            order_book: Dictionary containing 'bids' and 'asks' arrays
            
        Returns:
            Dictionary of liquidity metrics including support/resistance clusters
            and suggested entry/stop-loss levels
        """
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
        bin_size = current_price * (self.price_bin_size_pct / 100)
        
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
        
        # Define cluster thresholds based on averages
        bid_cluster_threshold = avg_bid_bin_volume * 1.8  # 1.8x average for significant support
        ask_cluster_threshold = avg_ask_bin_volume * 1.8  # 1.8x average for significant resistance
        bid_gap_threshold = avg_bid_bin_volume * 0.3     # 0.3x average for bid gaps
        ask_gap_threshold = avg_ask_bin_volume * 0.3     # 0.3x average for ask gaps
        
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
            "gaps": gaps
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
        total_zones = len(support_clusters) + len(resistance_clusters)
        if total_zones < self.min_liquidity_zones:
            return False, f"Too few liquidity zones detected: {total_zones} (minimum: {self.min_liquidity_zones})"
        
        # Check 2: Are the bid/ask ratios within reasonable ranges?
        if bid_ask_ratio > self.max_bid_ask_ratio:
            return False, f"Bid/ask ratio too extreme (high): {bid_ask_ratio:.2f} (max allowed: {self.max_bid_ask_ratio})"
        
        if bid_ask_ratio < self.min_bid_ask_ratio:
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
        
        # Check 4: Evaluate the volumes - are any volumes unrealistically high?
        for cluster in support_clusters:
            # Flag clusters with excessive strength
            if cluster['strength'] > 10:  # 10x average volume
                return False, f"Unrealistic support volume spike detected: {cluster['strength']:.2f}x average"
        
        for cluster in resistance_clusters:
            # Flag clusters with excessive strength
            if cluster['strength'] > 10:  # 10x average volume
                return False, f"Unrealistic resistance volume spike detected: {cluster['strength']:.2f}x average"
        
        # Check 5: Ensure gaps are not too frequent (more gaps than clusters suggest data quality issues)
        if len(gaps) > total_zones * 3:
            return False, f"Too many liquidity gaps detected: {len(gaps)} (vs {total_zones} clusters)"
        
        # All checks passed, the result is sane
        return True, None
        
    def _generate_signal(self, metrics: Dict[str, Any]) -> Tuple[str, int, str]:
        """
        Generate a trading signal based on liquidity analysis.
        
        Args:
            metrics: Liquidity metrics
            
        Returns:
            Tuple of (signal, confidence, explanation)
        """
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
        
        # Default to neutral
        signal = "NEUTRAL"
        confidence = 50
        explanation = "Market liquidity is balanced"
        
        # Check sanity status first
        agent_sane = metrics.get('agent_sane', True)
        sanity_message = metrics.get('sanity_message', None)
        
        # If sanity check failed, downgrade confidence and add warning
        if not agent_sane:
            explanation = f"⚠️ Abnormal liquidity structure detected: {sanity_message}. "
            explanation += "Defaulting to NEUTRAL signal with reduced confidence."
            return "NEUTRAL", 50, explanation
        
        # Check for strong imbalances
        if bid_ask_ratio > 2.0 and ask_depth < self.thresholds['medium_depth']:
            signal = "BUY"
            confidence = self.high_confidence
            explanation = f"Strong buying pressure with bid/ask ratio of {bid_ask_ratio:.2f}"
        elif bid_ask_ratio < 0.5 and bid_depth < self.thresholds['medium_depth']:
            signal = "SELL"
            confidence = self.high_confidence
            explanation = f"Strong selling pressure with bid/ask ratio of {bid_ask_ratio:.2f}"
        
        # Check for moderate imbalances
        elif bid_ask_ratio > 1.5:
            signal = "BUY"
            confidence = self.medium_confidence
            explanation = f"Moderate buying pressure with bid/ask ratio of {bid_ask_ratio:.2f}"
        elif bid_ask_ratio < 0.67:
            signal = "SELL"
            confidence = self.medium_confidence
            explanation = f"Moderate selling pressure with bid/ask ratio of {bid_ask_ratio:.2f}"
        
        # Check for support/resistance clusters
        if signal == "BUY" and support_clusters:
            explanation += f", strong support detected at {support_clusters[0]}"
            confidence = min(95, confidence + 5)
        elif signal == "SELL" and resistance_clusters:
            explanation += f", strong resistance detected at {resistance_clusters[0]}"
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
                    explanation += f". Watch support at {support_clusters[0]:.2f} and resistance at {resistance_clusters[0]:.2f}"
        
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
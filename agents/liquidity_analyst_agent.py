"""
Liquidity Analyst Agent Module

This agent analyzes market liquidity data including:
- Order book depth
- Volume profiles
- Funding rates
- Trading activity

The agent uses LLM-powered analysis to identify liquidity trends
and provide insights for trading decisions.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union

# Add parent directory to path to allow importing from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import required modules
from models.llm_client import LLMClient
from data.database import DatabaseConnector
from agents.base_agent import BaseAnalystAgent
from market_data_provider_factory import MarketDataProviderFactory

def json_serializable(obj):
    """Convert objects to JSON serializable types."""
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    else:
        return str(obj)

class LiquidityAnalystAgent(BaseAnalystAgent):
    """
    Liquidity Analyst Agent that analyzes market liquidity data.
    
    This agent:
    - Fetches liquidity-related data from the database
    - Processes and analyzes the data
    - Uses LLM for advanced liquidity insights
    - Returns structured analysis results
    """
    
    def __init__(self):
        """Initialize the Liquidity Analyst Agent."""
        # Initialize the base agent
        super().__init__()
        
        # Get agent and trading configuration
        self.agent_config = self.get_agent_config()
        self.trading_config = self.get_trading_config()
        
        # Initialize LLM client
        self.llm_client = LLMClient()
        
        # Initialize database connector
        self.db = DatabaseConnector()
        
        # Set default parameters
        self.default_symbol = self.trading_config.get("default_pair", "BTC/USDT").replace("/", "")
        
        # Use agent-specific timeframe from config if available
        liquidity_config = self.agent_config.get("liquidity_analyst", {})
        self.default_interval = liquidity_config.get("timeframe", self.trading_config.get("default_interval", "1h"))
        
        self.logger.info(f"Liquidity Analyst Agent initialized with symbol={self.default_symbol}, interval={self.default_interval}")
    
    def fetch_data(self, 
                  symbol: Optional[str] = None, 
                  interval: Optional[str] = None,
                  limit: int = 100) -> Dict[str, pd.DataFrame]:
        """
        Fetch all liquidity-related data for analysis.
        
        Args:
            symbol: Trading symbol (default from config)
            interval: Time interval (default from config)
            limit: Maximum number of records to retrieve
            
        Returns:
            Dictionary of DataFrames with liquidity data
        """
        symbol = symbol or self.default_symbol
        interval = interval or self.default_interval
        
        self.logger.info(f"Fetching liquidity data for {symbol} at {interval} interval")
        
        data_sources = self.agent_config.get("data_sources", [])
        result = {}
        
        # Connect to database - in demo mode, we'll proceed even if connection fails
        try:
            self.db.connect()
        except Exception as e:
            self.logger.warning(f"Database connection issue: {e}. Will proceed with limited data.")
        
        # Fetch data from each source
        try:
            if "market_depth" in data_sources:
                try:
                    # Ensure we have non-null values for the parameters
                    sym = str(symbol) if symbol is not None else str(self.default_symbol)
                    intv = str(interval) if interval is not None else str(self.default_interval)
                    
                    # Try fetching from database first
                    db_records = self.db.get_market_depth(sym, intv, limit)
                    
                    if db_records and len(db_records) > 0:
                        # Use data from database
                        result["market_depth"] = db_records
                        self.logger.info(f"Fetched {len(result['market_depth'])} market depth records from database")
                    else:
                        # Try direct Binance API call as backup
                        self.logger.info("No market depth data in database, fetching directly from Binance API")
                        
                        try:
                            # Create factory and fetch data
                            factory = MarketDataProviderFactory()
                            depth_data = factory.fetch_market_depth(sym, 100)  # Fetch top 100 bids and asks
                            
                            if depth_data and "bids" in depth_data and depth_data["bids"]:
                                self.logger.info(f"Successfully fetched market depth from Binance API")
                                result["market_depth"] = [depth_data]  # Store as a list with a single entry
                            else:
                                self.logger.warning("No valid market depth data returned from Binance API")
                                result["market_depth"] = []
                        except Exception as api_e:
                            self.logger.warning(f"Failed to fetch market depth from Binance API: {api_e}")
                            result["market_depth"] = []
                except Exception as e:
                    self.logger.warning(f"Could not fetch market depth data: {e}")
                    result["market_depth"] = []
            
            if "volume_profile" in data_sources:
                try:
                    # Ensure we have non-null values for the parameters
                    sym = str(symbol) if symbol is not None else str(self.default_symbol)
                    intv = str(interval) if interval is not None else str(self.default_interval)
                    # For volume profile, we'll use a shorter time period
                    result["volume_profile"] = self.db.get_volume_profile(sym, intv, "24h", limit)
                    self.logger.info(f"Fetched {len(result['volume_profile'])} volume profile records")
                except Exception as e:
                    self.logger.warning(f"Could not fetch volume profile data: {e}")
                    result["volume_profile"] = []
            
            if "funding_rates" in data_sources:
                try:
                    # Ensure we have non-null values for the parameters
                    sym = str(symbol) if symbol is not None else str(self.default_symbol)
                    result["funding_rates"] = self.db.get_funding_rates(sym, limit)
                    self.logger.info(f"Fetched {len(result.get('funding_rates', []))} funding rate records")
                except Exception as e:
                    self.logger.warning(f"Could not fetch funding rates data: {e}")
                    result["funding_rates"] = []
        
        except Exception as e:
            self.logger.warning(f"Error fetching liquidity data: {e}. Will continue with limited analysis.")
        
        finally:
            # Disconnect from database
            self.db.disconnect()
        
        return result
    
    def preprocess_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Preprocess and transform raw data for analysis.
        
        Args:
            data: Dictionary of DataFrames with raw data
            
        Returns:
            Dictionary with preprocessed data
        """
        self.logger.info("Preprocessing liquidity data")
        result = {}
        
        try:
            # Process market depth data
            if "market_depth" in data and not data["market_depth"].empty:
                md = data["market_depth"]
                
                # Calculate basic statistics
                result["depth_stats"] = {
                    "avg_bid_depth": md["bid_depth"].mean(),
                    "avg_ask_depth": md["ask_depth"].mean(),
                    "avg_bid_ask_ratio": md["bid_ask_ratio"].mean(),
                    "max_bid_depth": md["bid_depth"].max(),
                    "max_ask_depth": md["ask_depth"].max(),
                    "min_bid_ask_ratio": md["bid_ask_ratio"].min(),
                    "max_bid_ask_ratio": md["bid_ask_ratio"].max(),
                    "current_bid_ask_ratio": md.iloc[0]["bid_ask_ratio"] if len(md) > 0 else None
                }
                
                # Extract time series for visualization
                result["depth_time_series"] = md[["timestamp", "bid_depth", "ask_depth", "bid_ask_ratio"]].head(20).to_dict(orient="records")
            
            # Process volume profile data
            if "volume_profile" in data and not data["volume_profile"].empty:
                vp = data["volume_profile"]
                
                # Group by price level and aggregate volume
                volume_by_price = vp.groupby("price_level").agg({"volume": "sum"}).reset_index()
                
                # Find price levels with highest volume (liquidity zones)
                liquidity_zones = volume_by_price.nlargest(5, "volume")
                
                # Calculate buy/sell ratio
                buy_volume = vp[vp["is_buying"] == True]["volume"].sum()
                sell_volume = vp[vp["is_buying"] == False]["volume"].sum()
                buy_sell_ratio = buy_volume / sell_volume if sell_volume > 0 else float('inf')
                
                result["volume_stats"] = {
                    "liquidity_zones": liquidity_zones.to_dict(orient="records"),
                    "buy_volume": float(buy_volume),
                    "sell_volume": float(sell_volume),
                    "buy_sell_ratio": float(buy_sell_ratio),
                    "total_volume": float(vp["volume"].sum())
                }
            
            # Process funding rate data
            if "funding_rates" in data and not data["funding_rates"].empty:
                fr = data["funding_rates"]
                
                # Calculate statistics
                result["funding_stats"] = {
                    "latest_rate": float(fr.iloc[0]["rate"]) if "rate" in fr.columns and len(fr) > 0 else None,
                    "avg_rate": float(fr["rate"].mean()) if "rate" in fr.columns else None,
                    "positive_rate_count": int((fr["rate"] > 0).sum()) if "rate" in fr.columns else 0,
                    "negative_rate_count": int((fr["rate"] < 0).sum()) if "rate" in fr.columns else 0
                }
                
                # Extract time series
                result["funding_time_series"] = fr[["timestamp", "rate"]].head(20).to_dict(orient="records") if "rate" in fr.columns else []
        
        except Exception as e:
            self.logger.error(f"Error preprocessing data: {e}")
        
        return result
    
    def analyze_liquidity(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze preprocessed liquidity data using rule-based methods.
        
        Args:
            processed_data: Dictionary with preprocessed data
            
        Returns:
            Dictionary with analysis results
        """
        self.logger.info("Analyzing liquidity data")
        result = {"liquidity_indicators": {}}
        
        try:
            # Analyze market depth
            if "depth_stats" in processed_data:
                ds = processed_data["depth_stats"]
                
                # Determine bid/ask imbalance
                if ds["current_bid_ask_ratio"] is not None:
                    if ds["current_bid_ask_ratio"] > 1.2:
                        result["liquidity_indicators"]["bid_ask_imbalance"] = "bid-heavy"
                    elif ds["current_bid_ask_ratio"] < 0.8:
                        result["liquidity_indicators"]["bid_ask_imbalance"] = "ask-heavy"
                    else:
                        result["liquidity_indicators"]["bid_ask_imbalance"] = "balanced"
                
                # Determine overall depth
                if ds["avg_bid_depth"] + ds["avg_ask_depth"] > 1000000:  # Example threshold
                    result["liquidity_indicators"]["overall_depth"] = "high"
                elif ds["avg_bid_depth"] + ds["avg_ask_depth"] > 100000:  # Example threshold
                    result["liquidity_indicators"]["overall_depth"] = "medium"
                else:
                    result["liquidity_indicators"]["overall_depth"] = "low"
            
            # Analyze volume profile
            if "volume_stats" in processed_data:
                vs = processed_data["volume_stats"]
                
                # Determine buy/sell pressure
                if vs["buy_sell_ratio"] > 1.2:
                    result["liquidity_indicators"]["buy_sell_pressure"] = "buying"
                elif vs["buy_sell_ratio"] < 0.8:
                    result["liquidity_indicators"]["buy_sell_pressure"] = "selling"
                else:
                    result["liquidity_indicators"]["buy_sell_pressure"] = "neutral"
                
                # Determine volume significance
                if vs["total_volume"] > 1000000:  # Example threshold
                    result["liquidity_indicators"]["volume_significance"] = "high"
                elif vs["total_volume"] > 100000:  # Example threshold
                    result["liquidity_indicators"]["volume_significance"] = "medium"
                else:
                    result["liquidity_indicators"]["volume_significance"] = "low"
                
                # Extract liquidity zones
                if "liquidity_zones" in vs and vs["liquidity_zones"]:
                    result["liquidity_zones"] = vs["liquidity_zones"]
            
            # Analyze funding rates
            if "funding_stats" in processed_data:
                fs = processed_data["funding_stats"]
                
                # Determine funding rate sentiment
                if fs["latest_rate"] is not None:
                    if fs["latest_rate"] > 0.01:  # 1% positive
                        result["liquidity_indicators"]["funding_sentiment"] = "bullish"
                    elif fs["latest_rate"] < -0.01:  # 1% negative
                        result["liquidity_indicators"]["funding_sentiment"] = "bearish"
                    else:
                        result["liquidity_indicators"]["funding_sentiment"] = "neutral"
                
                # Determine funding rate trend
                if fs["positive_rate_count"] > fs["negative_rate_count"] * 2:
                    result["liquidity_indicators"]["funding_trend"] = "consistently positive"
                elif fs["negative_rate_count"] > fs["positive_rate_count"] * 2:
                    result["liquidity_indicators"]["funding_trend"] = "consistently negative"
                else:
                    result["liquidity_indicators"]["funding_trend"] = "mixed"
        
        except Exception as e:
            self.logger.error(f"Error analyzing data: {e}")
        
        return result
    
    def generate_llm_analysis(self, 
                            processed_data: Dict[str, Any], 
                            rule_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate advanced liquidity analysis using LLM.
        
        Args:
            processed_data: Dictionary with preprocessed data
            rule_analysis: Dictionary with rule-based analysis results
            
        Returns:
            Dictionary with LLM analysis results
        """
        self.logger.info("Generating LLM analysis for liquidity data")
        
        # Combine data for LLM analysis
        analysis_data = {
            "processed_data": processed_data,
            "rule_based_analysis": rule_analysis
        }
        
        # Prompt for LLM
        prompt = f"""
        As a liquidity analyst for cryptocurrency trading, analyze the following liquidity data:
        
        {json.dumps(analysis_data, default=json_serializable, indent=2)}
        
        Provide a comprehensive analysis of market liquidity conditions including:
        1. Overall liquidity assessment
        2. Bid/ask imbalances and their implications
        3. Volume distribution analysis
        4. Funding rate impact on market dynamics
        5. Key liquidity zones and their significance
        6. Overall liquidity score (0-100)
        
        Format your response as a JSON object with the following structure:
        {{
            "analysis": {{
                "overall_liquidity": "[high/medium/low]",
                "bid_ask_imbalance": "[bid-heavy/ask-heavy/balanced]",
                "volume_profile": "[above average/average/below average]",
                "depth_analysis": "[your detailed analysis here]",
                "funding_rate_impact": "[your analysis here]",
                "liquidity_score": [0-100]
            }},
            "interpretation": "[summary of what the liquidity conditions mean]",
            "recommendation": "[trading recommendation based on liquidity]"
        }}
        """
        
        try:
            # Get analysis from LLM
            response = self.llm_client.generate(prompt)
            
            # Parse response
            try:
                # Try to extract JSON if response contains other text
                if "{" in response and "}" in response:
                    import re
                    json_match = re.search(r'({.*})', response.replace('\n', ' '), re.DOTALL)
                    if json_match:
                        response = json_match.group(1)
                
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response as JSON: {e}")
                return {"error": "Failed to parse LLM response", "raw_response": response}
        
        except Exception as e:
            self.logger.error(f"Error getting LLM analysis: {e}")
            return {"error": f"Error generating LLM analysis: {str(e)}"}
    
    def analyze(self, 
               symbol: Optional[str] = None, 
               interval: Optional[str] = None,
               market_data: Optional[Dict[str, Any]] = None,
               **kwargs) -> Dict[str, Any]:
        """
        Perform complete liquidity analysis.
        
        Args:
            symbol: Trading symbol (default from config)
            interval: Time interval (default from config)
            market_data: Optional market data from live feed (contains orderbook data)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with complete analysis results
        """
        # Use the default symbol if none provided
        symbol = symbol or self.default_symbol
        
        # Use agent-specific timeframe if none provided
        interval = interval or self.default_interval
        
        # Standard BTC/USDT format for logging, but use BTCUSDT format for API calls
        display_symbol = str(symbol) if symbol is not None else "UNKNOWN"
        if "/" not in display_symbol and len(display_symbol) > 3:
            # If we have BTCUSDT format, convert to BTC/USDT for display
            if display_symbol.endswith("USDT"):
                base = display_symbol[:-4]
                display_symbol = f"{base}/USDT"
        
        self.logger.info(f"Starting liquidity analysis for {display_symbol} at {interval} interval")
        
        # Step 1: Get orderbook data - try multiple sources in order of preference
        depth_data = None
        
        # 1.1: Try live market data first if available
        if market_data and 'orderbook' in market_data and market_data['orderbook']:
            depth_data = market_data['orderbook']
            self.logger.info("Using provided live orderbook data for analysis")
        
        # 1.2: If no live data, try our fetch_data method which attempts DB and then Binance API
        if not depth_data:
            raw_data = self.fetch_data(symbol, interval)
            
            # Check if we got market depth data
            if "market_depth" in raw_data and raw_data["market_depth"]:
                if isinstance(raw_data["market_depth"], list) and len(raw_data["market_depth"]) > 0:
                    if isinstance(raw_data["market_depth"][0], dict) and "bids" in raw_data["market_depth"][0]:
                        depth_data = raw_data["market_depth"][0]
                        self.logger.info("Using market depth data from fetch_data method")
                    else:
                        self.logger.warning("Market depth data found but in invalid format")
        
        # 1.3: If still no depth data, try direct Binance API call
        if not depth_data:
            try:
                self.logger.info("Attempting direct Binance API call for market depth")
                factory = MarketDataProviderFactory()
                # Ensure we have a valid symbol string
                if not symbol:
                    symbol = self.default_symbol
                formatted_symbol = symbol.replace("/", "") if "/" in symbol else symbol
                depth_data = factory.fetch_market_depth(formatted_symbol, 100)
                
                if depth_data and "bids" in depth_data and len(depth_data["bids"]) > 0:
                    self.logger.info("Successfully obtained market depth from direct Binance API call")
                else:
                    self.logger.warning("Direct API call returned no valid market depth data")
                    depth_data = None
            except Exception as e:
                self.logger.error(f"Direct Binance API call failed: {e}")
                depth_data = None
        
        # Check if we have valid depth data
        if not depth_data or not isinstance(depth_data, dict) or "bids" not in depth_data or "asks" not in depth_data:
            self.logger.warning(f"No valid market depth data available for {display_symbol} at {interval} interval")
            return {
                "symbol": display_symbol,
                "interval": interval,
                "error": "No liquidity data available for analysis",
                "signal": "NEUTRAL",  # Default to NEUTRAL on error
                "confidence": 50,
                "reason": "No liquidity data available for analysis"
            }
        
        # Step 2: Analyze market depth directly
        try:
            # Extract key metrics from depth data
            bids = depth_data.get("bids", [])
            asks = depth_data.get("asks", [])
            
            # Ensure we have data to work with
            if not bids or not asks:
                self.logger.warning(f"Empty bids or asks in market depth data for {display_symbol}")
                return {
                    "symbol": display_symbol,
                    "interval": interval,
                    "error": "Empty order book data",
                    "signal": "NEUTRAL",
                    "confidence": 50,
                    "reason": "Order book data contains empty bids or asks"
                }
            
            # Calculate key metrics
            bid_total = depth_data.get("bid_total", 0)
            ask_total = depth_data.get("ask_total", 0)
            
            # If totals not pre-calculated, calculate them
            if bid_total == 0 and len(bids) > 0:
                bid_total = sum(float(bid[0]) * float(bid[1]) for bid in bids)
            
            if ask_total == 0 and len(asks) > 0:
                ask_total = sum(float(ask[0]) * float(ask[1]) for ask in asks)
            
            # Calculate top 5 volumes if not provided
            top_5_bid_volume = depth_data.get("top_5_bid_volume", 0)
            top_5_ask_volume = depth_data.get("top_5_ask_volume", 0)
            
            if top_5_bid_volume == 0 and len(bids) >= 5:
                top_5_bid_volume = sum(float(bid[0]) * float(bid[1]) for bid in bids[:5])
            
            if top_5_ask_volume == 0 and len(asks) >= 5:
                top_5_ask_volume = sum(float(ask[0]) * float(ask[1]) for ask in asks[:5])
            
            # Calculate mid price and spread
            if len(bids) > 0 and len(asks) > 0:
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                mid_price = (best_bid + best_ask) / 2
                spread = best_ask - best_bid
                spread_percent = (spread / mid_price) * 100
            else:
                mid_price = 0
                spread = 0
                spread_percent = 0
            
            # Calculate bid/ask imbalance
            bid_ask_ratio = bid_total / ask_total if ask_total > 0 else 1.0
            top_5_bid_ask_ratio = top_5_bid_volume / top_5_ask_volume if top_5_ask_volume > 0 else 1.0
            
            # Determine signal based on order book imbalance
            signal = "NEUTRAL"
            confidence = 50
            reason = "Order book is balanced"
            
            # Check if we have strong buy/sell signals from top 5 levels (more accurate)
            if top_5_bid_volume > 0 and top_5_ask_volume > 0:
                if top_5_bid_ask_ratio > 1.2:  # 20% more bid volume than ask
                    strength = min(100, int(50 + (top_5_bid_ask_ratio - 1.0) * 100))
                    signal = "BUY"
                    confidence = min(95, strength)
                    reason = f"Strong buying pressure in order book (bid/ask ratio: {top_5_bid_ask_ratio:.2f})"
                    self.logger.info(f"Detected BUY signal from top 5 order book levels with {confidence}% confidence")
                    
                elif top_5_bid_ask_ratio < 0.8:  # 20% more ask volume than bid
                    strength = min(100, int(50 + (1.0 - top_5_bid_ask_ratio) * 100))
                    signal = "SELL"
                    confidence = min(95, strength)
                    reason = f"Strong selling pressure in order book (bid/ask ratio: {top_5_bid_ask_ratio:.2f})"
                    self.logger.info(f"Detected SELL signal from top 5 order book levels with {confidence}% confidence")
                    
                else:
                    # Balanced order book
                    signal = "HOLD"
                    confidence = int(70 - abs(1.0 - top_5_bid_ask_ratio) * 20)
                    reason = f"Order book is relatively balanced (bid/ask ratio: {top_5_bid_ask_ratio:.2f})"
                    self.logger.info(f"Detected HOLD signal from order book with {confidence}% confidence")
            
            # If no strong signal from top 5 levels, check overall book
            elif bid_total > 0 and ask_total > 0:
                if bid_ask_ratio > 1.2:
                    signal = "BUY"
                    confidence = min(85, int(50 + (bid_ask_ratio - 1.0) * 50))
                    reason = f"More buy orders than sell orders (bid/ask ratio: {bid_ask_ratio:.2f})"
                elif bid_ask_ratio < 0.8:
                    signal = "SELL"
                    confidence = min(85, int(50 + (1.0 - bid_ask_ratio) * 50))
                    reason = f"More sell orders than buy orders (bid/ask ratio: {bid_ask_ratio:.2f})"
                else:
                    signal = "HOLD"
                    confidence = 60
                    reason = "Order book is balanced"
            
            # Create detailed analysis with all available metrics
            liquidity_indicators = {
                "bid_total": bid_total,
                "ask_total": ask_total,
                "bid_ask_ratio": bid_ask_ratio,
                "top_5_bid_volume": top_5_bid_volume,
                "top_5_ask_volume": top_5_ask_volume,
                "top_5_bid_ask_ratio": top_5_bid_ask_ratio,
                "mid_price": mid_price,
                "spread": spread,
                "spread_percent": spread_percent,
                "bids_count": len(bids),
                "asks_count": len(asks)
            }
            
            # Prepare final result
            result = {
                "symbol": display_symbol,
                "interval": interval,
                "signal": signal,
                "confidence": confidence,
                "reason": reason,
                "liquidity_indicators": liquidity_indicators,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Liquidity analysis complete for {display_symbol}: {signal} with {confidence}% confidence")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing market depth data: {e}", exc_info=True)
            return {
                "symbol": display_symbol,
                "interval": interval,
                "error": f"Analysis failed: {str(e)}",
                "signal": "NEUTRAL",
                "confidence": 50,
                "reason": "Error in liquidity analysis"
            }

# Example usage (for demonstration)
if __name__ == "__main__":
    # Create agent
    agent = LiquidityAnalystAgent()
    
    # Run analysis
    analysis = agent.analyze("BTCUSDT", "1h")
    
    # Print results
    print(json.dumps(analysis, default=json_serializable, indent=2))
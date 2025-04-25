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
        self.default_interval = self.trading_config.get("default_interval", "1h")
        
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
        
        # Connect to database
        if not self.db.connect():
            self.logger.error("Failed to connect to database")
            return {}
        
        # Fetch data from each source
        try:
            if "market_depth" in data_sources:
                result["market_depth"] = self.db.get_market_depth(symbol, interval, limit)
                self.logger.info(f"Fetched {len(result['market_depth'])} market depth records")
            
            if "volume_profile" in data_sources:
                # For volume profile, we'll use a shorter time period
                result["volume_profile"] = self.db.get_volume_profile(symbol, interval, "24h", limit)
                self.logger.info(f"Fetched {len(result['volume_profile'])} volume profile records")
            
            if "funding_rates" in data_sources:
                result["funding_rates"] = self.db.get_funding_rates(symbol, limit)
                self.logger.info(f"Fetched {len(result.get('funding_rates', []))} funding rate records")
        
        except Exception as e:
            self.logger.error(f"Error fetching data: {e}")
        
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
        symbol = symbol or self.default_symbol
        interval = interval or self.default_interval
        
        self.logger.info(f"Starting liquidity analysis for {symbol} at {interval} interval")
        
        # Step 1: Get data - either from market_data or fetch from database
        raw_data = {}
        
        if market_data and 'orderbook' in market_data and market_data['orderbook']:
            # Use live market data if provided
            self.logger.info("Using provided live orderbook data for analysis")
            
            try:
                # First, fetch baseline data
                raw_data = self.fetch_data(symbol, interval)
                
                # Then, add/update with live orderbook data
                orderbook = market_data['orderbook']
                
                # Convert the orderbook data to the format expected by our analysis methods
                orderbook_data = pd.DataFrame({
                    'timestamp': [pd.Timestamp(orderbook.get('timestamp', pd.Timestamp.now().isoformat()))],
                    'bid_total': [float(orderbook.get('bid_total', 0))],
                    'ask_total': [float(orderbook.get('ask_total', 0))],
                    'bid_ask_ratio': [float(orderbook.get('bid_ask_ratio', 1.0))]
                })
                
                # Add bids and asks as separate DataFrames if needed
                bids_data = pd.DataFrame(orderbook.get('bids', []))
                asks_data = pd.DataFrame(orderbook.get('asks', []))
                
                # Update raw_data with live orderbook
                raw_data['orderbook'] = orderbook_data
                if not bids_data.empty:
                    raw_data['bids'] = bids_data
                if not asks_data.empty:
                    raw_data['asks'] = asks_data
                
                # Add ticker data if available
                if 'ticker' in market_data and market_data['ticker']:
                    ticker = market_data['ticker']
                    ticker_data = pd.DataFrame({
                        'timestamp': [pd.Timestamp(ticker.get('timestamp', pd.Timestamp.now().isoformat()))],
                        'price': [float(ticker.get('price', 0))],
                        'bid': [float(ticker.get('bid', 0))],
                        'ask': [float(ticker.get('ask', 0))],
                        'bid_size': [float(ticker.get('bid_size', 0))],
                        'ask_size': [float(ticker.get('ask_size', 0))]
                    })
                    raw_data['ticker'] = ticker_data
                
            except Exception as e:
                self.logger.error(f"Error processing live orderbook data: {e}")
                # Fall back to just fetching data from database
                raw_data = self.fetch_data(symbol, interval)
        else:
            # Fetch data from database if no live data provided
            raw_data = self.fetch_data(symbol, interval)
        
        # Check if we have data
        if not raw_data or all(df.empty for df in raw_data.values() if hasattr(df, 'empty')):
            self.logger.warning(f"No data available for {symbol} at {interval} interval")
            return self.validate_result({
                "symbol": symbol,
                "interval": interval,
                "error": "No data available for analysis"
            })
        
        # Step 2: Preprocess data
        processed_data = self.preprocess_data(raw_data)
        
        # Step 3: Rule-based analysis
        rule_analysis = self.analyze_liquidity(processed_data)
        
        # Step 4: LLM-enhanced analysis
        llm_analysis = self.generate_llm_analysis(processed_data, rule_analysis)
        
        # Step 5: Combine results
        result = {
            "symbol": symbol,
            "interval": interval,
            "timestamp": self.format_timestamp(),
            "rule_analysis": rule_analysis,
            "llm_analysis": llm_analysis
        }
        
        self.logger.info(f"Completed liquidity analysis for {symbol}")
        
        # Validate and return the result
        return self.validate_result(result)

# Example usage (for demonstration)
if __name__ == "__main__":
    # Create agent
    agent = LiquidityAnalystAgent()
    
    # Run analysis
    analysis = agent.analyze("BTCUSDT", "1h")
    
    # Print results
    print(json.dumps(analysis, default=json_serializable, indent=2))
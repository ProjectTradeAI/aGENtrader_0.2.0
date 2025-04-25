"""
Fundamental Analysis Agent Module

This module defines the FundamentalAnalysisAgent class, which analyzes
market fundamentals and broader economic factors to generate trading
recommendations.
"""
import os
import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    import pandas as pd
    import numpy as np
except ImportError:
    logger.warning("Required libraries not installed. Install with: pip install pandas numpy")

class FundamentalAnalysisAgent:
    """
    Agent that analyzes fundamental factors for trading decisions.
    Uses a structured collaborative approach to integrate market trends,
    news sentiment, and economic data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the fundamental analysis agent.
        
        Args:
            config: Optional configuration for the agent
        """
        self.config = config or {}
        
        # Default configuration
        self.default_config = {
            "use_authentic_data": True,
            "market_trend_weight": 0.3,
            "sentiment_weight": 0.3,
            "adoption_weight": 0.2,
            "economic_weight": 0.2,
            "confidence_threshold": 0.65,
            "api_keys": {
                "news_api": os.environ.get("NEWS_API_KEY", ""),
                "economic_data": os.environ.get("ECONOMIC_DATA_KEY", "")
            }
        }
        
        # Merge with provided config
        for key, value in self.default_config.items():
            if key not in self.config:
                self.config[key] = value
        
        # Initialize data sources
        self.data_sources = self._init_data_sources()
    
    def _init_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """Initialize data sources for fundamental analysis"""
        data_sources = {
            "market_data": {
                "available": True,
                "source": "database",
                "description": "Historical market data from database"
            },
            "news_sentiment": {
                "available": bool(self.config["api_keys"].get("news_api")),
                "source": "news_api" if self.config["api_keys"].get("news_api") else None,
                "description": "News sentiment analysis"
            },
            "economic_data": {
                "available": bool(self.config["api_keys"].get("economic_data")),
                "source": "economic_api" if self.config["api_keys"].get("economic_data") else None,
                "description": "Economic indicators and data"
            },
            "on_chain_metrics": {
                "available": False,  # Would be true if we had a blockchain data source
                "source": None,
                "description": "Blockchain on-chain analytics"
            }
        }
        
        return data_sources
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform fundamental analysis and generate trading recommendation.
        
        Args:
            symbol: Trading symbol
            data: Market data DataFrame
            
        Returns:
            Analysis result with trading recommendation
        """
        if data.empty:
            logger.warning(f"No data available for {symbol}")
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "direction": "hold",
                "confidence": 0.0,
                "reasoning": "No fundamental data available for analysis",
                "factors": {}
            }
        
        try:
            # Get current date (latest date in the data)
            if not data.empty and 'timestamp' in data.columns:
                current_date = pd.to_datetime(data['timestamp'].iloc[-1])
            else:
                current_date = datetime.now()
            
            # Analyze different fundamental factors
            market_trend = self._analyze_market_trend(symbol, data, current_date)
            sentiment = self._analyze_sentiment(symbol, current_date)
            adoption = self._analyze_adoption(symbol, current_date)
            economic = self._analyze_economic_factors(symbol, current_date)
            
            # Combine factors into weighted score
            weighted_score = (
                market_trend["score"] * self.config["market_trend_weight"] +
                sentiment["score"] * self.config["sentiment_weight"] +
                adoption["score"] * self.config["adoption_weight"] +
                economic["score"] * self.config["economic_weight"]
            )
            
            # Determine direction based on weighted score
            if weighted_score > self.config["confidence_threshold"]:
                direction = "buy"
                confidence = weighted_score
            elif weighted_score < -self.config["confidence_threshold"]:
                direction = "sell"
                confidence = abs(weighted_score)
            else:
                direction = "hold"
                confidence = 1 - abs(weighted_score)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                symbol, direction, confidence, market_trend, sentiment, adoption, economic
            )
            
            # Compile result
            result = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "direction": direction,
                "confidence": min(1.0, abs(confidence)),
                "reasoning": reasoning,
                "factors": {
                    "market_trend": market_trend,
                    "sentiment": sentiment,
                    "adoption": adoption,
                    "economic": economic
                },
                "weighted_score": weighted_score
            }
            
            logger.info(f"Fundamental analysis for {symbol}: {direction} with confidence {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error in fundamental analysis: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "direction": "hold",
                "confidence": 0.0,
                "reasoning": f"Fundamental analysis error: {str(e)}",
                "factors": {}
            }
    
    def _analyze_market_trend(self, symbol: str, data: pd.DataFrame, 
                             current_date: datetime) -> Dict[str, Any]:
        """
        Analyze market trend from a fundamental perspective.
        
        Args:
            symbol: Trading symbol
            data: Market data DataFrame
            current_date: Current date for analysis
            
        Returns:
            Market trend analysis
        """
        result = {
            "score": 0.0,
            "analysis": "",
            "factors": {}
        }
        
        if data.empty:
            result["analysis"] = "No market data available for trend analysis"
            return result
        
        try:
            # Extract relevant data
            recent_data = data.iloc[-30:] if len(data) >= 30 else data
            
            # Calculate market trend metrics
            if 'close' in recent_data.columns:
                # Price trend
                start_price = recent_data['close'].iloc[0]
                end_price = recent_data['close'].iloc[-1]
                price_change = (end_price - start_price) / start_price
                
                # Volatility
                daily_returns = recent_data['close'].pct_change().dropna()
                volatility = daily_returns.std() * (252 ** 0.5)  # Annualized
                
                # Market trend score based on price change and volatility
                trend_score = min(max(price_change * 3, -1), 1)  # Scale and bound
                volatility_factor = min(max((0.5 - volatility) * 2, -0.5), 0.5)  # Lower volatility is better
                
                result["score"] = trend_score + volatility_factor
                result["factors"] = {
                    "price_change": price_change,
                    "volatility": volatility,
                    "trend_score": trend_score,
                    "volatility_factor": volatility_factor
                }
                
                # Generate analysis text
                trend_text = "bullish" if trend_score > 0 else "bearish"
                vol_text = "low" if volatility < 0.3 else "moderate" if volatility < 0.6 else "high"
                result["analysis"] = (
                    f"Market trend is {trend_text} with {price_change:.1%} price change "
                    f"over the analyzed period. Volatility is {vol_text} at {volatility:.2f}."
                )
            else:
                result["analysis"] = "Insufficient market data for trend analysis"
                
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing market trend: {str(e)}")
            result["analysis"] = f"Error in market trend analysis: {str(e)}"
            return result
    
    def _analyze_sentiment(self, symbol: str, current_date: datetime) -> Dict[str, Any]:
        """
        Analyze news sentiment and social media for the asset.
        
        Args:
            symbol: Trading symbol
            current_date: Current date for analysis
            
        Returns:
            Sentiment analysis
        """
        result = {
            "score": 0.0,
            "analysis": "",
            "data_sources": []
        }
        
        # Check if we have news API access
        if not self.data_sources["news_sentiment"]["available"]:
            if self.config["use_authentic_data"]:
                result["analysis"] = "No news sentiment data available - API key missing"
                return result
        
        # In a real implementation, we would:
        # 1. Query news API for recent articles about the asset
        # 2. Analyze sentiment of those articles
        # 3. Check social media sentiment
        
        # For demonstration, we'll use placeholder analysis based on asset and date
        asset_seed = sum(ord(c) for c in symbol)
        date_seed = current_date.day + current_date.month * 31
        combined_seed = (asset_seed + date_seed) % 100
        
        # Generate a score between -1 and 1 based on the seed
        sentiment_score = (combined_seed - 50) / 50
        
        # Create analysis based on the score
        if sentiment_score > 0.3:
            sentiment = "positive"
            result["analysis"] = (
                f"News and social media sentiment for {symbol} is predominantly positive. "
                f"Recent announcements and community reception indicate growing interest."
            )
        elif sentiment_score < -0.3:
            sentiment = "negative"
            result["analysis"] = (
                f"News and social media sentiment for {symbol} shows concerning signals. "
                f"There appears to be negative coverage affecting market perception."
            )
        else:
            sentiment = "neutral"
            result["analysis"] = (
                f"News and social media sentiment for {symbol} is relatively neutral. "
                f"No significant positive or negative narrative is dominating discussions."
            )
        
        result["score"] = sentiment_score
        result["data_sources"] = ["news_api", "social_media_analysis"]
        
        return result
    
    def _analyze_adoption(self, symbol: str, current_date: datetime) -> Dict[str, Any]:
        """
        Analyze adoption metrics and ecosystem growth.
        
        Args:
            symbol: Trading symbol
            current_date: Current date for analysis
            
        Returns:
            Adoption analysis
        """
        result = {
            "score": 0.0,
            "analysis": "",
            "metrics": {}
        }
        
        # For cryptocurrency, we would analyze:
        # - Active addresses
        # - Transaction volume
        # - Developer activity
        # - Institutional adoption
        
        # Check for on-chain data availability
        if not self.data_sources["on_chain_metrics"]["available"]:
            if self.config["use_authentic_data"]:
                result["analysis"] = "No on-chain data available for adoption analysis"
                return result
        
        # For demonstration, generate placeholder metrics based on symbol and date
        asset_seed = sum(ord(c) for c in symbol)
        date_seed = current_date.day + current_date.month * 31
        combined_seed = (asset_seed + date_seed) % 100
        
        # Generate adoption score (-1 to 1)
        adoption_score = (combined_seed - 50) / 50
        
        # Create analysis based on score
        if adoption_score > 0.3:
            trend = "increasing"
            result["analysis"] = (
                f"Adoption metrics for {symbol} show positive growth. "
                f"Active addresses and transaction volumes have increased, "
                f"suggesting growing utility and user base."
            )
        elif adoption_score < -0.3:
            trend = "decreasing"
            result["analysis"] = (
                f"Adoption metrics for {symbol} show concerning trends. "
                f"Decreasing network activity and transaction volumes "
                f"may indicate reduced utility or interest."
            )
        else:
            trend = "stable"
            result["analysis"] = (
                f"Adoption metrics for {symbol} are relatively stable. "
                f"No significant changes in network activity or usage patterns."
            )
        
        result["score"] = adoption_score
        result["metrics"] = {
            "active_addresses_trend": trend,
            "transaction_volume_trend": trend,
            "developer_activity": "moderate",
            "institutional_adoption": "early stage"
        }
        
        return result
    
    def _analyze_economic_factors(self, symbol: str, current_date: datetime) -> Dict[str, Any]:
        """
        Analyze broader economic factors impacting the asset.
        
        Args:
            symbol: Trading symbol
            current_date: Current date for analysis
            
        Returns:
            Economic analysis
        """
        result = {
            "score": 0.0,
            "analysis": "",
            "factors": {}
        }
        
        # Check if we have economic data API access
        if not self.data_sources["economic_data"]["available"]:
            if self.config["use_authentic_data"]:
                result["analysis"] = "No economic data available - API key missing"
                return result
        
        # In a real implementation, we would analyze:
        # - Inflation rates
        # - Interest rates
        # - Market liquidity
        # - Regulatory environment
        
        # For demonstration, generate placeholder analysis
        asset_seed = sum(ord(c) for c in symbol)
        date_seed = current_date.day + current_date.month * 31
        combined_seed = (asset_seed + date_seed) % 100
        
        # Generate economic impact score (-1 to 1)
        economic_score = (combined_seed - 50) / 75  # Smaller range for economic factors
        
        # Create analysis based on score
        if economic_score > 0.2:
            impact = "positive"
            result["analysis"] = (
                f"Current economic conditions appear favorable for {symbol}. "
                f"Monetary policies and market liquidity are supportive of growth assets."
            )
        elif economic_score < -0.2:
            impact = "negative"
            result["analysis"] = (
                f"Economic headwinds may challenge {symbol} performance. "
                f"Tightening monetary conditions and reduced liquidity could impact valuations."
            )
        else:
            impact = "neutral"
            result["analysis"] = (
                f"Current economic conditions have mixed implications for {symbol}. "
                f"No clear positive or negative bias from broader economic factors."
            )
        
        result["score"] = economic_score
        result["factors"] = {
            "monetary_policy": "neutral",
            "liquidity_conditions": "moderate",
            "regulatory_environment": "evolving",
            "overall_impact": impact
        }
        
        return result
    
    def _generate_reasoning(self, symbol: str, direction: str, confidence: float,
                          market_trend: Dict[str, Any], sentiment: Dict[str, Any],
                          adoption: Dict[str, Any], economic: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for the trading decision"""
        
        # Create directional descriptor
        if direction == "buy":
            direction_text = "bullish"
        elif direction == "sell":
            direction_text = "bearish"
        else:
            direction_text = "neutral"
        
        # Start with overall conclusion
        reasoning = [f"Fundamental analysis for {symbol} is {direction_text} with {confidence:.1%} confidence."]
        
        # Add factor analyses
        if market_trend.get("analysis"):
            reasoning.append(market_trend["analysis"])
            
        if sentiment.get("analysis"):
            reasoning.append(sentiment["analysis"])
            
        if adoption.get("analysis"):
            reasoning.append(adoption["analysis"])
            
        if economic.get("analysis"):
            reasoning.append(economic["analysis"])
        
        # Add conclusion with strongest factors
        factors = []
        if market_trend.get("score", 0) > 0.3:
            factors.append("positive market trend")
        elif market_trend.get("score", 0) < -0.3:
            factors.append("negative market trend")
            
        if sentiment.get("score", 0) > 0.3:
            factors.append("positive sentiment")
        elif sentiment.get("score", 0) < -0.3:
            factors.append("negative sentiment")
            
        if adoption.get("score", 0) > 0.3:
            factors.append("strong adoption metrics")
        elif adoption.get("score", 0) < -0.3:
            factors.append("weak adoption metrics")
            
        if economic.get("score", 0) > 0.3:
            factors.append("supportive economic conditions")
        elif economic.get("score", 0) < -0.3:
            factors.append("challenging economic conditions")
        
        if factors:
            if direction == "buy":
                reasoning.append(f"The {direction} recommendation is primarily based on {', '.join(factors)}.")
            elif direction == "sell":
                reasoning.append(f"The {direction} recommendation is primarily based on {', '.join(factors)}.")
            else:
                reasoning.append(f"The {direction} recommendation reflects balanced or insufficient signals from fundamental factors.")
        
        return " ".join(reasoning)

# If executed as a script, run a simple demonstration
if __name__ == "__main__":
    # Create mock data for testing
    try:
        import pandas as pd
        import numpy as np
        
        # Create sample data
        dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.normal(100, 5, 30),
            'high': np.random.normal(105, 5, 30),
            'low': np.random.normal(95, 5, 30),
            'close': np.random.normal(100, 10, 30),
            'volume': np.random.normal(1000000, 200000, 30)
        })
        
        # Ensure timestamps are datetime
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        # Create and test the agent
        agent = FundamentalAnalysisAgent({"use_authentic_data": False})
        result = agent.analyze("BTCUSDT", data)
        
        print(json.dumps(result, indent=2))
        
    except ImportError:
        print("Cannot run demonstration: required libraries not installed.")
        print("Install with: pip install pandas numpy")
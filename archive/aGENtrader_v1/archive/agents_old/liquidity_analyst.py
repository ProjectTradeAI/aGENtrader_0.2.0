"""
Liquidity Analyst Agent

This module defines the Liquidity Analyst agent, which specializes in analyzing
market liquidity conditions, including order book depth, funding rates, futures basis,
and exchange flows.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union, Callable

from agents.database_retrieval_tool import CustomJSONEncoder
from agents.liquidity_data import (
    get_exchange_flows,
    get_funding_rates,
    get_market_depth,
    get_futures_basis,
    get_volume_profile,
    get_liquidity_summary
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("liquidity_analyst")

class LiquidityAnalyst:
    """
    Liquidity Analyst agent for analyzing market liquidity conditions.
    
    This agent specializes in analyzing:
    - Order book depth and imbalances
    - Funding rates in perpetual futures markets
    - Futures basis and term structure
    - Exchange inflow/outflow patterns
    - Volume distribution across price levels
    """
    
    def __init__(self):
        """Initialize the Liquidity Analyst agent"""
        logger.info("Initializing Liquidity Analyst agent")
    
    def analyze_exchange_flows(self, symbol: str, exchange: Optional[str] = None, 
                            interval: str = "1d", days: int = 7) -> Dict[str, Any]:
        """
        Analyze exchange flow patterns.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name (or None for all exchanges)
            interval: Data interval
            days: Number of days to analyze
            
        Returns:
            Analysis results
        """
        try:
            # Get exchange flow data
            data_json = get_exchange_flows(symbol, exchange, interval, days)
            if not data_json:
                return {"error": "Failed to retrieve exchange flow data"}
            
            data = json.loads(data_json)
            if not data or not data.get("data"):
                return {"error": "No exchange flow data available"}
            
            # Analyze exchange flow trends
            flow_data = data.get("data", [])
            
            # Calculate net flow trend
            if len(flow_data) >= 2:
                latest_flow = flow_data[0]
                oldest_flow = flow_data[-1]
                
                net_flow_change = float(latest_flow["net_flow"]) - float(oldest_flow["net_flow"])
                
                trend = "accumulation" if net_flow_change < 0 else "distribution" if net_flow_change > 0 else "neutral"
            else:
                trend = "insufficient data"
            
            # Calculate aggregates
            inflow_total = sum(float(item["inflow"]) for item in flow_data)
            outflow_total = sum(float(item["outflow"]) for item in flow_data)
            net_flow_total = inflow_total - outflow_total
            
            # Generate analysis
            analysis = {
                "symbol": symbol,
                "exchange": exchange if exchange else "all",
                "interval": interval,
                "days_analyzed": days,
                "data_points": len(flow_data),
                "net_flow_trend": trend,
                "aggregates": {
                    "inflow_total": inflow_total,
                    "outflow_total": outflow_total,
                    "net_flow_total": net_flow_total
                },
                "interpretation": "bullish" if trend == "accumulation" else "bearish" if trend == "distribution" else "neutral"
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing exchange flows: {str(e)}")
            return {"error": f"Error analyzing exchange flows: {str(e)}"}
    
    def analyze_funding_rates(self, symbol: str, exchange: Optional[str] = None,
                           interval: str = "8h", limit: int = 10) -> Dict[str, Any]:
        """
        Analyze funding rate patterns.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name (or None for all exchanges)
            interval: Data interval
            limit: Number of data points to analyze
            
        Returns:
            Analysis results
        """
        try:
            # Get funding rate data
            data_json = get_funding_rates(symbol, exchange, interval, limit)
            if not data_json:
                return {"error": "Failed to retrieve funding rate data"}
            
            data = json.loads(data_json)
            if not data or not data.get("data"):
                return {"error": "No funding rate data available"}
            
            # Analyze funding rate trends
            rate_data = data.get("data", [])
            
            # Calculate average funding rate
            average_rate = data.get("average_funding_rate", 0)
            
            # Calculate rate trend
            if len(rate_data) >= 2:
                latest_rate = float(rate_data[0]["funding_rate"])
                oldest_rate = float(rate_data[-1]["funding_rate"])
                
                rate_change = latest_rate - oldest_rate
                rate_trend = "increasing" if rate_change > 0 else "decreasing" if rate_change < 0 else "stable"
            else:
                rate_trend = "insufficient data"
            
            # Generate analysis
            analysis = {
                "symbol": symbol,
                "exchange": exchange if exchange else "all",
                "interval": interval,
                "data_points": len(rate_data),
                "average_funding_rate": average_rate,
                "annualized_rate": data.get("annualized_rate", 0),
                "latest_rate": data.get("latest_funding_rate", 0),
                "rate_trend": rate_trend,
                "interpretation": self._interpret_funding_rate(average_rate, rate_trend)
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing funding rates: {str(e)}")
            return {"error": f"Error analyzing funding rates: {str(e)}"}
    
    def analyze_market_depth(self, symbol: str, exchange: Optional[str] = None,
                          interval: str = "5m", limit: int = 10) -> Dict[str, Any]:
        """
        Analyze order book depth patterns.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name (or None for all exchanges)
            interval: Data interval
            limit: Number of data points to analyze
            
        Returns:
            Analysis results
        """
        try:
            # Get market depth data
            data_json = get_market_depth(symbol, exchange, None, interval, limit)
            if not data_json:
                return {"error": "Failed to retrieve market depth data"}
            
            data = json.loads(data_json)
            if not data or not data.get("data"):
                return {"error": "No market depth data available"}
            
            # Analyze market depth trends
            depth_data = data.get("data", [])
            
            # Group data by depth level
            depth_levels = {}
            for item in depth_data:
                level = float(item["depth_level"])
                if level not in depth_levels:
                    depth_levels[level] = []
                depth_levels[level].append(item)
            
            # Calculate average bid/ask ratio by depth level
            level_ratios = {}
            for level, items in depth_levels.items():
                avg_ratio = sum(float(item["bid_ask_ratio"]) for item in items) / len(items)
                level_ratios[level] = avg_ratio
            
            # Calculate total bid and ask depth
            total_bid = sum(float(item["bid_depth"]) for item in depth_data)
            total_ask = sum(float(item["ask_depth"]) for item in depth_data)
            overall_ratio = total_bid / total_ask if total_ask > 0 else 0
            
            # Generate analysis
            analysis = {
                "symbol": symbol,
                "exchange": exchange if exchange else "all",
                "interval": interval,
                "data_points": len(depth_data),
                "depth_levels": len(depth_levels),
                "total_bid_depth": total_bid,
                "total_ask_depth": total_ask,
                "overall_bid_ask_ratio": overall_ratio,
                "level_ratios": level_ratios,
                "interpretation": self._interpret_depth_ratio(overall_ratio)
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing market depth: {str(e)}")
            return {"error": f"Error analyzing market depth: {str(e)}"}
    
    def analyze_futures_basis(self, symbol: str, exchange: Optional[str] = None,
                           interval: str = "1h", limit: int = 24) -> Dict[str, Any]:
        """
        Analyze futures basis patterns.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name (or None for all exchanges)
            interval: Data interval
            limit: Number of data points to analyze
            
        Returns:
            Analysis results
        """
        try:
            # Get futures basis data
            data_json = get_futures_basis(symbol, exchange, None, interval, limit)
            if not data_json:
                return {"error": "Failed to retrieve futures basis data"}
            
            data = json.loads(data_json)
            if not data or not data.get("data"):
                return {"error": "No futures basis data available"}
            
            # Analyze futures basis trends
            basis_data = data.get("data", [])
            
            # Group data by contract type
            contract_types = {}
            for item in basis_data:
                contract_type = item["contract_type"]
                if contract_type not in contract_types:
                    contract_types[contract_type] = []
                contract_types[contract_type].append(item)
            
            # Calculate average basis by contract type
            type_basis = {}
            for contract_type, items in contract_types.items():
                avg_basis = sum(float(item["basis_points"]) for item in items) / len(items)
                type_basis[contract_type] = avg_basis
            
            # Calculate overall average basis
            average_basis = data.get("average_basis_points", 0)
            
            # Calculate basis trend
            basis_trend = data.get("basis_trend", "insufficient data")
            
            # Generate analysis
            analysis = {
                "symbol": symbol,
                "exchange": exchange if exchange else "all",
                "interval": interval,
                "data_points": len(basis_data),
                "contract_types": list(contract_types.keys()),
                "average_basis": average_basis,
                "average_annualized_basis": data.get("average_annualized_basis", 0),
                "type_basis": type_basis,
                "basis_trend": basis_trend,
                "interpretation": self._interpret_futures_basis(average_basis, basis_trend)
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing futures basis: {str(e)}")
            return {"error": f"Error analyzing futures basis: {str(e)}"}
    
    def analyze_volume_profile(self, symbol: str, exchange: Optional[str] = None,
                            time_period: str = "1d") -> Dict[str, Any]:
        """
        Analyze volume profile patterns.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name (or None for all exchanges)
            time_period: Time period for the volume profile
            
        Returns:
            Analysis results
        """
        try:
            # Get volume profile data
            data_json = get_volume_profile(symbol, exchange, time_period, "1h", 10)
            if not data_json:
                return {"error": "Failed to retrieve volume profile data"}
            
            data = json.loads(data_json)
            if not data or not data.get("price_levels"):
                return {"error": "No volume profile data available"}
            
            # Analyze volume profile
            price_levels = data.get("price_levels", [])
            
            # Get point of control
            poc = data.get("point_of_control", {})
            
            # Get volume distribution
            volume_dist = data.get("volume_distribution", {})
            
            # Generate analysis
            analysis = {
                "symbol": symbol,
                "exchange": exchange if exchange else "all",
                "time_period": time_period,
                "price_levels_analyzed": len(price_levels),
                "point_of_control": poc,
                "volume_distribution": volume_dist,
                "buy_sell_ratio": volume_dist.get("buy_percentage", 0) / volume_dist.get("sell_percentage", 1) if volume_dist.get("sell_percentage", 0) > 0 else 1,
                "interpretation": self._interpret_volume_profile(volume_dist)
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing volume profile: {str(e)}")
            return {"error": f"Error analyzing volume profile: {str(e)}"}
    
    def get_liquidity_analysis(self, symbol: str, exchange: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a comprehensive liquidity analysis for a symbol.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name (or None for all exchanges)
            
        Returns:
            Comprehensive liquidity analysis
        """
        try:
            # Get liquidity summary data
            data_json = get_liquidity_summary(symbol, exchange)
            if not data_json:
                return {"error": "Failed to retrieve liquidity summary data"}
            
            data = json.loads(data_json)
            if not data:
                return {"error": "No liquidity summary data available"}
            
            # Analyze liquidity metrics
            metrics = data.get("liquidity_metrics", {})
            
            # Generate analysis with detailed interpretations
            analysis = {
                "symbol": symbol,
                "exchange": exchange if exchange else "all",
                "timestamp": data.get("timestamp"),
                "overall_liquidity_sentiment": data.get("overall_liquidity_sentiment", "neutral"),
                "exchange_flow_analysis": self._analyze_exchange_flow_metric(metrics.get("exchange_flow", {})),
                "funding_rate_analysis": self._analyze_funding_rate_metric(metrics.get("funding_rate", {})),
                "market_depth_analysis": self._analyze_market_depth_metric(metrics.get("market_depth", {})),
                "futures_basis_analysis": self._analyze_futures_basis_metric(metrics.get("futures_basis", {})),
                "liquidity_signals": data.get("liquidity_signals", {})
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error generating liquidity analysis: {str(e)}")
            return {"error": f"Error generating liquidity analysis: {str(e)}"}
    
    def _interpret_funding_rate(self, rate: float, trend: str) -> Dict[str, Any]:
        """
        Interpret funding rate data.
        
        Args:
            rate: Average funding rate
            trend: Rate trend (increasing, decreasing, stable)
            
        Returns:
            Interpretation
        """
        if rate > 0.0005:  # >0.05% positive
            sentiment = "strongly bullish"
            explanation = "Traders paying a significant premium to hold long positions"
        elif rate > 0.0001:  # >0.01% positive
            sentiment = "moderately bullish"
            explanation = "Traders paying a modest premium to hold long positions"
        elif rate < -0.0005:  # >0.05% negative
            sentiment = "strongly bearish"
            explanation = "Traders paying a significant premium to hold short positions"
        elif rate < -0.0001:  # >0.01% negative
            sentiment = "moderately bearish"
            explanation = "Traders paying a modest premium to hold short positions"
        else:
            sentiment = "neutral"
            explanation = "Minimal funding rate premium in either direction"
        
        # Adjust based on trend
        if trend == "increasing" and rate < 0:
            sentiment = "bearish to neutral"
            explanation += ", but the negative funding rate is becoming less negative"
        elif trend == "increasing" and rate > 0:
            sentiment = "increasingly bullish"
            explanation += ", with growing premium for long positions"
        elif trend == "decreasing" and rate > 0:
            sentiment = "bullish to neutral"
            explanation += ", but the positive funding rate is becoming less positive"
        elif trend == "decreasing" and rate < 0:
            sentiment = "increasingly bearish"
            explanation += ", with growing premium for short positions"
        
        return {
            "sentiment": sentiment,
            "explanation": explanation
        }
    
    def _interpret_depth_ratio(self, ratio: float) -> Dict[str, Any]:
        """
        Interpret market depth bid/ask ratio.
        
        Args:
            ratio: Bid/ask ratio
            
        Returns:
            Interpretation
        """
        if ratio > 1.5:
            sentiment = "strongly bullish"
            explanation = "Significantly more buy orders than sell orders"
        elif ratio > 1.1:
            sentiment = "moderately bullish"
            explanation = "More buy orders than sell orders"
        elif ratio < 0.67:  # 1/1.5
            sentiment = "strongly bearish"
            explanation = "Significantly more sell orders than buy orders"
        elif ratio < 0.91:  # 1/1.1
            sentiment = "moderately bearish"
            explanation = "More sell orders than buy orders"
        else:
            sentiment = "neutral"
            explanation = "Roughly equal buy and sell orders"
        
        return {
            "sentiment": sentiment,
            "explanation": explanation
        }
    
    def _interpret_futures_basis(self, basis: float, trend: str) -> Dict[str, Any]:
        """
        Interpret futures basis data.
        
        Args:
            basis: Average basis in basis points
            trend: Basis trend (increasing, decreasing, stable)
            
        Returns:
            Interpretation
        """
        if basis > 50:  # >0.5%
            sentiment = "strongly bullish"
            explanation = "Large premium in futures markets suggests strong bullish sentiment"
        elif basis > 20:  # >0.2%
            sentiment = "moderately bullish"
            explanation = "Moderate premium in futures markets suggests bullish sentiment"
        elif basis < -20:  # <-0.2%
            sentiment = "strongly bearish"
            explanation = "Discount in futures markets suggests strong bearish sentiment"
        elif basis < -5:  # <-0.05%
            sentiment = "moderately bearish"
            explanation = "Modest discount in futures markets suggests bearish sentiment"
        else:
            sentiment = "neutral"
            explanation = "Minimal basis in futures markets suggests balanced sentiment"
        
        # Adjust based on trend
        if trend == "increasing":
            explanation += ", with basis increasing over the period analyzed"
        elif trend == "decreasing":
            explanation += ", with basis decreasing over the period analyzed"
        
        return {
            "sentiment": sentiment,
            "explanation": explanation
        }
    
    def _interpret_volume_profile(self, volume_dist: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret volume profile data.
        
        Args:
            volume_dist: Volume distribution data
            
        Returns:
            Interpretation
        """
        buy_pct = volume_dist.get("buy_percentage", 0)
        sell_pct = volume_dist.get("sell_percentage", 0)
        
        if buy_pct > 60:
            sentiment = "strongly bullish"
            explanation = f"Buying volume ({buy_pct:.1f}%) significantly exceeds selling volume ({sell_pct:.1f}%)"
        elif buy_pct > 55:
            sentiment = "moderately bullish"
            explanation = f"Buying volume ({buy_pct:.1f}%) exceeds selling volume ({sell_pct:.1f}%)"
        elif sell_pct > 60:
            sentiment = "strongly bearish"
            explanation = f"Selling volume ({sell_pct:.1f}%) significantly exceeds buying volume ({buy_pct:.1f}%)"
        elif sell_pct > 55:
            sentiment = "moderately bearish"
            explanation = f"Selling volume ({sell_pct:.1f}%) exceeds buying volume ({buy_pct:.1f}%)"
        else:
            sentiment = "neutral"
            explanation = f"Buying volume ({buy_pct:.1f}%) and selling volume ({sell_pct:.1f}%) are relatively balanced"
        
        return {
            "sentiment": sentiment,
            "explanation": explanation
        }
    
    def _analyze_exchange_flow_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze exchange flow metric from the liquidity summary.
        
        Args:
            metric: Exchange flow metric data
            
        Returns:
            Detailed analysis
        """
        if not metric:
            return {"sentiment": "unknown", "explanation": "No exchange flow data available"}
        
        flow_interpretation = metric.get("flow_interpretation", "")
        net_flow = float(metric.get("net_flow", 0))
        
        if flow_interpretation == "accumulation":
            sentiment = "bullish"
            explanation = f"Net outflow of {abs(net_flow):.2f} from exchanges suggests accumulation (withdrawal to cold storage)"
        elif flow_interpretation == "distribution":
            sentiment = "bearish"
            explanation = f"Net inflow of {net_flow:.2f} to exchanges suggests distribution (preparation for selling)"
        else:
            sentiment = "neutral"
            explanation = "Exchange flows are relatively balanced"
        
        return {
            "sentiment": sentiment,
            "explanation": explanation,
            "inflow": metric.get("inflow"),
            "outflow": metric.get("outflow"),
            "net_flow": metric.get("net_flow")
        }
    
    def _analyze_funding_rate_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze funding rate metric from the liquidity summary.
        
        Args:
            metric: Funding rate metric data
            
        Returns:
            Detailed analysis
        """
        if not metric:
            return {"sentiment": "unknown", "explanation": "No funding rate data available"}
        
        rate_interpretation = metric.get("rate_interpretation", "")
        latest_rate = float(metric.get("latest_rate", 0)) * 100  # Convert to percentage
        
        if rate_interpretation == "bullish":
            sentiment = "bullish"
            explanation = f"Positive funding rate of {latest_rate:.4f}% indicates traders are paying a premium to hold long positions"
        elif rate_interpretation == "bearish":
            sentiment = "bearish"
            explanation = f"Negative funding rate of {latest_rate:.4f}% indicates traders are paying a premium to hold short positions"
        else:
            sentiment = "neutral"
            explanation = f"Funding rate of {latest_rate:.4f}% is close to neutral"
        
        # Add annualized context
        annualized = float(metric.get("annualized_rate", 0)) * 100
        if abs(annualized) > 1:
            explanation += f", equivalent to {annualized:.2f}% annualized"
        
        return {
            "sentiment": sentiment,
            "explanation": explanation,
            "latest_rate": latest_rate,
            "average_rate": metric.get("average_rate"),
            "annualized_rate": annualized
        }
    
    def _analyze_market_depth_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market depth metric from the liquidity summary.
        
        Args:
            metric: Market depth metric data
            
        Returns:
            Detailed analysis
        """
        if not metric:
            return {"sentiment": "unknown", "explanation": "No market depth data available"}
        
        depth_interpretation = metric.get("depth_interpretation", "")
        ratio = float(metric.get("overall_bid_ask_ratio", 1))
        
        if depth_interpretation == "buy pressure":
            sentiment = "bullish"
            explanation = f"Bid/ask ratio of {ratio:.2f} indicates more buy orders than sell orders in the order book"
        elif depth_interpretation == "sell pressure":
            sentiment = "bearish"
            explanation = f"Bid/ask ratio of {ratio:.2f} indicates more sell orders than buy orders in the order book"
        else:
            sentiment = "neutral"
            explanation = f"Bid/ask ratio of {ratio:.2f} indicates relatively balanced order book"
        
        return {
            "sentiment": sentiment,
            "explanation": explanation,
            "bid_depth": metric.get("total_bid_depth"),
            "ask_depth": metric.get("total_ask_depth"),
            "ratio": ratio
        }
    
    def _analyze_futures_basis_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze futures basis metric from the liquidity summary.
        
        Args:
            metric: Futures basis metric data
            
        Returns:
            Detailed analysis
        """
        if not metric:
            return {"sentiment": "unknown", "explanation": "No futures basis data available"}
        
        basis_interpretation = metric.get("basis_interpretation", "")
        basis_points = float(metric.get("basis_points", 0))
        
        if basis_interpretation == "bullish":
            sentiment = "bullish"
            explanation = f"Futures basis of {basis_points} basis points indicates premium in futures prices"
        elif basis_interpretation == "bearish":
            sentiment = "bearish"
            explanation = f"Futures basis of {basis_points} basis points indicates discount in futures prices"
        else:
            sentiment = "neutral"
            explanation = f"Futures basis of {basis_points} basis points is relatively neutral"
        
        contract_type = metric.get("contract_type", "")
        if contract_type:
            explanation += f" for {contract_type} contracts"
        
        # Add annualized context
        annualized = float(metric.get("annualized_basis", 0)) * 100
        if abs(annualized) > 1:
            explanation += f", equivalent to {annualized:.2f}% annualized"
        
        return {
            "sentiment": sentiment,
            "explanation": explanation,
            "basis_points": basis_points,
            "contract_type": contract_type,
            "annualized_basis": annualized
        }

def get_liquidity_analyst() -> LiquidityAnalyst:
    """Factory function to create and return a LiquidityAnalyst instance"""
    return LiquidityAnalyst()

def get_analyst_functions() -> Dict[str, Callable]:
    """
    Get a dictionary of liquidity analyst functions for agent integration.
    
    Returns:
        Dictionary of function name to function mappings
    """
    analyst = get_liquidity_analyst()
    
    return {
        "analyze_exchange_flows": analyst.analyze_exchange_flows,
        "analyze_funding_rates": analyst.analyze_funding_rates,
        "analyze_market_depth": analyst.analyze_market_depth,
        "analyze_futures_basis": analyst.analyze_futures_basis,
        "analyze_volume_profile": analyst.analyze_volume_profile,
        "get_liquidity_analysis": analyst.get_liquidity_analysis
    }
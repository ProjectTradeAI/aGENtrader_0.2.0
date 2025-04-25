"""
Portfolio Management and Risk Analysis

This module implements portfolio management and risk analysis capabilities
for the trading system, including:

1. Risk analysis functions (VaR, maximum drawdown, etc.)
2. Position sizing strategies (fixed percentage, Kelly criterion, etc.)
3. Portfolio optimization techniques
4. Risk-adjusted position sizing

These components can be used by the trading agents to make more informed
decisions about position sizing and risk management.
"""

import math
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

# Import database utilities for volatility calculations
from agents.database_retrieval_tool import get_price_history, calculate_volatility

class RiskAnalyzer:
    """
    Risk analysis tools for portfolio management
    
    This class provides risk metrics calculation, position sizing recommendations,
    and portfolio optimization based on risk tolerance parameters.
    """
    
    def __init__(self, risk_tolerance: float = 0.02, confidence_level: float = 0.95):
        """
        Initialize the risk analyzer
        
        Args:
            risk_tolerance: Maximum percentage of portfolio to risk per trade (default: 2%)
            confidence_level: Confidence level for VaR calculations (default: 95%)
        """
        self.risk_tolerance = risk_tolerance
        self.confidence_level = confidence_level
    
    def calculate_value_at_risk(self, symbol: str, position_value: float, 
                               lookback_days: int = 30, interval: str = "1h") -> Dict[str, Any]:
        """
        Calculate Value at Risk (VaR) for a position
        
        Args:
            symbol: Trading symbol
            position_value: Current position value in quote currency
            lookback_days: Number of days to look back for historical data
            interval: Data interval for historical prices
            
        Returns:
            Dictionary with VaR metrics
        """
        # Get historical price data
        # The get_price_history function only takes symbol and days parameters
        price_history_json = get_price_history(
            symbol=symbol,
            days=lookback_days
        )
        
        if not price_history_json:
            return {
                "value_at_risk": position_value * 0.1,  # Conservative estimate if not enough data
                "confidence_level": self.confidence_level,
                "var_percentage": 0.1,
                "message": "Insufficient historical data for accurate VaR calculation",
                "status": "warning"
            }
        
        # Parse JSON string into dictionary
        price_data = json.loads(price_history_json)
        
        # Extract price history from the data dictionary
        price_history = price_data.get('data', [])
        
        if not price_history or len(price_history) < 10:
            return {
                "value_at_risk": position_value * 0.1,  # Conservative estimate if not enough data
                "confidence_level": self.confidence_level,
                "var_percentage": 0.1,
                "message": "Insufficient historical data for accurate VaR calculation",
                "status": "warning"
            }
        
        # Calculate daily returns
        prices = [float(p['close']) for p in price_history]
        returns = [prices[i]/prices[i-1] - 1 for i in range(1, len(prices))]
        
        # Calculate VaR
        returns = np.array(returns)
        var_percentage = np.percentile(returns, (1 - self.confidence_level) * 100)
        value_at_risk = abs(var_percentage) * position_value
        
        return {
            "value_at_risk": value_at_risk,
            "confidence_level": self.confidence_level,
            "var_percentage": abs(var_percentage),
            "message": f"VaR ({self.confidence_level*100:.0f}%): {value_at_risk:.2f} ({abs(var_percentage)*100:.2f}%)",
            "status": "success"
        }
    
    def calculate_max_position_size(self, symbol: str, entry_price: float, stop_loss: float, 
                                   portfolio_value: float) -> Dict[str, Any]:
        """
        Calculate maximum position size based on risk parameters
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price for the trade
            stop_loss: Stop loss price for the trade
            portfolio_value: Total portfolio value
            
        Returns:
            Dictionary with position sizing information
        """
        # Calculate risk per share/coin
        if entry_price <= 0 or stop_loss <= 0:
            return {
                "max_position_size": 0,
                "max_quantity": 0,
                "risk_amount": 0,
                "message": "Invalid price or stop loss values",
                "status": "error"
            }
        
        # For short positions, stop loss is above entry
        is_long = stop_loss < entry_price
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit == 0:
            return {
                "max_position_size": 0,
                "max_quantity": 0,
                "risk_amount": 0,
                "message": "Stop loss must be different from entry price",
                "status": "error"
            }
        
        # Calculate maximum risk amount
        max_risk_amount = portfolio_value * self.risk_tolerance
        
        # Calculate maximum position quantity
        max_quantity = max_risk_amount / risk_per_unit
        max_position_size = max_quantity * entry_price
        
        return {
            "max_position_size": max_position_size,
            "max_quantity": max_quantity,
            "risk_amount": max_risk_amount,
            "risk_per_unit": risk_per_unit,
            "is_long": is_long,
            "message": f"Max position: {max_position_size:.2f} ({max_quantity:.4f} units)",
            "status": "success"
        }
    
    def calculate_kelly_position_size(self, win_rate: float, risk_reward_ratio: float, 
                                     portfolio_value: float) -> Dict[str, Any]:
        """
        Calculate position size using the Kelly Criterion
        
        Args:
            win_rate: Probability of winning the trade (0.0 to 1.0)
            risk_reward_ratio: Ratio of potential profit to potential loss
            portfolio_value: Total portfolio value
            
        Returns:
            Dictionary with Kelly position sizing information
        """
        if win_rate <= 0 or win_rate >= 1:
            return {
                "kelly_percentage": 0,
                "position_size": 0,
                "message": "Win rate must be between 0 and 1",
                "status": "error"
            }
        
        if risk_reward_ratio <= 0:
            return {
                "kelly_percentage": 0,
                "position_size": 0,
                "message": "Risk-reward ratio must be positive",
                "status": "error"
            }
        
        # Calculate Kelly percentage
        # Kelly formula: f* = (p * b - q) / b
        # where p = probability of win, q = probability of loss (1-p), b = odds received on win (risk-reward ratio)
        kelly_percentage = (win_rate * risk_reward_ratio - (1 - win_rate)) / risk_reward_ratio
        
        # Cap the Kelly percentage to avoid over-concentration
        # Using half-Kelly is often recommended to reduce volatility
        capped_kelly = min(kelly_percentage, 0.5) / 2  # Using quarter Kelly for more conservative sizing
        
        if kelly_percentage <= 0:
            return {
                "kelly_percentage": kelly_percentage,
                "capped_kelly": 0,
                "position_size": 0,
                "message": "Negative Kelly value, trade should be avoided",
                "status": "warning"
            }
        
        position_size = capped_kelly * portfolio_value
        
        return {
            "kelly_percentage": kelly_percentage,
            "capped_kelly": capped_kelly,
            "position_size": position_size,
            "message": f"Kelly: {kelly_percentage:.2%}, Adjusted Kelly: {capped_kelly:.2%}, Size: {position_size:.2f}",
            "status": "success"
        }
    
    def calculate_volatility_adjusted_size(self, symbol: str, portfolio_value: float, 
                                          lookback_days: int = 30, 
                                          target_volatility: float = 0.01) -> Dict[str, Any]:
        """
        Calculate volatility-adjusted position size
        
        Args:
            symbol: Trading symbol
            portfolio_value: Total portfolio value
            lookback_days: Number of days to look back for volatility calculation
            target_volatility: Target daily volatility as a decimal (default: 1%)
            
        Returns:
            Dictionary with volatility-adjusted sizing information
        """
        # Get historical volatility
        volatility_json = calculate_volatility(
            symbol=symbol,
            days=lookback_days
        )
        
        if not volatility_json:
            return {
                "position_size": portfolio_value * 0.1,  # Conservative default
                "message": "Error calculating volatility: Could not retrieve data",
                "status": "warning"
            }
        
        # Parse volatility result
        volatility_result = json.loads(volatility_json)
        daily_volatility = volatility_result.get("daily_volatility", 0.01)
        
        if daily_volatility == 0:
            return {
                "position_size": 0,
                "message": "Cannot calculate position size with zero volatility",
                "status": "error"
            }
        
        # Calculate volatility-adjusted position size
        # Size = (Target Volatility / Asset Volatility) * Portfolio Value
        volatility_ratio = target_volatility / daily_volatility
        position_size = volatility_ratio * portfolio_value
        
        # Cap position size at 30% of portfolio to prevent over-concentration
        max_size = portfolio_value * 0.3
        if position_size > max_size:
            position_size = max_size
            message = f"Position size capped at 30% of portfolio: {position_size:.2f}"
            status = "warning"
        else:
            message = f"Volatility-adjusted position size: {position_size:.2f}"
            status = "success"
        
        return {
            "position_size": position_size,
            "volatility_ratio": volatility_ratio,
            "daily_volatility": daily_volatility,
            "target_volatility": target_volatility,
            "message": message,
            "status": status
        }
    
    def analyze_portfolio_risk(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze overall portfolio risk metrics
        
        Args:
            portfolio: Portfolio dictionary with positions and cash balance
            
        Returns:
            Dictionary with portfolio risk metrics
        """
        positions = portfolio.get("positions", [])
        total_equity = portfolio.get("total_equity", 0)
        cash_balance = portfolio.get("cash_balance", 0)
        
        if total_equity == 0:
            return {
                "cash_ratio": 1.0,
                "largest_position_ratio": 0,
                "risk_concentration": 0,
                "diversification_score": 0,
                "message": "Portfolio is empty",
                "status": "warning"
            }
        
        # Calculate cash ratio
        cash_ratio = cash_balance / total_equity
        
        # Calculate position concentration metrics
        if not positions:
            return {
                "cash_ratio": cash_ratio,
                "largest_position_ratio": 0,
                "risk_concentration": 0,
                "diversification_score": 0,
                "message": "No positions in portfolio",
                "status": "warning"
            }
        
        position_values = [p.get("value", 0) for p in positions]
        largest_position = max(position_values) if position_values else 0
        largest_position_ratio = largest_position / total_equity
        
        # Calculate Herfindahl-Hirschman Index (HHI) for concentration
        # HHI = sum of squared percentage weights
        position_weights = [pv / total_equity for pv in position_values]
        hhi = sum([w**2 for w in position_weights])
        
        # Normalize HHI to 0-1 range
        normalized_hhi = (hhi - (1/len(positions))) / (1 - (1/len(positions))) if len(positions) > 1 else 1
        
        # Calculate diversification score (inverse of HHI)
        diversification_score = 1 - normalized_hhi
        
        return {
            "cash_ratio": cash_ratio,
            "largest_position_ratio": largest_position_ratio,
            "position_count": len(positions),
            "risk_concentration": normalized_hhi,
            "diversification_score": diversification_score,
            "message": f"Portfolio has {len(positions)} positions, {cash_ratio:.1%} cash, largest position {largest_position_ratio:.1%}",
            "status": "success"
        }

class PortfolioManager:
    """
    Portfolio manager for optimizing position sizing and risk management
    
    This class manages the portfolio optimization process, combining multiple
    position sizing techniques and risk analyses to provide comprehensive
    portfolio management.
    """
    
    def __init__(self, risk_analyzer: Optional[RiskAnalyzer] = None, 
                risk_tolerance: float = 0.02):
        """
        Initialize the portfolio manager
        
        Args:
            risk_analyzer: Risk analyzer instance (creates new one if None)
            risk_tolerance: Maximum percentage of portfolio to risk per trade
        """
        self.risk_analyzer = risk_analyzer or RiskAnalyzer(risk_tolerance=risk_tolerance)
        self.risk_tolerance = risk_tolerance
    
    def get_optimal_position_size(self, symbol: str, entry_price: float, stop_loss: float,
                                 portfolio: Dict[str, Any], win_probability: float = 0.5, 
                                 risk_reward_ratio: float = 1.5) -> Dict[str, Any]:
        """
        Calculate optimal position size using multiple techniques
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price for the trade
            stop_loss: Stop loss price for the trade
            portfolio: Portfolio dictionary with positions and cash balance
            win_probability: Estimated probability of winning the trade
            risk_reward_ratio: Ratio of potential profit to potential loss
            
        Returns:
            Dictionary with optimal position sizing information
        """
        portfolio_value = portfolio.get("total_equity", 0)
        cash_balance = portfolio.get("cash_balance", 0)
        
        if portfolio_value == 0:
            return {
                "position_size": 0,
                "quantity": 0,
                "message": "Portfolio has zero value",
                "status": "error"
            }
        
        if cash_balance <= 0:
            return {
                "position_size": 0,
                "quantity": 0,
                "message": "Insufficient cash balance for new position",
                "status": "error"
            }
        
        # Get position size based on fixed percentage risk
        risk_based_size = self.risk_analyzer.calculate_max_position_size(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            portfolio_value=portfolio_value
        )
        
        # Get position size based on Kelly criterion
        kelly_size = self.risk_analyzer.calculate_kelly_position_size(
            win_rate=win_probability,
            risk_reward_ratio=risk_reward_ratio,
            portfolio_value=portfolio_value
        )
        
        # Get position size based on volatility adjustment
        volatility_size = self.risk_analyzer.calculate_volatility_adjusted_size(
            symbol=symbol,
            portfolio_value=portfolio_value
        )
        
        # Analyze current portfolio risk
        portfolio_risk = self.risk_analyzer.analyze_portfolio_risk(portfolio)
        
        # Calculate weighted average of different sizing methods
        # Weight more conservative approaches higher if portfolio is concentrated
        risk_concentration = portfolio_risk.get("risk_concentration", 0)
        
        if risk_concentration > 0.5:  # High concentration, be more conservative
            weights = {
                "risk_based": 0.5,
                "kelly": 0.2,
                "volatility": 0.3
            }
        else:  # More diversified, can be slightly more aggressive
            weights = {
                "risk_based": 0.4,
                "kelly": 0.3,
                "volatility": 0.3
            }
        
        # Get position sizes from each method
        sizes = {
            "risk_based": risk_based_size.get("max_position_size", 0),
            "kelly": kelly_size.get("position_size", 0),
            "volatility": volatility_size.get("position_size", 0)
        }
        
        # Calculate weighted average, excluding any negative or zero values
        valid_weights = {}
        total_weight = 0
        
        for method, size in sizes.items():
            if size > 0:
                valid_weights[method] = weights[method]
                total_weight += weights[method]
        
        if total_weight == 0:
            weighted_size = 0
        else:
            # Normalize weights to sum to 1
            normalized_weights = {m: w/total_weight for m, w in valid_weights.items()}
            weighted_size = sum(sizes[m] * normalized_weights[m] for m in normalized_weights)
        
        # Cap position size by available cash and maximum concentration
        max_concentration = 0.3  # Maximum 30% of portfolio in a single position
        max_size_by_concentration = portfolio_value * max_concentration
        max_position_size = min(weighted_size, cash_balance, max_size_by_concentration)
        
        # Calculate quantity
        quantity = max_position_size / entry_price if entry_price > 0 else 0
        
        # Detailed position sizing information
        details = {
            "risk_based_size": risk_based_size.get("max_position_size", 0),
            "kelly_size": kelly_size.get("position_size", 0),
            "volatility_size": volatility_size.get("position_size", 0),
            "weighted_size": weighted_size,
            "max_size_by_cash": cash_balance,
            "max_size_by_concentration": max_size_by_concentration,
            "portfolio_value": portfolio_value,
            "cash_balance": cash_balance,
            "risk_concentration": risk_concentration
        }
        
        return {
            "position_size": max_position_size,
            "quantity": quantity,
            "position_value_percentage": (max_position_size / portfolio_value) if portfolio_value > 0 else 0,
            "sizing_details": details,
            "message": f"Optimal position size: {max_position_size:.2f} ({quantity:.6f} units)",
            "status": "success"
        }
    
    def get_position_adjustment(self, symbol: str, current_price: float, current_position: Dict[str, Any], 
                               portfolio: Dict[str, Any], target_allocation: float = None) -> Dict[str, Any]:
        """
        Calculate position size adjustment based on current position and target allocation
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            current_position: Current position details
            portfolio: Portfolio dictionary with positions and cash balance
            target_allocation: Target allocation as percentage of portfolio (0.0 to 1.0)
            
        Returns:
            Dictionary with position adjustment information
        """
        portfolio_value = portfolio.get("total_equity", 0)
        cash_balance = portfolio.get("cash_balance", 0)
        
        if portfolio_value == 0:
            return {
                "adjustment": 0,
                "quantity_change": 0,
                "action": "none",
                "message": "Portfolio has zero value",
                "status": "error"
            }
        
        # Get current position details
        current_quantity = current_position.get("quantity", 0)
        current_value = current_position.get("value", 0)
        
        # If no target allocation provided, calculate optimal allocation
        if target_allocation is None:
            volatility_result = self.risk_analyzer.calculate_volatility_adjusted_size(
                symbol=symbol,
                portfolio_value=portfolio_value
            )
            target_position_size = volatility_result.get("position_size", 0)
            target_allocation = target_position_size / portfolio_value if portfolio_value > 0 else 0
        
        # Calculate target position value and quantity
        target_value = portfolio_value * target_allocation
        target_quantity = target_value / current_price if current_price > 0 else 0
        
        # Calculate adjustment needed
        value_adjustment = target_value - current_value
        quantity_adjustment = target_quantity - current_quantity
        
        # Determine action
        if abs(quantity_adjustment) < 0.001:
            action = "none"
            message = "No adjustment needed"
        elif quantity_adjustment > 0:
            # Check if we have enough cash
            if value_adjustment > cash_balance:
                value_adjustment = cash_balance
                quantity_adjustment = cash_balance / current_price if current_price > 0 else 0
                message = f"Buy adjustment limited by cash: {quantity_adjustment:.6f} units (${value_adjustment:.2f})"
            else:
                message = f"Buy {quantity_adjustment:.6f} units (${value_adjustment:.2f})"
            action = "buy"
        else:
            message = f"Sell {abs(quantity_adjustment):.6f} units (${abs(value_adjustment):.2f})"
            action = "sell"
        
        return {
            "adjustment": value_adjustment,
            "quantity_change": quantity_adjustment,
            "target_allocation": target_allocation,
            "target_value": target_value,
            "target_quantity": target_quantity,
            "current_allocation": current_value / portfolio_value if portfolio_value > 0 else 0,
            "action": action,
            "message": message,
            "status": "success" if action != "none" else "info"
        }
    
    def optimize_portfolio(self, portfolio: Dict[str, Any], risk_profile: str = "moderate") -> Dict[str, Any]:
        """
        Optimize portfolio allocations based on risk profile
        
        Args:
            portfolio: Portfolio dictionary with positions and cash balance
            risk_profile: Risk profile (conservative, moderate, aggressive)
            
        Returns:
            Dictionary with portfolio optimization recommendations
        """
        # Analyze current portfolio risk
        portfolio_risk = self.risk_analyzer.analyze_portfolio_risk(portfolio)
        positions = portfolio.get("positions", [])
        total_equity = portfolio.get("total_equity", 0)
        
        if not positions:
            return {
                "recommendations": [],
                "message": "No positions to optimize",
                "status": "warning"
            }
        
        # Set target cash ratio based on risk profile
        target_cash_ratios = {
            "conservative": 0.4,  # 40% cash
            "moderate": 0.25,     # 25% cash
            "aggressive": 0.1     # 10% cash
        }
        
        target_cash = target_cash_ratios.get(risk_profile, 0.25)
        current_cash = portfolio.get("cash_balance", 0) / total_equity if total_equity > 0 else 0
        
        # Calculate volatility for each position
        volatility_data = {}
        
        for position in positions:
            symbol = position.get("symbol", "")
            volatility_result = self.risk_analyzer.calculate_volatility_adjusted_size(
                symbol=symbol,
                portfolio_value=total_equity
            )
            volatility_data[symbol] = {
                "daily_volatility": volatility_result.get("daily_volatility", 0.01),
                "position_size": volatility_result.get("position_size", 0),
                "current_value": position.get("value", 0),
                "current_allocation": position.get("value", 0) / total_equity if total_equity > 0 else 0
            }
        
        # Calculate target allocations based on inverse volatility weighting
        # Higher volatility assets get lower allocation
        if not volatility_data:
            return {
                "recommendations": [],
                "message": "Could not calculate volatility for any positions",
                "status": "error"
            }
        
        inverse_volatilities = {s: 1/max(v["daily_volatility"], 0.001) for s, v in volatility_data.items()}
        total_inverse_vol = sum(inverse_volatilities.values())
        
        # Allocate the non-cash portion of the portfolio inversely proportional to volatility
        equity_to_allocate = 1 - target_cash
        
        if total_inverse_vol == 0:
            # Equal allocation if we can't use volatility
            target_allocations = {s: equity_to_allocate / len(volatility_data) for s in volatility_data}
        else:
            target_allocations = {s: (v/total_inverse_vol) * equity_to_allocate 
                                for s, v in inverse_volatilities.items()}
        
        # Generate recommendations
        recommendations = []
        
        for position in positions:
            symbol = position.get("symbol", "")
            current_value = position.get("value", 0)
            current_allocation = current_value / total_equity if total_equity > 0 else 0
            target_allocation = target_allocations.get(symbol, 0)
            
            adjustment_value = (target_allocation - current_allocation) * total_equity
            
            # Only recommend significant changes (>1% of portfolio)
            if abs(adjustment_value) > (total_equity * 0.01):
                action = "buy" if adjustment_value > 0 else "sell"
                recommendations.append({
                    "symbol": symbol,
                    "current_allocation": current_allocation,
                    "target_allocation": target_allocation,
                    "adjustment_value": adjustment_value,
                    "action": action,
                    "message": f"{action.capitalize()} {symbol}: {abs(adjustment_value):.2f} to reach {target_allocation:.1%} allocation"
                })
        
        # Consider cash adjustment if needed
        cash_adjustment = (target_cash - current_cash) * total_equity
        
        if abs(cash_adjustment) > (total_equity * 0.05):  # Only if >5% adjustment needed
            action = "increase" if cash_adjustment > 0 else "decrease"
            recommendations.append({
                "symbol": "CASH",
                "current_allocation": current_cash,
                "target_allocation": target_cash,
                "adjustment_value": cash_adjustment,
                "action": action,
                "message": f"{action.capitalize()} cash by {abs(cash_adjustment):.2f} to reach {target_cash:.1%} allocation"
            })
        
        return {
            "risk_profile": risk_profile,
            "current_cash_ratio": current_cash,
            "target_cash_ratio": target_cash,
            "recommendations": recommendations,
            "message": f"Generated {len(recommendations)} portfolio optimization recommendations",
            "status": "success" if recommendations else "info"
        }


# Risk analysis agent definition for AutoGen integration
def risk_analysis_agent_definition() -> Dict[str, Any]:
    """
    Get the AutoGen definition for the risk analysis agent
    
    Returns:
        Dictionary with AutoGen agent configuration
    """
    return {
        "name": "RiskAnalysisAgent",
        "description": "Specialized agent for portfolio risk analysis and position sizing",
        "system_message": """You are a Risk Analysis Agent specializing in portfolio management and 
position sizing. Your role is to analyze market conditions, asset volatility, and portfolio 
structures to recommend risk-appropriate position sizes and portfolio allocations.
        
Your expertise includes:
- Value at Risk (VaR) calculation
- Volatility-based position sizing
- Kelly Criterion for optimal position sizing
- Portfolio diversification analysis
- Risk concentration measurement
- Drawdown analysis and risk management

You should always consider:
1. Current market volatility and conditions
2. Correlation between assets in the portfolio
3. Proper risk management (typically 1-2% of capital per trade)
4. Portfolio concentration and diversification
5. Maximum drawdown scenarios

You can use quantitative analysis to calculate optimal position sizes and provide 
specific recommendations on portfolio allocation based on risk tolerance profiles.""",
        "functions": [
            {
                "name": "calculate_value_at_risk",
                "description": "Calculate Value at Risk (VaR) for a position",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol"
                        },
                        "position_value": {
                            "type": "number",
                            "description": "Current position value in quote currency"
                        },
                        "lookback_days": {
                            "type": "integer",
                            "description": "Number of days to look back for historical data",
                            "default": 30
                        },
                        "interval": {
                            "type": "string",
                            "description": "Data interval for historical prices",
                            "default": "1h"
                        }
                    },
                    "required": ["symbol", "position_value"]
                }
            },
            {
                "name": "calculate_max_position_size",
                "description": "Calculate maximum position size based on risk parameters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol"
                        },
                        "entry_price": {
                            "type": "number",
                            "description": "Entry price for the trade"
                        },
                        "stop_loss": {
                            "type": "number",
                            "description": "Stop loss price for the trade"
                        },
                        "portfolio_value": {
                            "type": "number",
                            "description": "Total portfolio value"
                        }
                    },
                    "required": ["symbol", "entry_price", "stop_loss", "portfolio_value"]
                }
            },
            {
                "name": "calculate_kelly_position_size",
                "description": "Calculate position size using the Kelly Criterion",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "win_rate": {
                            "type": "number",
                            "description": "Probability of winning the trade (0.0 to 1.0)"
                        },
                        "risk_reward_ratio": {
                            "type": "number",
                            "description": "Ratio of potential profit to potential loss"
                        },
                        "portfolio_value": {
                            "type": "number",
                            "description": "Total portfolio value"
                        }
                    },
                    "required": ["win_rate", "risk_reward_ratio", "portfolio_value"]
                }
            },
            {
                "name": "calculate_volatility_adjusted_size",
                "description": "Calculate volatility-adjusted position size",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol"
                        },
                        "portfolio_value": {
                            "type": "number",
                            "description": "Total portfolio value"
                        },
                        "lookback_days": {
                            "type": "integer",
                            "description": "Number of days to look back for volatility calculation",
                            "default": 30
                        },
                        "target_volatility": {
                            "type": "number",
                            "description": "Target daily volatility as a decimal (default: 1%)",
                            "default": 0.01
                        }
                    },
                    "required": ["symbol", "portfolio_value"]
                }
            },
            {
                "name": "analyze_portfolio_risk",
                "description": "Analyze overall portfolio risk metrics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "portfolio": {
                            "type": "object",
                            "description": "Portfolio dictionary with positions and cash balance"
                        }
                    },
                    "required": ["portfolio"]
                }
            },
            {
                "name": "get_optimal_position_size",
                "description": "Calculate optimal position size using multiple techniques",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol"
                        },
                        "entry_price": {
                            "type": "number",
                            "description": "Entry price for the trade"
                        },
                        "stop_loss": {
                            "type": "number",
                            "description": "Stop loss price for the trade"
                        },
                        "portfolio": {
                            "type": "object",
                            "description": "Portfolio dictionary with positions and cash balance"
                        },
                        "win_probability": {
                            "type": "number",
                            "description": "Estimated probability of winning the trade",
                            "default": 0.5
                        },
                        "risk_reward_ratio": {
                            "type": "number",
                            "description": "Ratio of potential profit to potential loss",
                            "default": 1.5
                        }
                    },
                    "required": ["symbol", "entry_price", "stop_loss", "portfolio"]
                }
            },
            {
                "name": "optimize_portfolio",
                "description": "Optimize portfolio allocations based on risk profile",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "portfolio": {
                            "type": "object",
                            "description": "Portfolio dictionary with positions and cash balance"
                        },
                        "risk_profile": {
                            "type": "string",
                            "description": "Risk profile (conservative, moderate, aggressive)",
                            "enum": ["conservative", "moderate", "aggressive"],
                            "default": "moderate"
                        }
                    },
                    "required": ["portfolio"]
                }
            }
        ]
    }


# Portfolio manager agent definition for AutoGen integration  
def portfolio_manager_agent_definition() -> Dict[str, Any]:
    """
    Get the AutoGen definition for the portfolio manager agent
    
    Returns:
        Dictionary with AutoGen agent configuration
    """
    return {
        "name": "PortfolioManagerAgent",
        "description": "Specialized agent for portfolio management and allocation optimization",
        "system_message": """You are a Portfolio Manager Agent specializing in portfolio allocation, 
position sizing, and risk management. Your role is to analyze and optimize portfolio structure 
to balance risk and potential returns based on market conditions and risk tolerance.
        
Your expertise includes:
- Optimal asset allocation based on risk profiles
- Position sizing and adjustment strategies
- Portfolio rebalancing recommendations
- Risk-adjusted performance analysis
- Diversification optimization
- Drawdown minimization strategies

You should always consider:
1. The trader's risk profile and investment goals
2. Current market regime and volatility environment
3. Correlation between assets to optimize diversification
4. Liquidity needs and transaction costs
5. Historical performance and forward projections

Your recommendations should be specific, providing clear allocation percentages,
position size adjustments, and rebalancing strategies based on quantitative analysis
of risk, return, and correlation metrics.""",
        "functions": [
            {
                "name": "analyze_portfolio_risk",
                "description": "Analyze overall portfolio risk metrics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "portfolio": {
                            "type": "object",
                            "description": "Portfolio dictionary with positions and cash balance"
                        }
                    },
                    "required": ["portfolio"]
                }
            },
            {
                "name": "get_optimal_position_size",
                "description": "Calculate optimal position size using multiple techniques",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol"
                        },
                        "entry_price": {
                            "type": "number",
                            "description": "Entry price for the trade"
                        },
                        "stop_loss": {
                            "type": "number",
                            "description": "Stop loss price for the trade"
                        },
                        "portfolio": {
                            "type": "object",
                            "description": "Portfolio dictionary with positions and cash balance"
                        },
                        "win_probability": {
                            "type": "number",
                            "description": "Estimated probability of winning the trade",
                            "default": 0.5
                        },
                        "risk_reward_ratio": {
                            "type": "number",
                            "description": "Ratio of potential profit to potential loss",
                            "default": 1.5
                        }
                    },
                    "required": ["symbol", "entry_price", "stop_loss", "portfolio"]
                }
            },
            {
                "name": "get_position_adjustment",
                "description": "Calculate position size adjustment based on current position and target allocation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol"
                        },
                        "current_price": {
                            "type": "number",
                            "description": "Current market price"
                        },
                        "current_position": {
                            "type": "object",
                            "description": "Current position details"
                        },
                        "portfolio": {
                            "type": "object",
                            "description": "Portfolio dictionary with positions and cash balance"
                        },
                        "target_allocation": {
                            "type": "number",
                            "description": "Target allocation as percentage of portfolio (0.0 to 1.0)",
                            "default": None
                        }
                    },
                    "required": ["symbol", "current_price", "current_position", "portfolio"]
                }
            },
            {
                "name": "optimize_portfolio",
                "description": "Optimize portfolio allocations based on risk profile",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "portfolio": {
                            "type": "object",
                            "description": "Portfolio dictionary with positions and cash balance"
                        },
                        "risk_profile": {
                            "type": "string",
                            "description": "Risk profile (conservative, moderate, aggressive)",
                            "enum": ["conservative", "moderate", "aggressive"],
                            "default": "moderate"
                        }
                    },
                    "required": ["portfolio"]
                }
            },
            {
                "name": "calculate_value_at_risk",
                "description": "Calculate Value at Risk (VaR) for a position",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol"
                        },
                        "position_value": {
                            "type": "number",
                            "description": "Current position value in quote currency"
                        },
                        "lookback_days": {
                            "type": "integer",
                            "description": "Number of days to look back for historical data",
                            "default": 30
                        },
                        "interval": {
                            "type": "string",
                            "description": "Data interval for historical prices",
                            "default": "1h"
                        }
                    },
                    "required": ["symbol", "position_value"]
                }
            }
        ]
    }
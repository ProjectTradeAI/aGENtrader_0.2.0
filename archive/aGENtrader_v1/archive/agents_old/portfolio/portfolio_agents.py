"""
Portfolio Management Agent Module

This module defines agents for portfolio management and risk assessment,
providing recommendations for position sizing and risk management.
"""
import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    import pandas as pd
    import numpy as np
except ImportError:
    logger.warning("Required libraries not installed. Install with: pip install pandas numpy")

class PortfolioManagementAgent:
    """
    Agent that provides portfolio management and risk assessment recommendations.
    Analyzes position sizing, risk allocation, and portfolio balance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the portfolio management agent.
        
        Args:
            config: Optional configuration for the agent
        """
        self.config = config or {}
        
        # Default configuration
        self.default_config = {
            "max_position_size_pct": 0.05,  # Maximum 5% of portfolio per position
            "max_single_loss_pct": 0.02,    # Maximum 2% loss per trade
            "portfolio_volatility_target": 0.15,  # Target annual volatility
            "position_correlation_weight": 0.2,  # Weight for correlation analysis
            "max_sector_allocation": 0.25,  # Maximum 25% in a single sector
            "drawdown_tolerance": 0.1,      # 10% max drawdown tolerance
            "risk_free_rate": 0.03,         # 3% risk-free rate
            "rebalance_threshold": 0.1      # Rebalance when allocations drift 10%
        }
        
        # Merge with provided config
        for key, value in self.default_config.items():
            if key not in self.config:
                self.config[key] = value
    
    def analyze(self, symbol: str, market_data: pd.DataFrame,
               portfolio_data: Dict[str, Any], agent_decisions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze portfolio risk and provide position management recommendations.
        
        Args:
            symbol: Trading symbol
            market_data: Market data DataFrame
            portfolio_data: Current portfolio information
            agent_decisions: Decisions from other agents
            
        Returns:
            Portfolio analysis and recommendations
        """
        try:
            # Extract relevant data
            portfolio_balance = portfolio_data.get("balance", 10000.0)
            positions = portfolio_data.get("positions", [])
            risk_level = portfolio_data.get("risk_level", "moderate")
            
            # Get other agent decisions
            technical_direction = agent_decisions.get("technical", {}).get("direction")
            fundamental_direction = agent_decisions.get("fundamental", {}).get("direction")
            
            # Calculate volatility
            volatility = self._calculate_volatility(market_data)
            
            # Calculate position sizing
            position_size = self._calculate_position_size(
                symbol, market_data, portfolio_balance, volatility, risk_level
            )
            
            # Calculate stop loss and take profit
            risk_params = self._calculate_risk_parameters(
                symbol, market_data, volatility, risk_level
            )
            
            # Determine if position should be taken
            execute_trade = self._should_execute_trade(
                technical_direction, fundamental_direction,
                position_size, portfolio_balance, positions
            )
            
            # Generate portfolio recommendation
            recommendation = self._generate_recommendation(
                execute_trade, position_size, portfolio_balance,
                risk_params, positions
            )
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                symbol, recommendation, technical_direction, 
                fundamental_direction, position_size, volatility,
                portfolio_balance, positions, risk_level
            )
            
            # Compile result
            result = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "recommendation": recommendation,
                "reasoning": reasoning,
                "position_sizing": {
                    "recommended_size": position_size,
                    "percent_of_portfolio": position_size / portfolio_balance if portfolio_balance > 0 else 0,
                    "volatility_adjusted": True
                },
                "risk_parameters": risk_params,
                "portfolio_metrics": {
                    "current_balance": portfolio_balance,
                    "num_positions": len(positions),
                    "volatility": volatility,
                    "risk_level": risk_level
                }
            }
            
            logger.info(f"Portfolio analysis for {symbol}: recommendation={recommendation}")
            return result
            
        except Exception as e:
            logger.error(f"Error in portfolio analysis: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "recommendation": "hold",
                "reasoning": f"Error in portfolio analysis: {str(e)}",
                "position_sizing": {"recommended_size": 0},
                "risk_parameters": {},
                "portfolio_metrics": {}
            }
    
    def _calculate_volatility(self, market_data: pd.DataFrame) -> float:
        """
        Calculate asset volatility from market data.
        
        Args:
            market_data: Market data DataFrame
            
        Returns:
            Annualized volatility
        """
        try:
            if market_data.empty or 'close' not in market_data.columns:
                return 0.3  # Default volatility if no data
                
            # Calculate daily returns
            daily_returns = market_data['close'].pct_change().dropna()
            
            # Calculate annualized volatility (252 trading days)
            volatility = daily_returns.std() * (252 ** 0.5)
            
            return volatility
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return 0.3  # Default volatility on error
    
    def _calculate_position_size(self, symbol: str, market_data: pd.DataFrame,
                               portfolio_balance: float, volatility: float,
                               risk_level: str) -> float:
        """
        Calculate position size based on portfolio size, volatility, and risk.
        
        Args:
            symbol: Trading symbol
            market_data: Market data DataFrame
            portfolio_balance: Current portfolio balance
            volatility: Asset volatility
            risk_level: Risk level (conservative, moderate, aggressive)
            
        Returns:
            Recommended position size in base currency
        """
        try:
            # Risk factor based on profile
            risk_factors = {
                "conservative": 0.5,
                "moderate": 1.0,
                "aggressive": 1.5
            }
            risk_factor = risk_factors.get(risk_level, 1.0)
            
            # Position size based on risk
            max_position_size = portfolio_balance * self.config["max_position_size_pct"] * risk_factor
            
            # Adjust for volatility
            volatility_adjustment = 0.2 / volatility if volatility > 0 else 1.0
            volatility_adjustment = min(max(volatility_adjustment, 0.5), 2.0)  # Bound adjustment
            
            # Calculate adjusted position size
            adjusted_position_size = max_position_size * volatility_adjustment
            
            # Ensure position size is reasonable
            position_size = min(adjusted_position_size, portfolio_balance * self.config["max_position_size_pct"] * 2)
            
            return position_size
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return portfolio_balance * 0.02  # Default to 2% of portfolio on error
    
    def _calculate_risk_parameters(self, symbol: str, market_data: pd.DataFrame,
                                volatility: float, risk_level: str) -> Dict[str, Any]:
        """
        Calculate risk parameters such as stop loss and take profit levels.
        
        Args:
            symbol: Trading symbol
            market_data: Market data DataFrame
            volatility: Asset volatility
            risk_level: Risk level
            
        Returns:
            Dictionary with risk parameters
        """
        try:
            # Current price
            current_price = market_data['close'].iloc[-1] if not market_data.empty and 'close' in market_data.columns else 100.0
            
            # Risk factor based on profile
            risk_factors = {
                "conservative": {"sl": 0.03, "tp": 0.06},  # 3% SL, 6% TP, 1:2 ratio
                "moderate": {"sl": 0.05, "tp": 0.15},      # 5% SL, 15% TP, 1:3 ratio
                "aggressive": {"sl": 0.08, "tp": 0.24}     # 8% SL, 24% TP, 1:3 ratio
            }
            risk_params = risk_factors.get(risk_level, {"sl": 0.05, "tp": 0.15})
            
            # Adjust based on volatility (more volatile = wider stops)
            volatility_adjustment = volatility / 0.2 if volatility > 0 else 1.0
            volatility_adjustment = min(max(volatility_adjustment, 0.8), 1.5)  # Bound adjustment
            
            # Calculate stop loss and take profit percentages
            stop_loss_pct = risk_params["sl"] * volatility_adjustment
            take_profit_pct = risk_params["tp"] * volatility_adjustment
            
            # Calculate actual levels
            stop_loss = current_price * (1 - stop_loss_pct)
            take_profit = current_price * (1 + take_profit_pct)
            
            return {
                "stop_loss_pct": stop_loss_pct,
                "take_profit_pct": take_profit_pct,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_reward_ratio": take_profit_pct / stop_loss_pct,
                "risk_level": risk_level,
                "volatility_adjustment": volatility_adjustment
            }
        except Exception as e:
            logger.error(f"Error calculating risk parameters: {str(e)}")
            return {
                "stop_loss_pct": 0.05,
                "take_profit_pct": 0.15,
                "stop_loss": current_price * 0.95 if 'current_price' in locals() else 95.0,
                "take_profit": current_price * 1.15 if 'current_price' in locals() else 115.0,
                "risk_reward_ratio": 3.0,
                "risk_level": risk_level,
                "volatility_adjustment": 1.0
            }
    
    def _should_execute_trade(self, technical_direction: Optional[str],
                            fundamental_direction: Optional[str],
                            position_size: float, portfolio_balance: float,
                            positions: List[Dict[str, Any]]) -> bool:
        """
        Determine if a trade should be executed based on agent decisions and portfolio state.
        
        Args:
            technical_direction: Technical analysis direction
            fundamental_direction: Fundamental analysis direction
            position_size: Recommended position size
            portfolio_balance: Current portfolio balance
            positions: Current portfolio positions
            
        Returns:
            True if trade should be executed, False otherwise
        """
        # Check if directions agree
        directions_agree = (
            technical_direction is not None and
            fundamental_direction is not None and
            technical_direction == fundamental_direction and
            technical_direction in ["buy", "sell"]
        )
        
        # Check portfolio exposure
        current_exposure = sum(position.get("size", 0) for position in positions)
        exposure_ratio = current_exposure / portfolio_balance if portfolio_balance > 0 else 0
        
        # Count existing positions
        position_count = len(positions)
        
        # Check if we should execute
        if not directions_agree:
            logger.info("Trade not executed: Directions don't agree")
            return False
        elif exposure_ratio > 0.8:
            logger.info("Trade not executed: Portfolio exposure too high")
            return False
        elif position_count >= 10:
            logger.info("Trade not executed: Too many open positions")
            return False
        elif position_size < (portfolio_balance * 0.01):
            logger.info("Trade not executed: Position size too small")
            return False
        else:
            return True
    
    def _generate_recommendation(self, execute_trade: bool, position_size: float,
                              portfolio_balance: float, risk_params: Dict[str, Any],
                              positions: List[Dict[str, Any]]) -> str:
        """
        Generate portfolio recommendation based on analysis.
        
        Args:
            execute_trade: Whether to execute the trade
            position_size: Recommended position size
            portfolio_balance: Current portfolio balance
            risk_params: Risk parameters
            positions: Current portfolio positions
            
        Returns:
            Recommendation string (execute, hold, reduce_size)
        """
        if not execute_trade:
            return "hold"
        
        # Check position size relative to portfolio
        position_pct = position_size / portfolio_balance if portfolio_balance > 0 else 0
        if position_pct > self.config["max_position_size_pct"]:
            return "reduce_size"
        
        # Check risk-reward ratio
        risk_reward = risk_params.get("risk_reward_ratio", 0)
        if risk_reward < 2.0:
            return "hold"  # Not worth the risk
        
        return "execute"
    
    def _generate_reasoning(self, symbol: str, recommendation: str,
                          technical_direction: Optional[str], fundamental_direction: Optional[str],
                          position_size: float, volatility: float,
                          portfolio_balance: float, positions: List[Dict[str, Any]],
                          risk_level: str) -> str:
        """
        Generate human-readable reasoning for the portfolio recommendation.
        
        Args:
            Various parameters about the recommendation and portfolio state
            
        Returns:
            Reasoning string
        """
        # Calculate portfolio metrics
        position_pct = position_size / portfolio_balance if portfolio_balance > 0 else 0
        exposure_ratio = sum(position.get("size", 0) for position in positions) / portfolio_balance if portfolio_balance > 0 else 0
        
        # Start with recommendation summary
        if recommendation == "execute":
            reason = f"Portfolio analysis recommends executing the trade for {symbol}."
        elif recommendation == "reduce_size":
            reason = f"Portfolio analysis recommends trading {symbol} with reduced position size."
        else:
            reason = f"Portfolio analysis suggests holding off on {symbol} trading at this time."
        
        # Add position size reasoning
        reason += f" Recommended position size is {position_size:.2f} ({position_pct:.1%} of portfolio)."
        
        # Add volatility assessment
        vol_desc = "high" if volatility > 0.4 else "moderate" if volatility > 0.2 else "low"
        reason += f" {symbol} has {vol_desc} volatility ({volatility:.2f})."
        
        # Add portfolio exposure reasoning
        reason += f" Current portfolio exposure is {exposure_ratio:.1%} with {len(positions)} open positions."
        
        # Add risk profile reasoning
        reason += f" Portfolio risk profile is set to '{risk_level}'."
        
        # Add direction agreement reasoning
        if technical_direction and fundamental_direction:
            if technical_direction == fundamental_direction:
                reason += f" Technical and fundamental analyses agree on '{technical_direction}' direction."
            else:
                reason += f" Technical analysis suggests '{technical_direction}' while fundamental analysis suggests '{fundamental_direction}'."
        
        return reason

# If executed as a script, run a simple demonstration
if __name__ == "__main__":
    # Create mock data for testing
    try:
        import pandas as pd
        import numpy as np
        
        # Create sample market data
        dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.normal(100, 5, 30),
            'high': np.random.normal(105, 5, 30),
            'low': np.random.normal(95, 5, 30),
            'close': np.random.normal(100, 10, 30),
            'volume': np.random.normal(1000000, 200000, 30)
        })
        
        # Sample portfolio data
        portfolio = {
            "balance": 10000.0,
            "positions": [
                {"symbol": "ETHUSDT", "size": 500.0, "entry_price": 2500.0}
            ],
            "risk_level": "moderate"
        }
        
        # Sample agent decisions
        decisions = {
            "technical": {"direction": "buy", "confidence": 0.8},
            "fundamental": {"direction": "buy", "confidence": 0.7}
        }
        
        # Create and test the agent
        agent = PortfolioManagementAgent()
        result = agent.analyze("BTCUSDT", data, portfolio, decisions)
        
        print(json.dumps(result, indent=2))
        
    except ImportError:
        print("Cannot run demonstration: required libraries not installed.")
        print("Install with: pip install pandas numpy")
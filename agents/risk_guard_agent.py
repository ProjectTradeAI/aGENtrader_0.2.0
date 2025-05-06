"""
Risk Guard Agent Module

This agent performs risk assessment and provides safety constraints on trade decisions
for the aGENtrader v0.2.2 system. It protects against excessive risk and ensures
trades comply with the defined risk management policies.
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum

# Add parent directory to path to allow importing from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import the base agent class
from agents.base_agent import BaseAnalystAgent

# Configure logger
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Enum for risk levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"

class RiskGuardAgent(BaseAnalystAgent):
    """RiskGuardAgent for aGENtrader v0.2.2
    
    This agent evaluates trade decisions against risk management policies and
    can modify or override decisions to maintain portfolio safety.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the risk guard agent
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.version = "v0.2.2"
        super().__init__(agent_name="risk_guard")
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Get risk guard specific configuration
        self.risk_config = self.get_agent_config()
        
        # Get trading configuration
        self.trading_config = self.get_trading_config()
        
        # Initialize risk thresholds
        self.max_risk_per_trade_pct = self.risk_config.get("max_risk_per_trade_pct", 2.0)
        self.max_daily_drawdown_pct = self.risk_config.get("max_daily_drawdown_pct", 5.0)
        self.max_position_size_pct = self.risk_config.get("max_position_size_pct", 10.0)
        self.volatility_multiplier = self.risk_config.get("volatility_multiplier", 1.5)
        
        # Initialize risk metrics
        self.daily_trades = []
        self.daily_drawdown = 0.0
        self.risk_level = RiskLevel.LOW
        self.last_assessment_time = datetime.now()
        
        # Portfolio reference data
        self.base_currency = self.trading_config.get("base_currency", "USDT")
        self.starting_balance = self.trading_config.get("starting_balance", 10000)
        
        # Initialize logs directory
        self.logs_dir = os.path.join(parent_dir, "logs")
        self.risk_dir = os.path.join(self.logs_dir, "risk")
        os.makedirs(self.risk_dir, exist_ok=True)
        
        # File paths
        self.risk_log_file = os.path.join(self.risk_dir, "risk_assessment.jsonl")
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.risk_log_file), exist_ok=True)
        
        self.logger.info(f"Risk Guard Agent initialized with max risk per trade: {self.max_risk_per_trade_pct}%")
        self.logger.info(f"Max daily drawdown: {self.max_daily_drawdown_pct}%, max position size: {self.max_position_size_pct}%")
    
    def get_trading_config(self):
        """
        Get trading configuration from settings file, with fallback to defaults.
        
        Returns:
            Dictionary containing trading configuration
        """
        # Use the base agent's load_config_section method
        return self.load_config_section('trading')
    
    def get_agent_config(self):
        """
        Get risk guard specific configuration, with fallback to defaults.
        
        Returns:
            Dictionary containing risk guard configuration
        """
        # Use the base agent's load_config_section method
        return self.load_config_section('risk_guard')
    
    def evaluate_market_risk(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate market risk based on volatility, volume, and liquidity metrics.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Dictionary with market risk assessment
        """
        # Default values if data is missing
        current_price = market_data.get('current_price', 0)
        volatility = market_data.get('volatility', {}).get('value', 0)
        volume = market_data.get('volume', 0)
        
        # Calculate risk metrics
        volatility_risk = min(100, volatility * self.volatility_multiplier)
        volume_risk = 0
        
        # Evaluate volume trend if available
        if 'volume_trend' in market_data:
            volume_change = market_data['volume_trend'].get('change_pct', 0)
            if volume_change < -30:
                volume_risk = 80  # Significant volume decrease is risky
            elif volume_change < -15:
                volume_risk = 60  # Moderate volume decrease
            elif volume_change > 50:
                volume_risk = 70  # Unusual volume spike
            elif volume_change > 30:
                volume_risk = 50  # Significant volume increase
        
        # Calculate liquidity risk if data available
        liquidity_risk = 50  # Default moderate risk
        if 'liquidity' in market_data:
            bid_ask_spread = market_data['liquidity'].get('bid_ask_spread_pct', 0)
            order_book_depth = market_data['liquidity'].get('depth', 0)
            
            if bid_ask_spread > 0.5:
                liquidity_risk = 90  # High spread indicates low liquidity
            elif bid_ask_spread > 0.2:
                liquidity_risk = 70  # Moderate spread
            elif bid_ask_spread < 0.05:
                liquidity_risk = 20  # Very tight spread
            
            # Adjust for order book depth if available
            if order_book_depth > 0:
                normalized_depth = min(1, order_book_depth / 1000000)  # Normalize to 0-1
                liquidity_risk = liquidity_risk * (1 - normalized_depth * 0.5)  # Reduce risk based on depth
        
        # Calculate overall market risk
        overall_risk = (volatility_risk * 0.5) + (volume_risk * 0.2) + (liquidity_risk * 0.3)
        
        # Determine risk level
        risk_level = RiskLevel.LOW
        if overall_risk > 80:
            risk_level = RiskLevel.EXTREME
        elif overall_risk > 65:
            risk_level = RiskLevel.HIGH
        elif overall_risk > 40:
            risk_level = RiskLevel.MEDIUM
        
        # Prepare result
        result = {
            "timestamp": datetime.now().isoformat(),
            "symbol": market_data.get('symbol', 'UNKNOWN'),
            "current_price": current_price,
            "volatility_risk": volatility_risk,
            "volume_risk": volume_risk,
            "liquidity_risk": liquidity_risk,
            "overall_risk": overall_risk,
            "risk_level": risk_level.value,
            "risk_factors": []
        }
        
        # Add specific risk factors
        if volatility_risk > 70:
            result["risk_factors"].append(f"High volatility: {volatility_risk:.1f}%")
        if volume_risk > 60:
            result["risk_factors"].append(f"Volume anomaly: {volume_risk:.1f}%")
        if liquidity_risk > 60:
            result["risk_factors"].append(f"Liquidity concern: {liquidity_risk:.1f}%")
        
        return result
    
    def evaluate_position_risk(self, trade_plan: Dict[str, Any], portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate position risk based on trade size, existing exposure, and market conditions.
        
        Args:
            trade_plan: Dictionary containing trade plan
            portfolio_data: Dictionary containing portfolio state
            
        Returns:
            Dictionary with position risk assessment
        """
        # Get trade details
        symbol = trade_plan.get('symbol', 'UNKNOWN')
        action = trade_plan.get('signal', 'UNKNOWN')
        position_size = trade_plan.get('position_size', 0)
        entry_price = trade_plan.get('entry_price', 0)
        
        # Calculate position value
        position_value = position_size * entry_price
        
        # Get portfolio details
        portfolio_value = portfolio_data.get('portfolio_value', self.starting_balance)
        total_exposure = portfolio_data.get('total_exposure_pct', 0)
        
        # Calculate position size as percentage of portfolio
        position_size_pct = (position_value / portfolio_value) * 100 if portfolio_value > 0 else 0
        
        # Get existing position in the same asset if any
        asset_exposure = 0
        asset_exposures = portfolio_data.get('asset_exposures', {})
        if symbol in asset_exposures:
            asset_exposure = asset_exposures[symbol]
        
        # Calculate total exposure after this trade
        new_total_exposure = total_exposure + position_size_pct
        new_asset_exposure = asset_exposure + position_size_pct
        
        # Evaluate position size risk
        position_size_risk = 0
        if position_size_pct > self.max_position_size_pct:
            position_size_risk = 100  # Exceeds maximum position size
        elif position_size_pct > (self.max_position_size_pct * 0.8):
            position_size_risk = 80  # Near maximum position size
        elif position_size_pct > (self.max_position_size_pct * 0.5):
            position_size_risk = 50  # Moderate position size
        else:
            position_size_risk = 30  # Small position size
        
        # Evaluate total exposure risk
        exposure_risk = 0
        max_total_exposure = portfolio_data.get('max_total_exposure_pct', 80)
        if new_total_exposure > max_total_exposure:
            exposure_risk = 100  # Exceeds maximum exposure
        elif new_total_exposure > (max_total_exposure * 0.9):
            exposure_risk = 90  # Very close to maximum exposure
        elif new_total_exposure > (max_total_exposure * 0.8):
            exposure_risk = 80  # Near maximum exposure
        elif new_total_exposure > (max_total_exposure * 0.6):
            exposure_risk = 60  # Moderate exposure
        else:
            exposure_risk = 40  # Low exposure
        
        # Calculate overall position risk
        overall_risk = (position_size_risk * 0.6) + (exposure_risk * 0.4)
        
        # Determine risk level
        risk_level = RiskLevel.LOW
        if overall_risk > 80:
            risk_level = RiskLevel.EXTREME
        elif overall_risk > 65:
            risk_level = RiskLevel.HIGH
        elif overall_risk > 40:
            risk_level = RiskLevel.MEDIUM
        
        # Prepare result
        result = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "action": action,
            "position_size": position_size,
            "position_value": position_value,
            "position_size_pct": position_size_pct,
            "new_total_exposure": new_total_exposure,
            "new_asset_exposure": new_asset_exposure,
            "position_size_risk": position_size_risk,
            "exposure_risk": exposure_risk,
            "overall_risk": overall_risk,
            "risk_level": risk_level.value,
            "risk_factors": []
        }
        
        # Add specific risk factors
        if position_size_pct > self.max_position_size_pct:
            result["risk_factors"].append(f"Position size ({position_size_pct:.1f}%) exceeds maximum ({self.max_position_size_pct:.1f}%)")
        if new_total_exposure > max_total_exposure:
            result["risk_factors"].append(f"Total exposure ({new_total_exposure:.1f}%) exceeds maximum ({max_total_exposure:.1f}%)")
        if position_size_risk > 70:
            result["risk_factors"].append(f"Large position size relative to portfolio: {position_size_pct:.1f}%")
        
        return result
    
    def evaluate_drawdown_risk(self, trade_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate drawdown risk based on stop loss placement and recent performance.
        
        Args:
            trade_plan: Dictionary containing trade plan
            
        Returns:
            Dictionary with drawdown risk assessment
        """
        # Get trade details
        symbol = trade_plan.get('symbol', 'UNKNOWN')
        action = trade_plan.get('signal', 'UNKNOWN')
        entry_price = trade_plan.get('entry_price', 0)
        stop_loss = trade_plan.get('stop_loss', 0)
        position_size = trade_plan.get('position_size', 0)
        
        # Skip if HOLD or no position size
        if action == "HOLD" or position_size == 0:
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "action": action,
                "risk_level": RiskLevel.LOW.value,
                "overall_risk": 0,
                "risk_pct": 0,
                "daily_drawdown_pct": self.daily_drawdown,
                "risk_factors": []
            }
        
        # Calculate potential loss percentage
        risk_pct = 0
        if stop_loss > 0 and entry_price > 0:
            if action == "BUY":
                risk_pct = ((entry_price - stop_loss) / entry_price) * 100
            elif action == "SELL":
                risk_pct = ((stop_loss - entry_price) / entry_price) * 100
        
        # Get daily drawdown
        daily_drawdown_pct = self.daily_drawdown
        
        # Potential loss in base currency
        potential_loss = (position_size * entry_price) * (risk_pct / 100)
        
        # Evaluate stop loss risk
        stop_loss_risk = 0
        if risk_pct > self.max_risk_per_trade_pct:
            stop_loss_risk = 100  # Exceeds maximum risk per trade
        elif risk_pct > (self.max_risk_per_trade_pct * 0.8):
            stop_loss_risk = 80  # Near maximum risk per trade
        elif risk_pct > (self.max_risk_per_trade_pct * 0.5):
            stop_loss_risk = 50  # Moderate risk per trade
        else:
            stop_loss_risk = 30  # Low risk per trade
        
        # Evaluate drawdown risk
        drawdown_risk = 0
        if daily_drawdown_pct + risk_pct > self.max_daily_drawdown_pct:
            drawdown_risk = 100  # Could exceed maximum daily drawdown
        elif daily_drawdown_pct + risk_pct > (self.max_daily_drawdown_pct * 0.8):
            drawdown_risk = 80  # Could approach maximum daily drawdown
        elif daily_drawdown_pct > (self.max_daily_drawdown_pct * 0.5):
            drawdown_risk = 60  # Already significant daily drawdown
        else:
            drawdown_risk = 20  # Low drawdown risk
        
        # Calculate overall drawdown risk
        overall_risk = (stop_loss_risk * 0.7) + (drawdown_risk * 0.3)
        
        # Determine risk level
        risk_level = RiskLevel.LOW
        if overall_risk > 80:
            risk_level = RiskLevel.EXTREME
        elif overall_risk > 65:
            risk_level = RiskLevel.HIGH
        elif overall_risk > 40:
            risk_level = RiskLevel.MEDIUM
        
        # Prepare result
        result = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "action": action,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "risk_pct": risk_pct,
            "potential_loss": potential_loss,
            "daily_drawdown_pct": daily_drawdown_pct,
            "stop_loss_risk": stop_loss_risk,
            "drawdown_risk": drawdown_risk,
            "overall_risk": overall_risk,
            "risk_level": risk_level.value,
            "risk_factors": []
        }
        
        # Add specific risk factors
        if risk_pct > self.max_risk_per_trade_pct:
            result["risk_factors"].append(f"Stop loss risk ({risk_pct:.1f}%) exceeds maximum ({self.max_risk_per_trade_pct:.1f}%)")
        if daily_drawdown_pct + risk_pct > self.max_daily_drawdown_pct:
            result["risk_factors"].append(f"Potential daily drawdown ({daily_drawdown_pct + risk_pct:.1f}%) exceeds maximum ({self.max_daily_drawdown_pct:.1f}%)")
        if stop_loss == 0:
            result["risk_factors"].append("No stop loss specified")
        
        return result
    
    def adjust_trade_plan(self, trade_plan: Dict[str, Any], risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust the trade plan based on risk assessment.
        
        Args:
            trade_plan: Original trade plan
            risk_assessment: Risk assessment dictionary
            
        Returns:
            Adjusted trade plan
        """
        # Skip if no position size or HOLD
        if not trade_plan or trade_plan.get('position_size', 0) == 0 or trade_plan.get('signal') == "HOLD":
            return trade_plan
        
        # Create a new trade plan to avoid modifying the original
        adjusted_plan = trade_plan.copy()
        
        # Get risk factors
        overall_risk_level = risk_assessment.get('risk_level', RiskLevel.LOW.value)
        market_risk = risk_assessment.get('market_risk', {}).get('risk_level', RiskLevel.LOW.value)
        position_risk = risk_assessment.get('position_risk', {}).get('risk_level', RiskLevel.LOW.value)
        drawdown_risk = risk_assessment.get('drawdown_risk', {}).get('risk_level', RiskLevel.LOW.value)
        
        # Check if we need to override the decision
        risk_factors = []
        adjustments_made = False
        
        # Original values
        original_position_size = adjusted_plan.get('position_size', 0)
        original_stop_loss = adjusted_plan.get('stop_loss', 0)
        
        # EXTREME risk - override to HOLD unless it's an exit
        if overall_risk_level == RiskLevel.EXTREME.value and adjusted_plan.get('signal') != "EXIT":
            adjusted_plan['signal'] = "HOLD"
            adjusted_plan['position_size'] = 0
            risk_factors.append("EXTREME risk level - trade overridden to HOLD")
            adjustments_made = True
        
        # HIGH risk - reduce position size
        elif overall_risk_level == RiskLevel.HIGH.value:
            # Reduce position size by 50%
            adjusted_plan['position_size'] = original_position_size * 0.5
            risk_factors.append(f"HIGH risk level - position size reduced by 50% (from {original_position_size} to {adjusted_plan['position_size']})")
            adjustments_made = True
            
            # Tighten stop loss if possible
            if original_stop_loss > 0 and position_risk == RiskLevel.HIGH.value:
                entry_price = adjusted_plan.get('entry_price', 0)
                if adjusted_plan.get('signal') == "BUY":
                    # For buying, move stop loss closer to entry (reduce risk)
                    new_stop_loss = entry_price * 0.98  # 2% below entry
                    adjusted_plan['stop_loss'] = max(new_stop_loss, original_stop_loss)
                elif adjusted_plan.get('signal') == "SELL":
                    # For selling, move stop loss closer to entry (reduce risk)
                    new_stop_loss = entry_price * 1.02  # 2% above entry
                    adjusted_plan['stop_loss'] = min(new_stop_loss, original_stop_loss) if original_stop_loss > 0 else new_stop_loss
                
                risk_factors.append(f"Stop loss adjusted for risk management (from {original_stop_loss} to {adjusted_plan['stop_loss']})")
        
        # MEDIUM risk - adjust if specific risks are high
        elif overall_risk_level == RiskLevel.MEDIUM.value:
            # Check if any specific risk is HIGH
            if market_risk == RiskLevel.HIGH.value or position_risk == RiskLevel.HIGH.value or drawdown_risk == RiskLevel.HIGH.value:
                # Reduce position size by 25%
                adjusted_plan['position_size'] = original_position_size * 0.75
                risk_factors.append(f"MEDIUM overall risk but HIGH specific risk - position size reduced by 25% (from {original_position_size} to {adjusted_plan['position_size']})")
                adjustments_made = True
        
        # Add risk assessment to the trade plan
        adjusted_plan['risk_assessment'] = {
            'original_position_size': original_position_size,
            'adjusted_position_size': adjusted_plan.get('position_size'),
            'overall_risk_level': overall_risk_level,
            'market_risk': market_risk,
            'position_risk': position_risk,
            'drawdown_risk': drawdown_risk,
            'risk_factors': risk_factors,
            'adjustments_made': adjustments_made
        }
        
        return adjusted_plan
    
    def log_risk_assessment(self, assessment: Dict[str, Any]) -> None:
        """
        Log risk assessment to file.
        
        Args:
            assessment: Risk assessment dictionary
        """
        try:
            with open(self.risk_log_file, 'a') as f:
                f.write(json.dumps(assessment) + '\n')
        except Exception as e:
            self.logger.error(f"Error logging risk assessment: {e}")
    
    def update_daily_metrics(self, trade_result: Optional[Dict[str, Any]] = None) -> None:
        """
        Update daily trading metrics.
        
        Args:
            trade_result: Result of a closed trade (optional)
        """
        # Get current time
        now = datetime.now()
        
        # If a new day has started, reset daily metrics
        if now.date() > self.last_assessment_time.date():
            self.daily_trades = []
            self.daily_drawdown = 0.0
            self.logger.info("New day - reset daily trading metrics")
        
        # Update last assessment time
        self.last_assessment_time = now
        
        # Update metrics with trade result if provided
        if trade_result:
            self.daily_trades.append(trade_result)
            
            # Update daily drawdown if trade was a loss
            pnl = trade_result.get('pnl', 0)
            if pnl < 0:
                # Convert to percentage of starting balance
                pnl_pct = abs(pnl) / self.starting_balance * 100
                self.daily_drawdown += pnl_pct
                self.logger.info(f"Updated daily drawdown to {self.daily_drawdown:.2f}%")
    
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Run the risk guard agent.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Dictionary containing risk assessment and adjusted trade plan
        """
        # Get input parameters
        trade_plan = kwargs.get('trade_plan', {})
        market_data = kwargs.get('market_data', {})
        portfolio_data = kwargs.get('portfolio_data', {})
        update_metrics = kwargs.get('update_metrics', False)
        trade_result = kwargs.get('trade_result', None)
        
        # Update daily metrics if requested
        if update_metrics:
            self.update_daily_metrics(trade_result)
        
        # Skip assessment if no trade plan
        if not trade_plan or not market_data:
            return {
                "status": "SKIPPED",
                "reason": "No trade plan or market data provided",
                "timestamp": datetime.now().isoformat(),
                "adjusted_trade_plan": None
            }
        
        # Perform risk assessments
        market_risk = self.evaluate_market_risk(market_data)
        position_risk = self.evaluate_position_risk(trade_plan, portfolio_data)
        drawdown_risk = self.evaluate_drawdown_risk(trade_plan)
        
        # Determine overall risk level
        risk_levels = {
            RiskLevel.LOW.value: 1,
            RiskLevel.MEDIUM.value: 2,
            RiskLevel.HIGH.value: 3,
            RiskLevel.EXTREME.value: 4
        }
        
        market_risk_value = risk_levels.get(market_risk.get('risk_level', RiskLevel.LOW.value), 1)
        position_risk_value = risk_levels.get(position_risk.get('risk_level', RiskLevel.LOW.value), 1)
        drawdown_risk_value = risk_levels.get(drawdown_risk.get('risk_level', RiskLevel.LOW.value), 1)
        
        # Weight the risks (market: 30%, position: 40%, drawdown: 30%)
        overall_risk_value = (market_risk_value * 0.3) + (position_risk_value * 0.4) + (drawdown_risk_value * 0.3)
        
        # Map back to risk level
        overall_risk_level = RiskLevel.LOW.value
        if overall_risk_value > 3.5:
            overall_risk_level = RiskLevel.EXTREME.value
        elif overall_risk_value > 2.5:
            overall_risk_level = RiskLevel.HIGH.value
        elif overall_risk_value > 1.5:
            overall_risk_level = RiskLevel.MEDIUM.value
        
        # Compile full assessment
        assessment = {
            "timestamp": datetime.now().isoformat(),
            "symbol": trade_plan.get('symbol', 'UNKNOWN'),
            "action": trade_plan.get('signal', 'UNKNOWN'),
            "market_risk": market_risk,
            "position_risk": position_risk,
            "drawdown_risk": drawdown_risk,
            "overall_risk_level": overall_risk_level,
            "overall_risk_value": overall_risk_value
        }
        
        # Adjust trade plan based on risk assessment
        adjusted_trade_plan = self.adjust_trade_plan(trade_plan, {
            "risk_level": overall_risk_level,
            "market_risk": market_risk,
            "position_risk": position_risk,
            "drawdown_risk": drawdown_risk
        })
        
        # Log risk assessment
        self.log_risk_assessment(assessment)
        
        # Prepare result
        result = {
            "status": "SUCCESS",
            "timestamp": datetime.now().isoformat(),
            "risk_assessment": assessment,
            "adjusted_trade_plan": adjusted_trade_plan,
            "risk_level": overall_risk_level,
            "version": self.version
        }
        
        return result
    
    def analyze(self, symbol: Optional[str] = None, interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Perform risk analysis for BaseAnalystAgent interface compatibility.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1h', '15m')
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with risk analysis results
        """
        # Get market data if provided
        market_data = kwargs.get('market_data', {})
        
        # Ensure we have symbol from arguments or market data
        if symbol is None and 'symbol' in market_data:
            symbol = market_data['symbol']
        
        # Evaluate market risk
        market_risk = self.evaluate_market_risk(market_data)
        
        # Map risk level to signal and confidence
        risk_level = market_risk.get('risk_level', RiskLevel.LOW.value)
        
        # Default signal is NEUTRAL
        signal = "NEUTRAL"
        confidence = 50
        reasoning = "Insufficient risk data for assessment."
        
        # Adjust signal based on risk level
        if risk_level == RiskLevel.EXTREME.value:
            signal = "SELL"  # Suggest exiting positions in extreme risk
            confidence = 90
            reasoning = "Extreme market risk detected. Consider reducing exposure."
        elif risk_level == RiskLevel.HIGH.value:
            signal = "HOLD"  # Suggest not entering new positions in high risk
            confidence = 80
            reasoning = "High market risk. Caution advised for new positions."
        elif risk_level == RiskLevel.MEDIUM.value:
            signal = "NEUTRAL"
            confidence = 60
            reasoning = "Medium market risk. Normal trading conditions with caution."
        elif risk_level == RiskLevel.LOW.value:
            signal = "NEUTRAL"
            confidence = 70
            reasoning = "Low market risk. Favorable trading conditions."
        
        # Get specific risk factors
        risk_factors = market_risk.get('risk_factors', [])
        if risk_factors:
            reasoning += " " + " ".join(risk_factors)
        
        # Prepare analysis result
        result = {
            "signal": signal,
            "confidence": confidence,
            "reasoning": reasoning,
            "symbol": symbol if symbol else "UNKNOWN",
            "interval": interval if interval else "N/A",
            "timestamp": datetime.now().isoformat(),
            "risk_level": risk_level,
            "market_risk": market_risk,
            "version": self.version
        }
        
        return result

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the risk guard agent
    agent = RiskGuardAgent()
    
    # Example market data
    market_data = {
        "symbol": "BTC/USDT",
        "current_price": 50000,
        "volatility": {
            "value": 2.5,
            "period": "24h"
        },
        "volume": 1000000,
        "volume_trend": {
            "change_pct": -20
        },
        "liquidity": {
            "bid_ask_spread_pct": 0.1,
            "depth": 500000
        }
    }
    
    # Example portfolio data
    portfolio_data = {
        "portfolio_value": 10000,
        "total_exposure_pct": 30,
        "max_total_exposure_pct": 80,
        "asset_exposures": {
            "BTC/USDT": 10
        }
    }
    
    # Example trade plan
    trade_plan = {
        "symbol": "BTC/USDT",
        "signal": "BUY",
        "entry_price": 50000,
        "stop_loss": 48000,
        "take_profit": 55000,
        "position_size": 0.1,
        "confidence": 75
    }
    
    # Run the risk guard agent
    result = agent.run(
        trade_plan=trade_plan,
        market_data=market_data,
        portfolio_data=portfolio_data
    )
    
    # Print the result
    print(json.dumps(result, indent=2))
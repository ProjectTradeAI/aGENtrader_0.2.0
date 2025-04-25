#!/usr/bin/env python
"""
RiskGuardAgent for aGENtrader v2.1

This agent evaluates trading decisions for risk compliance before execution.
It acts as a final safety check to prevent trades that exceed risk thresholds.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional, List

import yaml

# Setup logger
logger = logging.getLogger("aGENtrader.risk_guard")

class RiskGuardAgent:
    """
    Agent responsible for evaluating trades against risk thresholds.
    
    Acts as a safety mechanism to prevent excessive risk by:
    - Enforcing max position size limits
    - Rejecting trades during excessive volatility
    - Preventing too many concurrent positions
    - Enforcing minimum time between trades
    - Tracking drawdown limits
    """
    
    def __init__(self, config_path: str = "config/settings.yaml", trade_book_manager=None):
        """
        Initialize the risk guard agent.
        
        Args:
            config_path: Path to settings file
            trade_book_manager: Optional TradeBookManager instance for checking open positions
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.trade_book = trade_book_manager
        
        # Setup rejected trades log
        self.rejected_log_path = "logs/rejected_trades.jsonl"
        os.makedirs(os.path.dirname(self.rejected_log_path), exist_ok=True)
        
        # Initialize trade history tracking
        self.trade_history = []
        self.last_trade_time = 0
        
        # Extract risk guard settings
        self.enabled = self.config.get("risk_guard", {}).get("enabled", True)
        self.max_position_size = self.config.get("risk_guard", {}).get("max_position_size", 0.30)
        self.max_confidence = self.config.get("risk_guard", {}).get("max_confidence", 95)
        self.min_confidence = self.config.get("risk_guard", {}).get("min_confidence", 40)
        self.max_volatility = self.config.get("risk_guard", {}).get("max_volatility", 0.07)
        self.max_concurrent_positions = self.config.get("risk_guard", {}).get("max_concurrent_positions", 3)
        self.max_daily_trades = self.config.get("risk_guard", {}).get("max_daily_trades", 10)
        self.min_trade_interval = self.config.get("risk_guard", {}).get("min_trade_interval", 3600)
        self.max_drawdown = self.config.get("risk_guard", {}).get("max_drawdown", 0.15)
        self.restricted_symbols = self.config.get("risk_guard", {}).get("restricted_symbols", [])
        
        logger.info(f"RiskGuardAgent initialized (enabled: {self.enabled})")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as file:
                    return yaml.safe_load(file)
            else:
                logger.warning(f"Configuration file {config_path} not found. Using defaults.")
                return {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def evaluate_trade(self, trade_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Evaluate a proposed trade against risk thresholds.
        
        Args:
            trade_payload: Dictionary with trade information
                Required keys:
                - symbol: Trading symbol
                - action: Trade action (BUY, SELL)
                - position_size: Position size (0.0-1.0)
                - confidence: Confidence level (0-100)
                Optional keys:
                - volatility: Market volatility
                - timestamp: Trade timestamp
        
        Returns:
            Tuple with (accepted, reason)
            - accepted: Boolean indicating if trade is accepted
            - reason: If rejected, the reason for rejection, otherwise None
        """
        # If risk guard is disabled, always accept
        if not self.enabled:
            return True, None
        
        symbol = trade_payload.get("symbol")
        action = trade_payload.get("action")
        position_size = trade_payload.get("position_size", 0.0)
        confidence = trade_payload.get("confidence", 0)
        volatility = trade_payload.get("volatility")
        
        # Check for missing required fields
        required_fields = ["symbol", "action", "position_size"]
        missing_fields = [field for field in required_fields if field not in trade_payload]
        if missing_fields:
            reason = f"Missing required fields: {', '.join(missing_fields)}"
            self._log_rejected_trade(trade_payload, reason)
            return False, reason
        
        # Run all risk checks
        checks = [
            self._check_position_size(position_size),
            self._check_confidence(confidence),
            self._check_volatility(volatility),
            self._check_concurrent_positions(symbol),
            self._check_trade_frequency(),
            self._check_restricted_symbols(symbol),
            self._check_drawdown()
        ]
        
        # Filter out None values (passed checks)
        failures = [reason for accepted, reason in checks if not accepted and reason is not None]
        
        if failures:
            combined_reason = "; ".join(failures)
            self._log_rejected_trade(trade_payload, combined_reason)
            return False, combined_reason
        
        # All checks passed
        logger.info(f"Trade accepted: {symbol} {action}")
        return True, None
    
    def _check_position_size(self, position_size: float) -> Tuple[bool, Optional[str]]:
        """Check if position size exceeds maximum allowed."""
        if position_size > self.max_position_size:
            reason = f"Position size too large: {position_size:.2%} > {self.max_position_size:.2%}"
            logger.warning(reason)
            return False, reason
        return True, None
    
    def _check_confidence(self, confidence: float) -> Tuple[bool, Optional[str]]:
        """Check if confidence is within acceptable range."""
        if confidence > self.max_confidence:
            reason = f"Confidence too high: {confidence} > {self.max_confidence}"
            logger.warning(reason)
            return False, reason
        
        if confidence < self.min_confidence:
            reason = f"Confidence too low: {confidence} < {self.min_confidence}"
            logger.warning(reason)
            return False, reason
            
        return True, None
    
    def _check_volatility(self, volatility: Optional[float]) -> Tuple[bool, Optional[str]]:
        """Check if volatility exceeds maximum allowed."""
        if volatility is None:
            # If volatility isn't provided, we can't check it
            return True, None
            
        if volatility > self.max_volatility:
            reason = f"Volatility too high: {volatility:.2%} > {self.max_volatility:.2%}"
            logger.warning(reason)
            return False, reason
        return True, None
    
    def _check_concurrent_positions(self, symbol: Any) -> Tuple[bool, Optional[str]]:
        """Check if adding this position would exceed max concurrent positions."""
        if not self.trade_book or symbol is None:
            # If no trade book manager is provided or no symbol, we can't check open positions
            return True, None
            
        open_positions = self.trade_book.list_open_trades()
        
        # If we already have a position for this symbol, it's a replacement, so no impact on count
        if any(pos.get("symbol") == symbol for pos in open_positions):
            return True, None
            
        if len(open_positions) >= self.max_concurrent_positions:
            reason = f"Too many concurrent positions: {len(open_positions)} >= {self.max_concurrent_positions}"
            logger.warning(reason)
            return False, reason
        return True, None
    
    def _check_trade_frequency(self) -> Tuple[bool, Optional[str]]:
        """Check if trading too frequently."""
        current_time = time.time()
        time_since_last_trade = current_time - self.last_trade_time
        
        if time_since_last_trade < self.min_trade_interval:
            reason = f"Trading too frequently: {time_since_last_trade:.0f}s < {self.min_trade_interval}s minimum"
            logger.warning(reason)
            return False, reason
            
        # Count daily trades
        today = datetime.now().date()
        today_start_time = datetime.combine(today, datetime.min.time()).timestamp()
        
        daily_trades = len([t for t in self.trade_history 
                           if t.get("timestamp", 0) >= today_start_time])
        
        if daily_trades >= self.max_daily_trades:
            reason = f"Daily trade limit reached: {daily_trades} >= {self.max_daily_trades}"
            logger.warning(reason)
            return False, reason
            
        return True, None
    
    def _check_restricted_symbols(self, symbol: Any) -> Tuple[bool, Optional[str]]:
        """Check if symbol is on the restricted list."""
        if symbol is None:
            return True, None
            
        if symbol in self.restricted_symbols:
            reason = f"Symbol {symbol} is restricted from trading"
            logger.warning(reason)
            return False, reason
        return True, None
    
    def _check_drawdown(self) -> Tuple[bool, Optional[str]]:
        """Check if current drawdown exceeds maximum allowed."""
        # This would need access to portfolio performance metrics
        # Placeholder for now
        return True, None
    
    def record_trade(self, trade_payload: Dict[str, Any]):
        """
        Record a trade that was executed.
        
        Args:
            trade_payload: Dictionary with trade information
        """
        # Add timestamp if not present
        if "timestamp" not in trade_payload:
            trade_payload["timestamp"] = time.time()
            
        # Update last trade time
        self.last_trade_time = trade_payload["timestamp"]
        
        # Add to history
        self.trade_history.append(trade_payload.copy())
        
        # Keep trade history manageable (retain last 100 trades)
        if len(self.trade_history) > 100:
            self.trade_history = self.trade_history[-100:]
    
    def _log_rejected_trade(self, trade_payload: Dict[str, Any], reason: str):
        """
        Log a rejected trade to the rejected trades log.
        
        Args:
            trade_payload: Dictionary with trade information
            reason: Reason for rejection
        """
        try:
            # Create a log entry with rejection details
            log_entry = trade_payload.copy()
            log_entry["timestamp"] = log_entry.get("timestamp", datetime.now().isoformat())
            log_entry["rejection_reason"] = reason
            log_entry["rejection_time"] = datetime.now().isoformat()
            
            # Append to the log file
            with open(self.rejected_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
            logger.info(f"Trade rejected: {log_entry['symbol']} - {reason}")
                
        except Exception as e:
            logger.error(f"Error logging rejected trade: {e}")
            
    def reload_config(self):
        """Reload configuration from YAML file."""
        self.config = self._load_config(self.config_path)
        
        # Update settings
        self.enabled = self.config.get("risk_guard", {}).get("enabled", True)
        self.max_position_size = self.config.get("risk_guard", {}).get("max_position_size", 0.30)
        self.max_confidence = self.config.get("risk_guard", {}).get("max_confidence", 95)
        self.min_confidence = self.config.get("risk_guard", {}).get("min_confidence", 40)
        self.max_volatility = self.config.get("risk_guard", {}).get("max_volatility", 0.07)
        self.max_concurrent_positions = self.config.get("risk_guard", {}).get("max_concurrent_positions", 3)
        self.max_daily_trades = self.config.get("risk_guard", {}).get("max_daily_trades", 10)
        self.min_trade_interval = self.config.get("risk_guard", {}).get("min_trade_interval", 3600)
        self.max_drawdown = self.config.get("risk_guard", {}).get("max_drawdown", 0.15)
        self.restricted_symbols = self.config.get("risk_guard", {}).get("restricted_symbols", [])
        
        logger.info(f"RiskGuardAgent configuration reloaded (enabled: {self.enabled})")
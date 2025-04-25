#!/usr/bin/env python
"""
TradeBookManager for aGENtrader v2

This module provides trade tracking and persistence functionality, allowing
the system to track open positions, avoid redundant entries, and maintain
a history of all trades for analysis.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Setup logger
logger = logging.getLogger("aGENtrader.trade_book")

class TradeBookManager:
    """
    Manages the trading book for the aGENtrader system.
    
    Responsibilities:
    - Track all open and closed trades
    - Persist trades to disk for analysis and recovery
    - Enable queries for current portfolio state
    - Prevent redundant trade entries
    """
    
    def __init__(self, trade_log_path: str = "logs/trade_book.jsonl"):
        """
        Initialize the trade book manager.
        
        Args:
            trade_log_path: Path to the trade log file
        """
        self.trade_log_path = trade_log_path
        self.open_trades = {}  # Dict of symbol -> trade info
        self.closed_trades = []  # List of closed trades
        
        # Ensure the log directory exists
        os.makedirs(os.path.dirname(trade_log_path), exist_ok=True)
        
        # Load existing trades from disk if available
        self._load_trades_from_disk()
        
        logger.info(f"TradeBookManager initialized with {len(self.open_trades)} open trades")
    
    def _load_trades_from_disk(self) -> None:
        """Load existing trades from the trade log file."""
        if not os.path.exists(self.trade_log_path):
            logger.info(f"No existing trade log found at {self.trade_log_path}")
            return
        
        try:
            with open(self.trade_log_path, 'r') as f:
                for line in f:
                    try:
                        trade = json.loads(line.strip())
                        if trade.get("status") == "open":
                            self.open_trades[trade["symbol"]] = trade
                        else:
                            self.closed_trades.append(trade)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse trade log line: {line}")
                        continue
            
            logger.info(f"Loaded {len(self.open_trades)} open trades and {len(self.closed_trades)} closed trades")
        
        except Exception as e:
            logger.error(f"Error loading trades from disk: {e}")
    
    def record_trade(self, trade: Dict[str, Any]) -> None:
        """
        Record a new trade in the system.
        
        Args:
            trade: Dictionary containing trade information
                Required keys: symbol, action, confidence, entry_price
                Optional keys: position_size, reason, stop_loss, take_profit
        """
        if not trade.get("symbol"):
            logger.error("Cannot record trade without a symbol")
            return
        
        # Check for required fields
        required_fields = ["action", "confidence", "entry_price"]
        for field in required_fields:
            if field not in trade:
                logger.error(f"Cannot record trade - missing required field: {field}")
                return
        
        # Add metadata
        trade["timestamp"] = trade.get("timestamp", datetime.utcnow().isoformat())
        trade["status"] = "open"
        trade["position_size"] = trade.get("position_size", 1.0)
        
        # If we already have an open trade for this symbol, close it first
        if trade["symbol"] in self.open_trades:
            logger.warning(
                f"Already have an open {self.open_trades[trade['symbol']]['action']} trade for {trade['symbol']}. "
                f"Closing it before opening a new {trade['action']} position."
            )
            self.close_trade(
                trade["symbol"], 
                exit_price=trade["entry_price"],
                reason="Replaced by new trade"
            )
        
        # Store the trade
        self.open_trades[trade["symbol"]] = trade
        
        # Persist to disk
        self._append_trade_to_log(trade)
        
        logger.info(
            f"Recorded new {trade['action']} trade for {trade['symbol']} "
            f"at {trade['entry_price']} with confidence {trade['confidence']}"
        )
    
    def close_trade(
        self, 
        symbol: str, 
        exit_price: Optional[float] = None,
        pnl: Optional[float] = None,
        reason: str = "Manual close"
    ) -> Optional[Dict[str, Any]]:
        """
        Close an open trade.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price (if None, the trade will be closed without P&L calculation)
            pnl: Explicit P&L value (if None, calculated from prices)
            reason: Reason for closing the trade
            
        Returns:
            Closed trade information or None if no open trade found
        """
        if symbol not in self.open_trades:
            logger.warning(f"Cannot close trade - no open trade found for {symbol}")
            return None
        
        # Get the open trade
        trade = self.open_trades[symbol]
        
        # Update trade information
        trade["status"] = "closed"
        trade["exit_timestamp"] = datetime.utcnow().isoformat()
        trade["exit_price"] = exit_price
        trade["close_reason"] = reason
        
        # Calculate P&L if possible
        if pnl is not None:
            trade["pnl"] = pnl
        elif exit_price is not None and "entry_price" in trade:
            direction = 1 if trade["action"] == "BUY" else -1
            trade["pnl"] = direction * (exit_price - trade["entry_price"]) * trade["position_size"]
        
        # Move to closed trades
        del self.open_trades[symbol]
        self.closed_trades.append(trade)
        
        # Persist updated trade to disk
        self._append_trade_to_log(trade)
        
        logger.info(
            f"Closed {trade['action']} trade for {symbol} "
            f"with reason: {reason}"
        )
        
        if "pnl" in trade:
            logger.info(f"Trade P&L: {trade['pnl']:.4f}")
        
        return trade
    
    def get_open_trade(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an open trade for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with trade information or None if no open trade
        """
        return self.open_trades.get(symbol)
    
    def get_position_direction(self, symbol: str) -> Optional[str]:
        """
        Get the direction of an open position.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            'BUY', 'SELL', or None if no open position
        """
        trade = self.get_open_trade(symbol)
        return trade["action"] if trade else None
    
    def list_open_trades(self) -> List[Dict[str, Any]]:
        """
        Get a list of all open trades.
        
        Returns:
            List of open trade dictionaries
        """
        return list(self.open_trades.values())
    
    def get_trade_history(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get the trade history, optionally filtered by symbol.
        
        Args:
            symbol: Trading symbol to filter by (optional)
            
        Returns:
            List of trade dictionaries (includes both open and closed trades)
        """
        all_trades = list(self.open_trades.values()) + self.closed_trades
        
        if symbol:
            return [trade for trade in all_trades if trade["symbol"] == symbol]
        else:
            return all_trades
    
    def _append_trade_to_log(self, trade: Dict[str, Any]) -> None:
        """
        Append a trade to the trade log file.
        
        Args:
            trade: Trade information dictionary
        """
        try:
            with open(self.trade_log_path, 'a') as f:
                f.write(json.dumps(trade) + '\n')
        except Exception as e:
            logger.error(f"Failed to write trade to log: {e}")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current portfolio.
        
        Returns:
            Dictionary with portfolio summary information
        """
        return {
            "open_positions": len(self.open_trades),
            "total_trades": len(self.open_trades) + len(self.closed_trades),
            "symbols": list(self.open_trades.keys()),
        }
    
    def has_open_position(self, symbol: str) -> bool:
        """
        Check if there's an open position for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if an open position exists, False otherwise
        """
        return symbol in self.open_trades
    
    def should_hold(self, symbol: str, proposed_action: str) -> bool:
        """
        Determine if we should hold instead of executing a proposed trade.
        
        Args:
            symbol: Trading symbol
            proposed_action: Proposed trading action ('BUY' or 'SELL')
            
        Returns:
            True if we should hold, False if the trade is appropriate
        """
        # If no open position, never hold
        if not self.has_open_position(symbol):
            return False
        
        # Get current position direction
        current_direction = self.get_position_direction(symbol)
        
        # Hold if trying to open a position in the same direction
        return proposed_action == current_direction
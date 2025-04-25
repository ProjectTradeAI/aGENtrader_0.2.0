"""
Paper Trading System

This module provides paper trading capabilities for testing trading strategies
without using real funds.
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("paper_trading")

class PaperTradingAccount:
    """Paper trading account for simulating trades"""
    
    def __init__(self, account_id: str, initial_balance: float = 10000.0):
        """
        Initialize a paper trading account
        
        Args:
            account_id: Unique account identifier
            initial_balance: Initial account balance in USDT
        """
        self.account_id = account_id
        self.balance = initial_balance
        self.positions = {}  # symbol -> position details
        self.trades = []
        self.trade_id_counter = 1
        self.created_at = datetime.now().isoformat()
        self.last_updated = self.created_at
        
        logger.info(f"Initialized new account {account_id} with {initial_balance} USDT")
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Get account summary
        
        Returns:
            Account summary dictionary
        """
        # Calculate unrealized PnL and total equity
        positions_value = 0.0
        unrealized_pnl = 0.0
        
        for symbol, position in self.positions.items():
            positions_value += position.get('current_value', 0.0)
            unrealized_pnl += position.get('unrealized_pnl', 0.0)
        
        total_value = self.balance + positions_value
        
        return {
            "account_id": self.account_id,
            "balance": self.balance,
            "positions_value": positions_value,
            "unrealized_pnl": unrealized_pnl,
            "total_value": total_value,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "position_count": len(self.positions)
        }
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions
        
        Returns:
            List of position dictionaries
        """
        result = []
        for symbol, position in self.positions.items():
            position_copy = position.copy()
            position_copy['symbol'] = symbol
            result.append(position_copy)
        
        return result
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get position details for a symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position details or None if not found
        """
        return self.positions.get(symbol)
    
    def open_position(self, symbol: str, side: str, price: float, size: float, 
                      take_profit: Optional[float] = None, stop_loss: Optional[float] = None,
                      trailing_stop: Optional[float] = None) -> Dict[str, Any]:
        """
        Open a new trading position
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            price: Entry price
            size: Position size in base currency
            take_profit: Optional take profit price
            stop_loss: Optional stop loss price
            trailing_stop: Optional trailing stop percentage
            
        Returns:
            Trade details
        """
        # Standardize side to uppercase
        side = side.upper()
        if side not in ['BUY', 'SELL']:
            logger.error(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
            return {"error": "Invalid side"}
        
        # Check if we already have a position for this symbol
        if symbol in self.positions:
            logger.warning(f"Position already exists for {symbol}")
            return {"error": "Position already exists"}
        
        # Calculate cost
        cost = price * size
        
        # Check if we have enough balance
        if cost > self.balance:
            logger.warning(f"Insufficient balance for {symbol} position. Need {cost}, have {self.balance}")
            return {"error": "Insufficient balance"}
        
        # Deduct from balance
        self.balance -= cost
        
        # Record trade
        trade_id = f"{self.account_id}_{self.trade_id_counter}"
        self.trade_id_counter += 1
        
        timestamp = datetime.now().isoformat()
        trade = {
            "trade_id": trade_id,
            "symbol": symbol,
            "side": side,
            "entry_price": price,
            "size": size,
            "cost": cost,
            "status": "OPEN",
            "entry_time": timestamp
        }
        
        # Add trade to history
        self.trades.append(trade)
        
        # Create position object
        self.positions[symbol] = {
            "trade_id": trade_id,
            "entry_price": price,
            "current_price": price,
            "size": size,
            "side": side,
            "cost": cost,
            "current_value": cost,
            "unrealized_pnl": 0.0,
            "unrealized_pnl_pct": 0.0,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "trailing_stop": trailing_stop,
            "trailing_stop_price": None,
            "entry_time": timestamp,
            "last_updated": timestamp
        }
        
        # Update trailing stop price if needed
        if trailing_stop and trailing_stop > 0:
            if side == 'BUY':
                # For long positions, trailing stop is below current price
                self.positions[symbol]['trailing_stop_price'] = price * (1 - trailing_stop / 100)
            else:
                # For short positions, trailing stop is above current price
                self.positions[symbol]['trailing_stop_price'] = price * (1 + trailing_stop / 100)
        
        self.last_updated = timestamp
        logger.info(f"Opened {side} position for {symbol} at {price}: {size} units (${cost:.2f})")
        
        return {
            "status": "success",
            "message": f"Opened {side} position",
            "trade": trade,
            "position": self.positions[symbol]
        }
    
    def close_position(self, symbol: str, price: float, reason: str = "manual") -> Dict[str, Any]:
        """
        Close an existing position
        
        Args:
            symbol: Trading symbol
            price: Exit price
            reason: Reason for closing (e.g., 'manual', 'take_profit', 'stop_loss', 'trailing_stop')
            
        Returns:
            Trade details
        """
        if symbol not in self.positions:
            logger.warning(f"No position found for {symbol}")
            return {"error": "Position not found"}
        
        # Get position details
        position = self.positions[symbol]
        entry_price = position['entry_price']
        size = position['size']
        side = position['side']
        cost = position['cost']
        trade_id = position['trade_id']
        
        # Calculate profit/loss
        current_value = price * size
        if side == 'BUY':
            # For long positions, profit when exit price > entry price
            profit_loss = current_value - cost
        else:
            # For short positions, profit when exit price < entry price
            profit_loss = cost - current_value
        
        profit_loss_pct = (profit_loss / cost) * 100
        
        # Add funds back to balance
        self.balance += current_value
        
        # Find the original trade and update it
        for i, trade in enumerate(self.trades):
            if trade['trade_id'] == trade_id:
                self.trades[i]['exit_price'] = price
                self.trades[i]['exit_time'] = datetime.now().isoformat()
                self.trades[i]['profit_loss'] = profit_loss
                self.trades[i]['profit_loss_pct'] = profit_loss_pct
                self.trades[i]['close_reason'] = reason
                self.trades[i]['status'] = 'CLOSED'
                break
        
        # Remove position
        position_copy = self.positions.pop(symbol)
        
        self.last_updated = datetime.now().isoformat()
        logger.info(f"Closed {side} position for {symbol} at {price}: {profit_loss:.2f} USDT ({profit_loss_pct:.2f}%)")
        
        return {
            "status": "success",
            "message": f"Closed {side} position",
            "symbol": symbol,
            "entry_price": entry_price,
            "exit_price": price,
            "profit_loss": profit_loss,
            "profit_loss_pct": profit_loss_pct,
            "close_reason": reason
        }
    
    def update_position(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """
        Update position with current market price
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            Updated position details
        """
        if symbol not in self.positions:
            logger.debug(f"No position found for {symbol}")
            return {"error": "Position not found"}
        
        position = self.positions[symbol]
        entry_price = position['entry_price']
        size = position['size']
        side = position['side']
        cost = position['cost']
        
        # Calculate current value and PnL
        current_value = current_price * size
        
        if side == 'BUY':
            # For long positions, profit when current price > entry price
            unrealized_pnl = current_value - cost
            # Check if we need to update trailing stop
            if position.get('trailing_stop') and position.get('trailing_stop_price'):
                trailing_stop_pct = position['trailing_stop']
                trailing_stop_price = position['trailing_stop_price']
                
                # For longs, if price moves up, move the trailing stop up
                if current_price > entry_price:
                    new_stop_price = current_price * (1 - trailing_stop_pct / 100)
                    if new_stop_price > trailing_stop_price:
                        position['trailing_stop_price'] = new_stop_price
                        logger.info(f"Updated trailing stop for {symbol} to {new_stop_price:.2f}")
        else:
            # For short positions, profit when current price < entry price
            unrealized_pnl = cost - current_value
            # Check if we need to update trailing stop
            if position.get('trailing_stop') and position.get('trailing_stop_price'):
                trailing_stop_pct = position['trailing_stop']
                trailing_stop_price = position['trailing_stop_price']
                
                # For shorts, if price moves down, move the trailing stop down
                if current_price < entry_price:
                    new_stop_price = current_price * (1 + trailing_stop_pct / 100)
                    if new_stop_price < trailing_stop_price:
                        position['trailing_stop_price'] = new_stop_price
                        logger.info(f"Updated trailing stop for {symbol} to {new_stop_price:.2f}")
        
        unrealized_pnl_pct = (unrealized_pnl / cost) * 100
        
        # Update position
        position['current_price'] = current_price
        position['current_value'] = current_value
        position['unrealized_pnl'] = unrealized_pnl
        position['unrealized_pnl_pct'] = unrealized_pnl_pct
        position['last_updated'] = datetime.now().isoformat()
        
        # Check if take profit or stop loss hit
        result = {
            "symbol": symbol,
            "current_price": current_price,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "take_profit_hit": False,
            "stop_loss_hit": False,
            "trailing_stop_hit": False
        }
        
        # Check take profit
        if position.get('take_profit') and (
            (side == 'BUY' and current_price >= position['take_profit']) or
            (side == 'SELL' and current_price <= position['take_profit'])
        ):
            result['take_profit_hit'] = True
        
        # Check stop loss
        if position.get('stop_loss') and (
            (side == 'BUY' and current_price <= position['stop_loss']) or
            (side == 'SELL' and current_price >= position['stop_loss'])
        ):
            result['stop_loss_hit'] = True
        
        # Check trailing stop
        if position.get('trailing_stop_price') and (
            (side == 'BUY' and current_price <= position['trailing_stop_price']) or
            (side == 'SELL' and current_price >= position['trailing_stop_price'])
        ):
            result['trailing_stop_hit'] = True
        
        return result
    
    def handle_price_update(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """
        Handle a price update for a symbol, including checking for TP/SL triggers
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            Result of price update
        """
        if symbol not in self.positions:
            return {"status": "no_position"}
        
        # Update position with new price
        update_result = self.update_position(symbol, current_price)
        
        result = {
            "status": "updated",
            "symbol": symbol,
            "current_price": current_price,
            "position_closed": False,
            "close_reason": None
        }
        
        # Check if any exit conditions were hit
        if update_result.get('take_profit_hit'):
            close_result = self.close_position(symbol, current_price, "take_profit")
            result["status"] = "closed"
            result["position_closed"] = True
            result["close_reason"] = "take_profit"
            result["close_details"] = close_result
        
        elif update_result.get('stop_loss_hit'):
            close_result = self.close_position(symbol, current_price, "stop_loss")
            result["status"] = "closed"
            result["position_closed"] = True
            result["close_reason"] = "stop_loss"
            result["close_details"] = close_result
        
        elif update_result.get('trailing_stop_hit'):
            close_result = self.close_position(symbol, current_price, "trailing_stop")
            result["status"] = "closed"
            result["position_closed"] = True
            result["close_reason"] = "trailing_stop"
            result["close_details"] = close_result
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert account to dictionary for serialization
        
        Returns:
            Account as dictionary
        """
        return {
            "account_id": self.account_id,
            "balance": self.balance,
            "positions": self.positions,
            "trades": self.trades,
            "trade_id_counter": self.trade_id_counter,
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaperTradingAccount':
        """
        Create account from dictionary
        
        Args:
            data: Account data dictionary
            
        Returns:
            New account instance
        """
        account = cls(data['account_id'], 0.0)  # Create with zero balance, we'll set the real one
        account.balance = data['balance']
        account.positions = data['positions']
        account.trades = data['trades']
        account.trade_id_counter = data['trade_id_counter']
        account.created_at = data['created_at']
        account.last_updated = data['last_updated']
        return account


class PaperTradingSystem:
    """Paper trading system for simulating trades"""
    
    def __init__(self, data_dir: str = "data/paper_trading", 
                 default_account_id: str = "default",
                 initial_balance: float = 10000.0):
        """
        Initialize the paper trading system
        
        Args:
            data_dir: Directory for storing account data
            default_account_id: Default account ID
            initial_balance: Initial balance for new accounts
        """
        self.data_dir = data_dir
        self.default_account_id = default_account_id
        self.initial_balance = initial_balance
        self.accounts = {}
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Try to load the default account if it exists
        self._load_account(default_account_id)
    
    def _get_account_path(self, account_id: str) -> str:
        """
        Get file path for account data
        
        Args:
            account_id: Account ID
            
        Returns:
            File path
        """
        return os.path.join(self.data_dir, f"{account_id}.json")
    
    def _load_account(self, account_id: str) -> bool:
        """
        Load account from file
        
        Args:
            account_id: Account ID
            
        Returns:
            True if loaded successfully, False otherwise
        """
        file_path = self._get_account_path(account_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.accounts[account_id] = PaperTradingAccount.from_dict(data)
                logger.info(f"Loaded account {account_id} from {file_path}")
                return True
            except Exception as e:
                logger.error(f"Error loading account {account_id}: {str(e)}")
        
        return False
    
    def _save_account(self, account_id: str) -> bool:
        """
        Save account to file
        
        Args:
            account_id: Account ID
            
        Returns:
            True if saved successfully, False otherwise
        """
        if account_id not in self.accounts:
            logger.error(f"Account {account_id} not found")
            return False
        
        file_path = self._get_account_path(account_id)
        try:
            with open(file_path, 'w') as f:
                json.dump(self.accounts[account_id].to_dict(), f, indent=2)
            logger.debug(f"Saved account {account_id} to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving account {account_id}: {str(e)}")
            return False
    
    def get_account(self, account_id: Optional[str] = None) -> PaperTradingAccount:
        """
        Get account by ID, creating if it doesn't exist
        
        Args:
            account_id: Account ID (default: default_account_id)
            
        Returns:
            Paper trading account
        """
        if not account_id:
            account_id = self.default_account_id
        
        if account_id not in self.accounts:
            # Try to load from file
            if not self._load_account(account_id):
                # Create new account
                self.accounts[account_id] = PaperTradingAccount(account_id, self.initial_balance)
                # Save to file
                self._save_account(account_id)
        
        return self.accounts[account_id]
    
    def execute_order(self, account_id: Optional[str], symbol: str, side: str, price: float, 
                      size: float, take_profit: Optional[float] = None, 
                      stop_loss: Optional[float] = None, trailing_stop: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute a trading order
        
        Args:
            account_id: Account ID (default: default_account_id)
            symbol: Trading symbol
            side: 'buy' or 'sell'
            price: Entry price
            size: Position size in base currency
            take_profit: Optional take profit price
            stop_loss: Optional stop loss price
            trailing_stop: Optional trailing stop percentage
            
        Returns:
            Result of order execution
        """
        account = self.get_account(account_id)
        
        if side.upper() == 'CLOSE':
            result = account.close_position(symbol, price, "manual")
        else:
            result = account.open_position(
                symbol=symbol,
                side=side,
                price=price,
                size=size,
                take_profit=take_profit,
                stop_loss=stop_loss,
                trailing_stop=trailing_stop
            )
        
        # Save account after order execution
        self._save_account(account.account_id)
        
        return result
    
    def execute_from_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an order based on a trading decision
        
        Args:
            decision: Trading decision dictionary (must include 'action', 'symbol', 'current_price')
            
        Returns:
            Result of order execution
        """
        # Extract values from decision
        action = decision.get('action', 'HOLD').upper()
        symbol = decision.get('symbol')
        current_price = decision.get('current_price')
        
        if not symbol or not current_price:
            return {
                "status": "error",
                "message": "Missing required fields in decision (symbol or current_price)"
            }
        
        # Get account
        account = self.get_account()
        
        # Check if we already have a position for this symbol
        has_position = symbol in account.positions
        
        result = {
            "status": "no_action",
            "message": f"HOLD decision for {symbol} at {current_price}",
            "action": action
        }
        
        if action == 'BUY' and not has_position:
            # Calculate position size (25% of account by default unless specified)
            trade_size_pct = decision.get('trade_size_pct', 25.0)
            position_value = account.balance * (trade_size_pct / 100.0)
            size = position_value / current_price
            
            # Extract risk parameters
            take_profit_pct = decision.get('take_profit_pct', 5.0)
            stop_loss_pct = decision.get('stop_loss_pct', 3.0)
            trailing_stop_pct = decision.get('trailing_stop_pct')
            
            # Calculate take profit and stop loss prices
            take_profit = current_price * (1 + take_profit_pct / 100)
            stop_loss = current_price * (1 - stop_loss_pct / 100)
            
            # Execute the order
            result = self.execute_order(
                account_id=account.account_id,
                symbol=symbol,
                side='BUY',
                price=current_price,
                size=size,
                take_profit=take_profit,
                stop_loss=stop_loss,
                trailing_stop=trailing_stop_pct
            )
            
            logger.info(f"Executed BUY order for {symbol} at {current_price}: {size} units")
        
        elif action == 'SELL' and has_position:
            # Close the position
            result = self.execute_order(
                account_id=account.account_id,
                symbol=symbol,
                side='CLOSE',
                price=current_price,
                size=0  # Not used for close
            )
            
            logger.info(f"Executed SELL (close) order for {symbol} at {current_price}")
        
        elif action == 'SELL' and not has_position:
            # We currently only support long positions in this simplified version
            result = {
                "status": "error",
                "message": "Short selling not supported in simplified backtest"
            }
        
        elif action == 'BUY' and has_position:
            result = {
                "status": "error",
                "message": f"Position already exists for {symbol}"
            }
        
        # Save account after execution
        self._save_account(account.account_id)
        
        return result
    
    def update_prices(self, price_updates: Dict[str, float]) -> Dict[str, Any]:
        """
        Update prices for all symbols in the updates dictionary
        
        Args:
            price_updates: Dictionary mapping symbols to prices
            
        Returns:
            Results of the price updates
        """
        account = self.get_account()
        results = {}
        
        for symbol, price in price_updates.items():
            results[symbol] = account.handle_price_update(symbol, price)
        
        # Save account after updates
        self._save_account(account.account_id)
        
        return results
        
    def get_portfolio(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the current portfolio details for an account
        
        Args:
            account_id: Account ID (default: default_account_id)
            
        Returns:
            Portfolio details
        """
        account = self.get_account(account_id)
        account_summary = account.get_account_summary()
        
        return {
            "account_id": account.account_id,
            "cash_balance": account.balance,
            "total_equity": account_summary["total_value"],
            "unrealized_pnl": account_summary["unrealized_pnl"],
            "positions": account.get_all_positions()
        }
    
    def get_trade_history(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get the trade history for an account
        
        Args:
            account_id: Account ID (default: default_account_id)
            
        Returns:
            List of trade details
        """
        account = self.get_account(account_id)
        return account.trades
    
    def get_performance_metrics(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate performance metrics for an account
        
        Args:
            account_id: Account ID (default: default_account_id)
            
        Returns:
            Performance metrics
        """
        account = self.get_account(account_id)
        
        trades = account.trades
        closed_trades = [t for t in trades if t.get("status") == "CLOSED"]
        
        # Basic metrics
        metrics = {
            "total_trades": len(trades),
            "closed_trades": len(closed_trades),
            "open_trades": len(trades) - len(closed_trades),
        }
        
        # Calculate P&L metrics
        if closed_trades:
            profitable_trades = [t for t in closed_trades if t.get("profit_loss", 0) > 0]
            
            metrics.update({
                "profitable_trades": len(profitable_trades),
                "losing_trades": len(closed_trades) - len(profitable_trades),
                "win_rate": len(profitable_trades) / len(closed_trades) if closed_trades else 0.0,
                "total_profit": sum(t.get("profit_loss", 0) for t in profitable_trades),
                "total_loss": sum(t.get("profit_loss", 0) for t in closed_trades if t.get("profit_loss", 0) <= 0),
                "total_pnl": sum(t.get("profit_loss", 0) for t in closed_trades),
                "avg_profit_per_trade": sum(t.get("profit_loss", 0) for t in profitable_trades) / len(profitable_trades) if profitable_trades else 0,
                "avg_loss_per_trade": sum(t.get("profit_loss", 0) for t in closed_trades if t.get("profit_loss", 0) <= 0) / (len(closed_trades) - len(profitable_trades)) if (len(closed_trades) - len(profitable_trades)) > 0 else 0,
            })
            
            # Calculate profit factor
            if metrics["total_loss"] != 0:
                metrics["profit_factor"] = abs(metrics["total_profit"] / metrics["total_loss"]) if metrics["total_loss"] else float('inf')
            else:
                metrics["profit_factor"] = float('inf') if metrics["total_profit"] > 0 else 0.0
        
        return metrics
"""
Portfolio Manager Agent Module

This agent tracks portfolio allocations, open positions, and controls exposure risk
for the aGENtrader v2 system. It validates trades against risk limits and provides
portfolio state information.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
import threading
from collections import defaultdict

# Add parent directory to path to allow importing from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import the base agent class
from agents.base_agent import BaseAnalystAgent

# Configure logger
logger = logging.getLogger(__name__)

class TradeValidationStatus(Enum):
    """Enum for trade validation status"""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PortfolioManagerAgent(BaseAnalystAgent):
    """
    Portfolio Manager Agent for tracking portfolio allocation and risk.
    
    This agent:
    - Tracks simulated portfolio holdings (balances per asset/pair)
    - Maintains a record of open trades
    - Enforces position limits and exposure rules
    - Logs portfolio state periodically
    """
    
    def __init__(self):
        """Initialize the Portfolio Manager Agent."""
        super().__init__(agent_name="portfolio_manager")
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Get portfolio manager specific configuration
        self.portfolio_config = self.get_agent_config()
        
        # Get trading configuration
        self.trading_config = self.get_trading_config()
        
        # Initialize portfolio state
        self.base_currency = self.portfolio_config.get("base_currency", "USDT")
        self.starting_balance = self.trading_config.get("starting_balance", 10000)
        self.current_balance = self.starting_balance
        self.initial_portfolio_value = self.starting_balance
        
        # Risk limits
        self.max_total_exposure_pct = self.portfolio_config.get("max_total_exposure_pct", 85)
        self.max_per_asset_exposure_pct = self.portfolio_config.get("max_per_asset_exposure_pct", 35)
        self.max_open_trades = self.portfolio_config.get("max_open_trades", 10)
        
        # Initialize portfolio holdings
        self.holdings = {
            self.base_currency: self.current_balance
        }
        
        # Track open positions
        self.open_positions = {}  # trade_id -> position_data
        
        # Track historical allocations for analysis
        self.allocation_history = []
        
        # Initialize snapshot timer if configured
        self.snapshot_interval_minutes = self.portfolio_config.get("snapshot_interval_minutes", 60)
        self.snapshot_thread = None
        self.snapshot_active = False
        
        # Initialize directory for portfolio snapshots
        self.logs_dir = os.path.join(parent_dir, "logs")
        self.portfolio_dir = os.path.join(self.logs_dir, "portfolio")
        os.makedirs(self.portfolio_dir, exist_ok=True)
        
        # File paths
        self.trade_log_file = os.path.join(parent_dir, "trades", "trade_log.jsonl")
        self.snapshot_file = os.path.join(self.portfolio_dir, "portfolio_snapshot.jsonl")
        
        # Create trades directory if it doesn't exist
        os.makedirs(os.path.dirname(self.trade_log_file), exist_ok=True)
        
        # Load existing trades to initialize the portfolio state
        self._load_existing_trades()
        
        # Start the portfolio snapshot thread if enabled
        if self.snapshot_interval_minutes > 0:
            self._start_snapshot_thread()
        
        self.logger.info(f"Portfolio Manager Agent initialized with base currency {self.base_currency}")
        self.logger.info(f"Max exposure limits: {self.max_total_exposure_pct}% total, {self.max_per_asset_exposure_pct}% per asset")
        self.logger.info(f"Max open trades: {self.max_open_trades}")
    
    def _load_existing_trades(self) -> None:
        """
        Load existing trades from the trade log and initialize portfolio state.
        If the file doesn't exist, create it as an empty JSONL file.
        """
        self.logger.info("Loading existing trades to initialize portfolio state")
        
        if not os.path.exists(self.trade_log_file):
            self.logger.warning(f"Trade log file not found at {self.trade_log_file}")
            try:
                # Create the trades directory if it doesn't exist (double-check)
                os.makedirs(os.path.dirname(self.trade_log_file), exist_ok=True)
                
                # Create an empty trade log file
                with open(self.trade_log_file, 'w') as f:
                    f.write("")  # Create an empty file for JSONL format
                
                self.logger.info(f"Created empty trade log file at {self.trade_log_file}")
                return
            except Exception as e:
                self.logger.error(f"Failed to create trade log file: {str(e)}")
                return
        
        try:
            trades = []
            with open(self.trade_log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        trade = json.loads(line.strip())
                        trades.append(trade)
            
            # Process trades chronologically
            trades.sort(key=lambda x: x.get('timestamp', ''))
            
            for trade in trades:
                if trade.get('status') == 'open':
                    self._add_open_position(trade)
                elif trade.get('status') == 'closed':
                    self._process_closed_trade(trade)
            
            self.logger.info(f"Loaded {len(trades)} trades from trade log")
            self.logger.info(f"Current portfolio state: {len(self.open_positions)} open positions")
            self.logger.info(f"Current balance: {self.current_balance} {self.base_currency}")
        
        except Exception as e:
            self.logger.error(f"Error loading trades: {e}")
    
    def _add_open_position(self, trade: Dict[str, Any]) -> None:
        """
        Add an open position to the portfolio.
        
        Args:
            trade: Trade data dictionary
        """
        trade_id = trade.get('trade_id')
        pair = trade.get('pair')
        action = trade.get('action')
        
        if not trade_id or not pair or not action:
            self.logger.warning(f"Invalid trade data, skipping: {trade}")
            return
        
        # Skip HOLD actions
        if action == "HOLD":
            return
        
        # Extract base and quote from the pair
        if '/' in pair:
            base, quote = pair.split('/')
        else:
            # Handle pairs without separator like BTCUSDT
            if self.base_currency in pair:
                # Assume format is "BASEUSDT"
                base = pair.replace(self.base_currency, '')
                quote = self.base_currency
            else:
                self.logger.warning(f"Could not parse pair: {pair}")
                base = pair
                quote = self.base_currency
        
        # Calculate position size
        entry_price = trade.get('entry_price', 0)
        position_size = trade.get('position_size', 0)
        position_value = position_size * entry_price
        
        # Update holdings
        if action == "BUY":
            # Subtract quote currency (e.g., USDT)
            self.holdings[quote] = self.holdings.get(quote, 0) - position_value
            # Add base currency (e.g., BTC)
            self.holdings[base] = self.holdings.get(base, 0) + position_size
        
        elif action == "SELL":
            # Add quote currency (e.g., USDT)
            self.holdings[quote] = self.holdings.get(quote, 0) + position_value
            # Subtract base currency (e.g., BTC)
            self.holdings[base] = self.holdings.get(base, 0) - position_size
        
        # Add to open positions
        self.open_positions[trade_id] = {
            'trade_id': trade_id,
            'pair': pair,
            'base': base,
            'quote': quote,
            'action': action,
            'entry_price': entry_price,
            'position_size': position_size,
            'position_value': position_value,
            'timestamp': trade.get('timestamp'),
            'unrealized_pnl': 0.0,
            'unrealized_pnl_pct': 0.0
        }
        
        self.logger.info(f"Added open position: {action} {position_size} {base} at {entry_price} {quote}")
    
    def _process_closed_trade(self, trade: Dict[str, Any]) -> None:
        """
        Process a closed trade and update portfolio state.
        
        Args:
            trade: Trade data dictionary
        """
        trade_id = trade.get('trade_id')
        pair = trade.get('pair')
        action = trade.get('action')
        
        if not trade_id or not pair or not action:
            self.logger.warning(f"Invalid trade data, skipping: {trade}")
            return
        
        # Skip HOLD actions
        if action == "HOLD":
            return
        
        # Extract base and quote from the pair
        if '/' in pair:
            base, quote = pair.split('/')
        else:
            # Handle pairs without separator like BTCUSDT
            if self.base_currency in pair:
                # Assume format is "BASEUSDT"
                base = pair.replace(self.base_currency, '')
                quote = self.base_currency
            else:
                self.logger.warning(f"Could not parse pair: {pair}")
                base = pair
                quote = self.base_currency
        
        # Calculate position size and PnL
        entry_price = trade.get('entry_price', 0)
        exit_price = trade.get('exit_price', 0)
        position_size = trade.get('position_size', 0)
        
        # If this was previously an open position, remove it
        if trade_id in self.open_positions:
            self.open_positions.pop(trade_id)
        
        # Update balance based on PnL
        pnl_percentage = trade.get('pnl_percentage', 0)
        position_value = position_size * entry_price
        pnl_value = position_value * (pnl_percentage / 100)
        
        # Update current balance
        self.current_balance += pnl_value
        
        # Update holdings based on closing the position
        if action == "BUY":
            # Close a long position
            self.holdings[base] = self.holdings.get(base, 0) - position_size
            self.holdings[quote] = self.holdings.get(quote, 0) + (position_size * exit_price)
        
        elif action == "SELL":
            # Close a short position
            self.holdings[base] = self.holdings.get(base, 0) + position_size
            self.holdings[quote] = self.holdings.get(quote, 0) - (position_size * exit_price)
        
        self.logger.debug(f"Processed closed trade: {trade_id}, PnL: {pnl_percentage}%, Value: {pnl_value} {quote}")
    
    def validate_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a trade against portfolio limits.
        
        Args:
            trade: Trade data dictionary
            
        Returns:
            Dictionary with validation status and reason
        """
        if not trade:
            return {
                "status": TradeValidationStatus.REJECTED.value,
                "reason": "Invalid trade data"
            }
        
        # Skip validation for HOLD actions
        if trade.get('action') == "HOLD":
            return {
                "status": TradeValidationStatus.APPROVED.value,
                "reason": "HOLD action does not affect portfolio"
            }
        
        # Check max open trades limit
        if len(self.open_positions) >= self.max_open_trades:
            return {
                "status": TradeValidationStatus.REJECTED.value,
                "reason": f"Maximum open trades limit ({self.max_open_trades}) reached"
            }
        
        pair = trade.get('pair', '')
        # Extract base currency from pair
        if '/' in pair:
            base = pair.split('/')[0]
        else:
            # Handle pairs without separator like BTCUSDT
            base = pair.replace(self.base_currency, '')
        
        # Calculate current exposure
        portfolio_value = self.get_portfolio_value()
        total_exposure = self.get_total_exposure_pct()
        asset_exposure = self.get_asset_exposure_pct(base)
        
        # Calculate new position size
        position_value = trade.get('position_value', 0)
        if not position_value:
            entry_price = trade.get('entry_price', 0)
            position_size = trade.get('position_size', 0)
            position_value = entry_price * position_size
        
        # Calculate new exposure percentages
        new_position_pct = (position_value / portfolio_value) * 100
        new_total_exposure = total_exposure + new_position_pct
        new_asset_exposure = asset_exposure + new_position_pct
        
        # Check total exposure limit
        if new_total_exposure > self.max_total_exposure_pct:
            return {
                "status": TradeValidationStatus.REJECTED.value,
                "reason": f"Total exposure limit exceeded: {new_total_exposure:.2f}% > {self.max_total_exposure_pct}%"
            }
        
        # Check per-asset exposure limit
        if new_asset_exposure > self.max_per_asset_exposure_pct:
            return {
                "status": TradeValidationStatus.REJECTED.value,
                "reason": f"Per-asset exposure limit exceeded for {base}: {new_asset_exposure:.2f}% > {self.max_per_asset_exposure_pct}%"
            }
        
        # All checks passed
        return {
            "status": TradeValidationStatus.APPROVED.value,
            "reason": "Trade meets all portfolio requirements",
            "exposure_info": {
                "new_position_pct": new_position_pct,
                "new_total_exposure": new_total_exposure,
                "new_asset_exposure": new_asset_exposure
            }
        }
    
    def get_portfolio_value(self) -> float:
        """
        Calculate the total portfolio value in base currency.
        
        Returns:
            Portfolio value in base currency
        """
        # Start with base currency balance
        total_value = self.holdings.get(self.base_currency, 0)
        
        # Add value of open positions
        for position in self.open_positions.values():
            total_value += position.get('position_value', 0)
        
        return total_value
    
    def get_total_exposure_pct(self) -> float:
        """
        Calculate the total portfolio exposure as a percentage.
        
        Returns:
            Total exposure percentage
        """
        portfolio_value = self.get_portfolio_value()
        
        if portfolio_value <= 0:
            return 0.0
        
        # Sum the value of all open positions
        total_position_value = sum(position.get('position_value', 0) for position in self.open_positions.values())
        
        # Calculate percentage
        exposure_pct = (total_position_value / portfolio_value) * 100
        
        return exposure_pct
    
    def get_asset_exposure_pct(self, asset: str) -> float:
        """
        Calculate the exposure to a specific asset as a percentage.
        
        Args:
            asset: Asset symbol (e.g., 'BTC')
            
        Returns:
            Asset exposure percentage
        """
        portfolio_value = self.get_portfolio_value()
        
        if portfolio_value <= 0:
            return 0.0
        
        # Sum the value of positions in this asset
        asset_position_value = sum(
            position.get('position_value', 0) 
            for position in self.open_positions.values() 
            if position.get('base') == asset
        )
        
        # Calculate percentage
        exposure_pct = (asset_position_value / portfolio_value) * 100
        
        return exposure_pct
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the current portfolio state.
        
        Returns:
            Dictionary with portfolio summary data
        """
        portfolio_value = self.get_portfolio_value()
        total_exposure = self.get_total_exposure_pct()
        
        # Calculate asset allocations
        asset_allocations = {}
        for asset, amount in self.holdings.items():
            if asset == self.base_currency:
                allocation_pct = (amount / portfolio_value) * 100
                asset_allocations[asset] = {
                    "amount": amount,
                    "allocation_pct": allocation_pct
                }
        
        # Add allocations for open positions
        for position in self.open_positions.values():
            base = position.get('base')
            if base not in asset_allocations:
                asset_allocations[base] = {
                    "amount": position.get('position_size', 0),
                    "allocation_pct": 0
                }
            
            position_value = position.get('position_value', 0)
            allocation_pct = (position_value / portfolio_value) * 100
            asset_allocations[base]["allocation_pct"] += allocation_pct
        
        # Calculate performance metrics
        initial_value = self.initial_portfolio_value
        pnl_value = portfolio_value - initial_value
        pnl_percentage = (pnl_value / initial_value) * 100 if initial_value > 0 else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "portfolio_value": portfolio_value,
            "base_currency": self.base_currency,
            "total_exposure_pct": total_exposure,
            "open_positions_count": len(self.open_positions),
            "asset_allocations": asset_allocations,
            "pnl": {
                "value": pnl_value,
                "percentage": pnl_percentage
            },
            "risk_limits": {
                "max_total_exposure_pct": self.max_total_exposure_pct,
                "max_per_asset_exposure_pct": self.max_per_asset_exposure_pct,
                "max_open_trades": self.max_open_trades
            }
        }
    
    def check_stop_loss_take_profit(self, data_provider=None) -> List[Dict[str, Any]]:
        """
        Check all open positions for stop-loss or take-profit hits.
        
        Args:
            data_provider: Optional data provider to use for getting current prices
            
        Returns:
            List of trades that were closed due to SL/TP hits
        """
        self.logger.info("Checking open positions for SL/TP hits")
        
        # Update position prices first
        self.update_position_prices(data_provider)
        
        # Track closed trades
        closed_trades = []
        positions_to_close = []
        
        # Check each position
        for trade_id, position in self.open_positions.items():
            current_price = position.get('current_price', 0)
            if not current_price:
                self.logger.warning(f"Position {trade_id} has no current price, skipping SL/TP check")
                continue
                
            # Get SL/TP levels (if they exist)
            stop_loss = position.get('stop_loss')
            take_profit = position.get('take_profit')
            action = position.get('action')
            
            if not stop_loss or not take_profit:
                # No SL/TP levels defined for this position
                continue
                
            # Check for SL/TP hits
            sl_hit = False
            tp_hit = False
            
            if action == "BUY":  # Long position
                if current_price <= stop_loss:
                    sl_hit = True
                    exit_reason = "STOP_LOSS"
                elif current_price >= take_profit:
                    tp_hit = True
                    exit_reason = "TAKE_PROFIT"
            elif action == "SELL":  # Short position
                if current_price >= stop_loss:
                    sl_hit = True
                    exit_reason = "STOP_LOSS"
                elif current_price <= take_profit:
                    tp_hit = True
                    exit_reason = "TAKE_PROFIT"
                    
            # Process trade if SL or TP hit
            if sl_hit or tp_hit:
                positions_to_close.append((trade_id, exit_reason, current_price))
        
        # Close positions that hit SL/TP (in a separate loop to avoid modifying during iteration)
        for trade_id, exit_reason, exit_price in positions_to_close:
            position = self.open_positions.get(trade_id)
            if not position:
                continue
                
            # Create a copy of the position for closing
            closed_trade = position.copy()
            closed_trade['status'] = 'closed'
            closed_trade['exit_price'] = exit_price
            closed_trade['exit_time'] = datetime.now().isoformat()
            closed_trade['exit_reason'] = exit_reason
            
            # Calculate PnL
            entry_price = closed_trade.get('entry_price', 0)
            action = closed_trade.get('action')
            
            if action == "BUY":  # Long position
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            elif action == "SELL":  # Short position
                pnl_pct = ((entry_price - exit_price) / entry_price) * 100
            else:
                pnl_pct = 0
                
            closed_trade['pnl_percentage'] = pnl_pct
            
            # Process the closed trade
            self._process_closed_trade(closed_trade)
            
            # Record the trade
            self.logger.info(f"🔔 Trade {trade_id} closed due to {exit_reason} at {exit_price} ({pnl_pct:.2f}%)")
            closed_trades.append(closed_trade)
            
        return closed_trades
        
    def update_position_prices(self, data_provider=None) -> None:
        """
        Update the prices of all open positions and calculate unrealized PnL.
        
        Args:
            data_provider: Optional data provider to use for getting current prices
        """
        self.logger.debug("Updating position prices")
        
        # Create a price map using the data provider if available
        price_map = {}
        if data_provider:
            for pair in set([pos.get('pair') for pos in self.open_positions.values()]):
                try:
                    # Handle both formats (BTC/USDT and BTCUSDT)
                    symbol = pair.replace('/', '') if '/' in pair else pair
                    price_map[pair] = data_provider.get_current_price(symbol)
                except Exception as e:
                    self.logger.warning(f"Could not get current price for {pair}: {e}")
        
        # Fallback to default prices if needed
        default_prices = {
            "BTC/USDT": 50000.0,
            "ETH/USDT": 3000.0,
            "BNB/USDT": 500.0,
            "SOL/USDT": 150.0,
            "DOGE/USDT": 0.1,
            "XRP/USDT": 0.5
        }
        
        for trade_id, position in self.open_positions.items():
            pair = position.get('pair')
            entry_price = position.get('entry_price', 0)
            
            try:
                # Get current price (using simple fallback for now)
                # In a real implementation, this would call market_fetcher.get_ticker(pair)
                current_price = default_prices.get(pair, entry_price * 1.01)  # Default 1% up
                
                if current_price:
                    action = position.get('action')
                    
                    # Calculate unrealized PnL
                    if action == "BUY":
                        # Long position
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    elif action == "SELL":
                        # Short position
                        pnl_pct = ((entry_price - current_price) / entry_price) * 100
                    else:
                        pnl_pct = 0
                    
                    position_value = position.get('position_value', 0)
                    unrealized_pnl = position_value * (pnl_pct / 100)
                    
                    # Update position data
                    position['current_price'] = current_price
                    position['unrealized_pnl'] = unrealized_pnl
                    position['unrealized_pnl_pct'] = pnl_pct
                    
                    self.logger.debug(f"Updated position {trade_id}: Current price: {current_price}, Unrealized PnL: {pnl_pct:.2f}%")
            
            except Exception as e:
                self.logger.error(f"Error updating price for {pair}: {e}")
    
    def _start_snapshot_thread(self) -> None:
        """
        Start a thread to periodically take portfolio snapshots.
        """
        self.snapshot_active = True
        self.snapshot_thread = threading.Thread(target=self._snapshot_thread_func)
        self.snapshot_thread.daemon = True
        self.snapshot_thread.start()
        self.logger.info(f"Portfolio snapshot thread started with interval {self.snapshot_interval_minutes} minutes")
    
    def _snapshot_thread_func(self) -> None:
        """
        Thread function for taking periodic portfolio snapshots.
        """
        while self.snapshot_active:
            try:
                # Take a snapshot
                self.take_portfolio_snapshot()
                
                # Sleep for the configured interval
                time.sleep(self.snapshot_interval_minutes * 60)
            
            except Exception as e:
                self.logger.error(f"Error in portfolio snapshot thread: {e}")
                time.sleep(60)  # Sleep for 1 minute on error
    
    def take_portfolio_snapshot(self) -> Dict[str, Any]:
        """
        Take a snapshot of the current portfolio state and save it to file.
        
        Returns:
            Portfolio snapshot data
        """
        try:
            # Update position prices
            self.update_position_prices()
            
            # Get portfolio summary
            snapshot = self.get_portfolio_summary()
            
            # Add open positions details
            snapshot['open_positions'] = list(self.open_positions.values())
            
            # Add timestamp if not present
            if 'timestamp' not in snapshot:
                snapshot['timestamp'] = datetime.now().isoformat()
            
            # Save to file
            with open(self.snapshot_file, 'a') as f:
                f.write(json.dumps(snapshot) + "\n")
            
            self.logger.info(f"Portfolio snapshot taken: {len(self.open_positions)} open positions, {snapshot['portfolio_value']:.2f} {self.base_currency}")
            
            # Add to history
            self.allocation_history.append(snapshot)
            
            return snapshot
        
        except Exception as e:
            self.logger.error(f"Error taking portfolio snapshot: {e}")
            return {}
    
    def analyze(self,
               symbol: Optional[str] = None,
               interval: Optional[str] = None,
               **kwargs) -> Dict[str, Any]:
        """
        Perform portfolio analysis.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1h', '15m')
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with portfolio analysis results
        """
        # Update position prices
        self.update_position_prices()
        
        # Get the portfolio summary
        portfolio_summary = self.get_portfolio_summary()
        
        # Identify overexposed assets
        overexposed_assets = []
        for asset, allocation in portfolio_summary.get('asset_allocations', {}).items():
            if asset != self.base_currency:
                allocation_pct = allocation.get('allocation_pct', 0)
                if allocation_pct > self.max_per_asset_exposure_pct:
                    overexposed_assets.append({
                        "asset": asset,
                        "exposure_pct": allocation_pct,
                        "limit_pct": self.max_per_asset_exposure_pct
                    })
        
        # Check total exposure
        total_exposure = portfolio_summary.get('total_exposure_pct', 0)
        total_exposure_status = "NORMAL"
        if total_exposure > self.max_total_exposure_pct:
            total_exposure_status = "EXCEEDED"
        elif total_exposure > (self.max_total_exposure_pct * 0.8):
            total_exposure_status = "WARNING"
        
        # Calculate available capital
        available_pct = 100 - total_exposure
        available_capital = portfolio_summary.get('portfolio_value', 0) * (available_pct / 100)
        
        # Prepare the analysis result
        analysis_result = {
            "symbol": symbol if symbol else "PORTFOLIO",
            "interval": interval if interval else "N/A",
            "timestamp": datetime.now().isoformat(),
            "portfolio_summary": portfolio_summary,
            "risk_analysis": {
                "total_exposure": {
                    "value_pct": total_exposure,
                    "limit_pct": self.max_total_exposure_pct,
                    "status": total_exposure_status
                },
                "overexposed_assets": overexposed_assets,
                "open_positions_count": len(self.open_positions),
                "max_positions_limit": self.max_open_trades
            },
            "available_capital": {
                "value": available_capital,
                "percentage": available_pct
            },
            "recommendation": {
                "action": "NORMAL",
                "confidence": 100,
                "reason": "Portfolio is within risk limits"
            }
        }
        
        # Generate a recommendation based on the analysis
        if total_exposure_status == "EXCEEDED" or overexposed_assets:
            analysis_result["recommendation"] = {
                "action": "REDUCE_EXPOSURE",
                "confidence": 90,
                "reason": "Portfolio exposure limits exceeded"
            }
        elif total_exposure_status == "WARNING":
            analysis_result["recommendation"] = {
                "action": "CAUTION",
                "confidence": 70,
                "reason": "Portfolio approaching exposure limits"
            }
        elif len(self.open_positions) >= self.max_open_trades:
            analysis_result["recommendation"] = {
                "action": "HOLD_NEW_POSITIONS",
                "confidence": 80,
                "reason": "Maximum number of open positions reached"
            }
        
        return analysis_result
    
    def record_trade_plan(self, trade_plan: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a trade plan generated by TradePlanAgent and update portfolio state.
        
        Args:
            trade_plan: Trade plan dictionary from TradePlanAgent
            market_data: Market data dictionary
            
        Returns:
            Dictionary with processing result
        """
        try:
            # Skip HOLD signals or invalid trade plans
            if not trade_plan or trade_plan.get('signal') == 'HOLD' or not trade_plan.get('entry_price'):
                self.logger.info("Trade plan is HOLD or invalid, skipping portfolio update")
                return {
                    "status": TradeValidationStatus.APPROVED.value,
                    "reason": "No action required for HOLD signal",
                    "portfolio_update": "No change"
                }
                
            # Create trade record from trade plan
            trade = {
                'trade_id': trade_plan.get('trade_id', f"TP-{int(time.time())}"),
                'pair': trade_plan.get('symbol', market_data.get('symbol')),
                'action': trade_plan.get('signal'),
                'entry_price': trade_plan.get('entry_price'),
                'position_size': trade_plan.get('position_size'),
                'position_value': trade_plan.get('position_size') * trade_plan.get('entry_price'),
                'stop_loss': trade_plan.get('stop_loss'),
                'take_profit': trade_plan.get('take_profit'),
                'timestamp': datetime.now().isoformat(),
                'status': 'open',
                'tags': trade_plan.get('tags', []),
                'confidence': trade_plan.get('confidence', 0),
                'risk_reward_ratio': trade_plan.get('risk_reward_ratio', 0)
            }
            
            # Process the trade
            return self.process_trade(trade)
            
        except Exception as e:
            self.logger.error(f"Error recording trade plan: {e}")
            return {
                "status": TradeValidationStatus.REJECTED.value,
                "reason": f"Error recording trade plan: {str(e)}"
            }
    
    def save_portfolio_state(self, file_path: Optional[str] = None) -> bool:
        """
        Save the current portfolio state to a file.
        
        Args:
            file_path: Path to save the file (defaults to logs/portfolio_state.json)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if file_path is None:
                file_path = os.path.join(self.portfolio_dir, "portfolio_state.json")
                
            # Update position prices
            self.update_position_prices()
            
            # Take a snapshot
            snapshot = self.take_portfolio_snapshot()
            
            # Add additional metadata
            state_data = {
                "portfolio": snapshot,
                "version": "0.2.0",
                "timestamp": datetime.now().isoformat()
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(state_data, f, indent=2)
                
            self.logger.info(f"Portfolio state saved to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving portfolio state: {e}")
            return False
            
    def load_portfolio_state(self, file_path: Optional[str] = None) -> bool:
        """
        Load portfolio state from a file.
        
        Args:
            file_path: Path to load the file from (defaults to logs/portfolio_state.json)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if file_path is None:
                file_path = os.path.join(self.portfolio_dir, "portfolio_state.json")
                
            if not os.path.exists(file_path):
                self.logger.warning(f"Portfolio state file {file_path} does not exist")
                return False
                
            # Load from file
            with open(file_path, 'r') as f:
                state_data = json.load(f)
                
            # Restore portfolio data
            portfolio_data = state_data.get('portfolio', {})
            
            # Restore positions
            if 'open_positions' in portfolio_data:
                for position in portfolio_data['open_positions']:
                    # Ensure it has the appropriate keys
                    if 'trade_id' in position:
                        self.open_positions[position['trade_id']] = position
            
            self.logger.info(f"Portfolio state loaded from {file_path} with {len(self.open_positions)} positions")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading portfolio state: {e}")
            return False

    def process_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a trade and update portfolio state.
        
        Args:
            trade: Trade data dictionary
            
        Returns:
            Dictionary with processing result
        """
        try:
            # Validate the trade
            validation = self.validate_trade(trade)
            
            # If rejected, return the validation result
            if validation.get('status') == TradeValidationStatus.REJECTED.value:
                return validation
            
            # Skip further processing for HOLD actions
            if trade.get('action') == "HOLD":
                return validation
            
            # Process the trade based on status
            if trade.get('status') == 'open':
                self._add_open_position(trade)
            elif trade.get('status') == 'closed':
                self._process_closed_trade(trade)
            
            # Update the portfolio snapshot
            self.take_portfolio_snapshot()
            
            return {
                "status": TradeValidationStatus.APPROVED.value,
                "reason": "Trade processed successfully",
                "portfolio_update": "Portfolio state updated"
            }
        
        except Exception as e:
            self.logger.error(f"Error processing trade: {e}")
            return {
                "status": TradeValidationStatus.REJECTED.value,
                "reason": f"Error processing trade: {str(e)}"
            }


if __name__ == "__main__":
    # Simple test code when the module is run directly
    portfolio_manager = PortfolioManagerAgent()
    
    # Print the current portfolio state
    summary = portfolio_manager.get_portfolio_summary()
    print(json.dumps(summary, indent=2))
    
    # Run a portfolio analysis
    analysis = portfolio_manager.analyze()
    print("\nPortfolio Analysis:")
    print(json.dumps(analysis, indent=2))
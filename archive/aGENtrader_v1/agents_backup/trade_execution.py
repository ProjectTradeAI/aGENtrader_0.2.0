"""
Trade Execution Agent

Executes trades based on signals from other agents, manages risk,
and interacts with exchange APIs.
"""

import json
import os
import time
from datetime import datetime
import numpy as np

class TradeExecutionAgent:
    def __init__(self, config_path="config/settings.json"):
        """Initialize the Trade Execution Agent"""
        self.name = "Trade Execution Agent"
        self.config = self._load_config(config_path)
        self.trades = []
        self.balances = self._initialize_balances()

    def _load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}. Using default settings.")
            return {
                "risk_per_trade": 0.02,  # 2% of portfolio per trade
                "max_open_trades": 5,
                "default_assets": ["BTC"],
                "exchange": "binance",
                "api_keys": {
                    "binance": {
                        "api_key": "YOUR_API_KEY_HERE",
                        "api_secret": "YOUR_API_SECRET_HERE"
                    }
                }
            }

    def _initialize_balances(self):
        """Initialize account balances (simulated)"""
        # In a real implementation, this would fetch actual balances from exchange
        return {
            "USD": 10000.00,
            "BTC": 0.1,
            "ETH": 1.5,
            "SOL": 10.0,
            "MATIC": 500.0
        }

    def get_price(self, symbol):
        """Get current price for a symbol (simulated)"""
        # In a real implementation, this would fetch from exchange API
        try:
            from server.trading import currentPrices
            return currentPrices.get(symbol, 0)
        except ImportError:
            # Use default simulated prices
            base_prices = {
                "BTC": 35000,
                "ETH": 2000,
                "SOL": 100,
                "MATIC": 1.2
            }
            # Add some randomness
            return base_prices.get(symbol, 100) * (1 + np.random.uniform(-0.01, 0.01))

    def calculate_position_size(self, symbol, signal_confidence):
        """Calculate position size based on risk management rules"""
        # Get account value in USD
        account_value = self.balances["USD"]
        for asset, amount in self.balances.items():
            if asset != "USD":
                account_value += amount * self.get_price(asset)

        # Calculate risk amount
        risk_amount = account_value * self.config["risk_per_trade"] * signal_confidence

        # Convert to quantity
        price = self.get_price(symbol)
        quantity = risk_amount / price

        return round(quantity, 8)  # Round to 8 decimal places for precision

    def execute_trade(self, symbol, trade_type, quantity=None, price=None, signal_confidence=0.5, execution_advice=None):
        """Execute a trade based on the given parameters"""
        current_price = price if price else self.get_price(symbol)

        # If quantity not specified, calculate based on risk management
        if quantity is None:
            # If we have liquidity-based advice, use it for position sizing
            if execution_advice and "max_recommended_size" in execution_advice:
                recommended_sizes = execution_advice["max_recommended_size"]["quantity"]

                # Choose size based on confidence
                if signal_confidence > 80:
                    quantity = recommended_sizes.get("aggressive", None)
                elif signal_confidence > 60:
                    quantity = recommended_sizes.get("moderate", None)
                else:
                    quantity = recommended_sizes.get("conservative", None)

                # If still None, fall back to default calculation
                if quantity is None:
                    quantity = self.calculate_position_size(symbol, signal_confidence)
            else:
                quantity = self.calculate_position_size(symbol, signal_confidence)

        print(f"Executing trade: {trade_type} {quantity} {symbol} at ${current_price}")

        # Check for liquidity warnings
        if execution_advice:
            liquidity_score = execution_advice.get("liquidity_score", 0)
            est_slippage = execution_advice.get("estimated_slippage", 0)

            if liquidity_score < 30:
                print(f"⚠️ WARNING: Low liquidity score ({liquidity_score}). Expect high slippage.")

            if est_slippage > 1.0:
                print(f"⚠️ WARNING: High estimated slippage ({est_slippage}%). Consider smaller trade size.")

            # Implement batch execution for large orders in low liquidity
            if liquidity_score < 50 and execution_advice.get("recommended_batch_sizing") == "multiple_batches":
                print(f"Splitting order into multiple batches due to liquidity concerns")
                # In a real system, this would execute the trade in multiple smaller lots

        # Simulate trade execution
        trade_id = len(self.trades) + 1
        timestamp = datetime.now().isoformat()

        # Update balances based on trade
        if trade_type.lower() == "buy":
            cost = quantity * current_price
            if self.balances["USD"] >= cost:
                self.balances["USD"] -= cost
                self.balances[symbol] = self.balances.get(symbol, 0) + quantity
                execution_status = "executed"
            else:
                execution_status = "failed"
                print(f"Insufficient USD balance for trade. Required: ${cost}, Available: ${self.balances['USD']}")
        else:  # sell
            if self.balances.get(symbol, 0) >= quantity:
                self.balances[symbol] -= quantity
                self.balances["USD"] += quantity * current_price
                execution_status = "executed"
            else:
                execution_status = "failed"
                print(f"Insufficient {symbol} balance for trade. Required: {quantity}, Available: {self.balances.get(symbol, 0)}")

        # Record trade
        trade = {
            "id": trade_id,
            "symbol": symbol,
            "type": trade_type,
            "quantity": quantity,
            "price": current_price,
            "timestamp": timestamp,
            "status": execution_status,
            "signal_confidence": signal_confidence
        }

        self.trades.append(trade)
        self._save_trades()
        self._save_balances()

        return trade

    def process_signal(self, signal):
        """Process a trading signal"""
        symbol = signal.get("asset")
        signal_type = signal.get("signal", "hold").lower()
        confidence = signal.get("confidence", 0)

        if signal_type in ["hold", "neutral"]:
            return None

    def simulate_trade(self, signal):
        """Simulate what a trade would look like without executing it"""
        symbol = signal.get("asset")
        signal_type = signal.get("signal", "hold").lower()
        confidence = signal.get("confidence", 0)

        if signal_type in ["hold", "neutral"]:
            return None

        # Get current portfolio status
        portfolio = self.get_portfolio_status()

        # Get current price for the symbol
        current_price = self._get_current_price(symbol)
        if not current_price:
            return None

        # Get risk profile settings
        risk_per_trade = self.config.get("risk_per_trade", 0.02)  # Default 2% risk per trade

        # Calculate position size based on portfolio value and risk
        position_size_usd = portfolio["total_value_usd"] * risk_per_trade

        # Adjust based on confidence
        confidence_factor = max(0.5, min(1.5, confidence / 50.0))  # 0.5 to 1.5 based on confidence
        position_size_usd *= confidence_factor

        # Calculate quantity
        quantity = position_size_usd / current_price

        # Calculate stop loss and take profit levels (example: 5% for stop loss, 10% for take profit)
        stop_loss = current_price * (0.95 if signal_type == "buy" else 1.05)
        take_profit = current_price * (1.10 if signal_type == "buy" else 0.90)

        # Create simulation result
        simulation = {
            "symbol": symbol,
            "type": signal_type,
            "price": current_price,
            "quantity": quantity,
            "value_usd": position_size_usd,
            "portfolio_percentage": (position_size_usd / portfolio["total_value_usd"]) * 100,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward_ratio": 2.0,  # 10% take profit vs 5% stop loss
            "simulated": True
        }

        return simulation

    def _get_current_price(self, symbol):
        return self.get_price(symbol)

    def _save_trades(self):
        """Save trades to file"""
        os.makedirs("data", exist_ok=True)
        with open("data/trade_history.json", "w") as file:
            json.dump(self.trades, file, indent=2)

    def _save_balances(self):
        """Save current balances to file"""
        os.makedirs("data", exist_ok=True)
        with open("data/account_balances.json", "w") as file:
            json.dump(self.balances, file, indent=2)

    def get_portfolio_status(self):
        """Get current portfolio status"""
        total_value_usd = self.balances["USD"]
        portfolio = []

        for asset, amount in self.balances.items():
            if asset != "USD" and amount > 0:
                price = self.get_price(asset)
                value_usd = amount * price
                total_value_usd += value_usd

                portfolio.append({
                    "asset": asset,
                    "amount": amount,
                    "price": price,
                    "value_usd": value_usd
                })

        return {
            "total_value_usd": total_value_usd,
            "assets": portfolio,
            "cash_balance": self.balances["USD"],
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Test the agent
    agent = TradeExecutionAgent()

    # Test with a sample signal
    test_signal = {
        "asset": "ETH",
        "signal": "buy",
        "confidence": 0.75
    }

    trade = agent.process_signal(test_signal)
    print(f"Executed trade: {trade}")

    portfolio = agent.get_portfolio_status()
    print(f"Portfolio status: {portfolio}")
"""
Trade Execution Agent

Executes trading decisions and manages active positions.
"""

import json
import os
import random
from datetime import datetime

class TradeExecutionAgent:
    def __init__(self):
        """Initialize the Trade Execution Agent"""
        self.name = "Trade Execution Agent"
        self.portfolio_file = "data/account_balances.json"
        self.trade_history_file = "data/trade_history.json"
        
        # Ensure data directories exist
        os.makedirs("data", exist_ok=True)
        
        # Initialize portfolio if it doesn't exist
        if not os.path.exists(self.portfolio_file):
            self._initialize_portfolio()
        
        # Initialize trade history if it doesn't exist
        if not os.path.exists(self.trade_history_file):
            with open(self.trade_history_file, "w") as file:
                json.dump([], file)
    
    def _initialize_portfolio(self):
        """Initialize portfolio with default values"""
        portfolio = {
            "cash_balance": 10000.0,  # Starting with $10,000 USDT
            "assets": [
                {
                    "asset": "BTCUSDT",
                    "amount": 0.1,
                    "average_price": 30000.0,
                    "price": 30000.0,
                    "value_usd": 3000.0
                }
            ],
            "total_value_usd": 13000.0,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.portfolio_file, "w") as file:
            json.dump(portfolio, file, indent=2)
    
    def get_portfolio_status(self):
        """Get current portfolio status"""
        try:
            with open(self.portfolio_file, "r") as file:
                portfolio = json.load(file)
            
            # Update current prices and values
            total_value = portfolio["cash_balance"]
            for asset in portfolio["assets"]:
                # In a real implementation, get actual market price
                current_price = self._get_current_price(asset["asset"])
                asset["price"] = current_price
                asset["value_usd"] = asset["amount"] * current_price
                total_value += asset["value_usd"]
            
            portfolio["total_value_usd"] = total_value
            portfolio["last_updated"] = datetime.now().isoformat()
            
            # Save updated portfolio
            with open(self.portfolio_file, "w") as file:
                json.dump(portfolio, file, indent=2)
                
            return portfolio
        except Exception as e:
            print(f"Error getting portfolio status: {str(e)}")
            return self._initialize_portfolio()
    
    def process_signal(self, signal):
        """
        Process a trading signal and execute a trade
        
        Args:
            signal (dict): Trading signal with asset, signal type, confidence, etc.
            
        Returns:
            dict: Trade execution details or None if no trade executed
        """
        if not signal or "asset" not in signal or "signal" not in signal:
            return None
        
        asset = signal["asset"]
        signal_type = signal["signal"]
        confidence = signal.get("confidence", 50)
        
        # Don't trade on low confidence
        if confidence < 60:
            return None
        
        # Don't trade on neutral/hold signals
        if signal_type in ["hold", "neutral"]:
            return None
        
        # Get current portfolio
        portfolio = self.get_portfolio_status()
        
        # Get current price
        current_price = self._get_current_price(asset)
        
        # Calculate trade amount based on confidence
        if signal_type == "buy":
            # Size position based on confidence and available cash
            position_size_percent = min(confidence / 200, 0.3)  # Max 30% of portfolio
            cash_to_use = portfolio["cash_balance"] * position_size_percent
            quantity = cash_to_use / current_price
            
            # Execute buy
            trade = self._execute_buy(asset, quantity, current_price, signal.get("strategy", "unknown"))
            return trade
            
        elif signal_type == "sell":
            # Find if we have this asset
            asset_holding = None
            for a in portfolio["assets"]:
                if a["asset"] == asset:
                    asset_holding = a
                    break
            
            if not asset_holding or asset_holding["amount"] <= 0:
                return None
            
            # Size position based on confidence
            sell_percent = min(confidence / 100, 1.0)
            quantity = asset_holding["amount"] * sell_percent
            
            # Execute sell
            trade = self._execute_sell(asset, quantity, current_price, signal.get("strategy", "unknown"))
            return trade
        
        return None
    
    def _execute_buy(self, asset, quantity, price, strategy):
        """Execute a buy trade"""
        # Round quantity to 5 decimal places
        quantity = round(quantity, 5)
        
        # Calculate total cost
        total_cost = quantity * price
        
        # Get current portfolio
        with open(self.portfolio_file, "r") as file:
            portfolio = json.load(file)
        
        # Check if we have enough cash
        if total_cost > portfolio["cash_balance"]:
            quantity = portfolio["cash_balance"] / price
            quantity = round(quantity, 5)
            total_cost = quantity * price
        
        # Update cash balance
        portfolio["cash_balance"] -= total_cost
        
        # Find if we already have this asset
        asset_index = -1
        for i, a in enumerate(portfolio["assets"]):
            if a["asset"] == asset:
                asset_index = i
                break
        
        if asset_index >= 0:
            # Update existing asset
            existing_amount = portfolio["assets"][asset_index]["amount"]
            existing_value = existing_amount * portfolio["assets"][asset_index]["average_price"]
            new_value = total_cost
            new_amount = quantity
            
            # Calculate new average price
            portfolio["assets"][asset_index]["average_price"] = (existing_value + new_value) / (existing_amount + new_amount)
            portfolio["assets"][asset_index]["amount"] += quantity
            portfolio["assets"][asset_index]["price"] = price
            portfolio["assets"][asset_index]["value_usd"] = portfolio["assets"][asset_index]["amount"] * price
        else:
            # Add new asset
            portfolio["assets"].append({
                "asset": asset,
                "amount": quantity,
                "average_price": price,
                "price": price,
                "value_usd": quantity * price
            })
        
        # Update total value
        portfolio["total_value_usd"] = portfolio["cash_balance"] + sum(a["value_usd"] for a in portfolio["assets"])
        portfolio["last_updated"] = datetime.now().isoformat()
        
        # Save updated portfolio
        with open(self.portfolio_file, "w") as file:
            json.dump(portfolio, file, indent=2)
        
        # Record trade
        trade = {
            "timestamp": datetime.now().isoformat(),
            "type": "buy",
            "symbol": asset,
            "quantity": quantity,
            "price": price,
            "total_cost": total_cost,
            "strategy": strategy
        }
        
        self._record_trade(trade)
        
        return trade
    
    def _execute_sell(self, asset, quantity, price, strategy):
        """Execute a sell trade"""
        # Round quantity to 5 decimal places
        quantity = round(quantity, 5)
        
        # Calculate total value
        total_value = quantity * price
        
        # Get current portfolio
        with open(self.portfolio_file, "r") as file:
            portfolio = json.load(file)
        
        # Find the asset
        asset_index = -1
        for i, a in enumerate(portfolio["assets"]):
            if a["asset"] == asset:
                asset_index = i
                break
        
        if asset_index < 0:
            return None
        
        # Check if we have enough of the asset
        if quantity > portfolio["assets"][asset_index]["amount"]:
            quantity = portfolio["assets"][asset_index]["amount"]
            total_value = quantity * price
        
        # Update asset amount
        portfolio["assets"][asset_index]["amount"] -= quantity
        portfolio["assets"][asset_index]["price"] = price
        portfolio["assets"][asset_index]["value_usd"] = portfolio["assets"][asset_index]["amount"] * price
        
        # Remove asset if amount is zero
        if portfolio["assets"][asset_index]["amount"] <= 0:
            portfolio["assets"].pop(asset_index)
        
        # Update cash balance
        portfolio["cash_balance"] += total_value
        
        # Update total value
        portfolio["total_value_usd"] = portfolio["cash_balance"] + sum(a["value_usd"] for a in portfolio["assets"])
        portfolio["last_updated"] = datetime.now().isoformat()
        
        # Save updated portfolio
        with open(self.portfolio_file, "w") as file:
            json.dump(portfolio, file, indent=2)
        
        # Record trade
        trade = {
            "timestamp": datetime.now().isoformat(),
            "type": "sell",
            "symbol": asset,
            "quantity": quantity,
            "price": price,
            "total_value": total_value,
            "strategy": strategy
        }
        
        self._record_trade(trade)
        
        return trade
    
    def _record_trade(self, trade):
        """Record a trade in the trade history"""
        try:
            with open(self.trade_history_file, "r") as file:
                trades = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            trades = []
        
        trades.append(trade)
        
        with open(self.trade_history_file, "w") as file:
            json.dump(trades, file, indent=2)
    
    def _get_current_price(self, symbol):
        """Get the current price for a symbol (mock implementation)"""
        # This would normally call an exchange API
        base_prices = {
            "BTCUSDT": 30000,
            "ETHUSDT": 2000,
            "BNBUSDT": 300,
            "XRPUSDT": 0.5,
            "ADAUSDT": 0.4,
            "SOLUSDT": 100,
            "DOGEUSDT": 0.1
        }
        
        # Get base price or generate random if not in our list
        base_price = base_prices.get(symbol, random.uniform(10, 1000))
        
        # Add some randomness
        current_price = base_price * (1 + random.uniform(-0.05, 0.05))
        return round(current_price, 2)
    
    def get_trade_history(self, limit=10):
        """Get recent trade history"""
        try:
            with open(self.trade_history_file, "r") as file:
                trades = json.load(file)
            return trades[-limit:]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

"""
Strategy Manager Agent with dummy strategy implementation
"""
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import importlib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class BaseStrategy:
    """Base class for all trading strategies"""
    def __init__(self, name):
        self.name = name
        self.last_signal = "hold"
        self._params = {}

    @property
    def params(self):
        """Get strategy parameters"""
        return self._params

    def update_parameters(self, params):
        """Update strategy parameters"""
        if not isinstance(params, dict):
            raise ValueError("Parameters must be a dictionary")
        self._params.update(params)

    def get_signal(self, context):
        """Generate trading signal based on context"""
        raise NotImplementedError("Subclasses must implement get_signal")

    def analyze(self, price_data):
        """Analyze price data"""
        raise NotImplementedError("Subclasses must implement analyze")

    def __str__(self):
        """String representation of the strategy"""
        return f"{self.name}Strategy"

class RSIStrategy(BaseStrategy):
    """RSI-based trading strategy"""
    def __init__(self):
        super().__init__("RSI")
        self._params = {
            "period": 14,
            "overbought": 70,
            "oversold": 30
        }

    def analyze(self, price_data):
        """Analyze using RSI"""
        if isinstance(price_data, (int, float)):
            return "hold"
        if len(price_data) < self._params["period"]:
            return "hold"
        # Simple RSI simulation for testing
        if price_data[-1] > price_data[-2] * 1.02:  # 2% up
            return "sell"  # Overbought
        if price_data[-1] < price_data[-2] * 0.98:  # 2% down
            return "buy"   # Oversold
        return "hold"

    def get_signal(self, context):
        """Get trading signal"""
        if isinstance(context, dict):
            if context.get("market_trend") == "strongly_bullish":
                self.last_signal = "buy"
            elif context.get("market_trend") == "strongly_bearish":
                self.last_signal = "sell"
            elif "price_history" in context:
                self.last_signal = self.analyze(context["price_history"])
            else:
                self.last_signal = "hold"
        return self.last_signal

class MACDStrategy(BaseStrategy):
    """MACD-based trading strategy"""
    def __init__(self):
        super().__init__("MACD")
        self._params = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        }

    def analyze(self, price_data):
        """Analyze using MACD"""
        if isinstance(price_data, (int, float)):
            return "hold"
        if len(price_data) < self._params["slow_period"]:
            return "hold"
        # Simple MACD simulation for testing
        if price_data[-1] > price_data[-2] * 1.01:  # 1% up
            return "buy"
        if price_data[-1] < price_data[-2] * 0.99:  # 1% down
            return "sell"
        return "hold"

    def get_signal(self, context):
        """Get trading signal"""
        if isinstance(context, dict):
            if context.get("market_trend") == "strongly_bullish":
                self.last_signal = "buy"
            elif context.get("market_trend") == "strongly_bearish":
                self.last_signal = "sell"
            elif "price_history" in context:
                self.last_signal = self.analyze(context["price_history"])
            else:
                self.last_signal = "hold"
        return self.last_signal

class StrategyManagerAgent:
    def __init__(self, config_path="config/settings.json"):
        """Initialize the Strategy Manager Agent"""
        self.name = "Strategy Manager Agent"
        self.config = self._load_config(config_path)
        self.strategies = self._load_strategies()
        self.strategy_performance = {}
        self.current_strategy_map = {}  # Maps symbols to current strategies
        self._strategy_library = None  # Private variable to store strategy library
        self._initialize_strategy_library()  # Initialize the library
        self.ml_models = {}  # ML models for strategy selection

    def _load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}. Using default settings.")
            return {
                "strategies": ["sma", "rsi", "macd"],
                "default_strategy": "sma",
                "strategy_evaluation_period": 72,  # hours
                "strategy_switch_threshold": 0.05,  # 5% better performance required to switch
                "symbols": ["BTC", "ETH", "SOL", "MATIC"],
                "risk_levels": ["low", "medium", "high"]
            }

    @property
    def strategy_library(self):
        """Return the strategy library containing available strategies and their profiles"""
        if self._strategy_library is None:
            self._strategy_library = self._load_strategy_library()
        return self._strategy_library

    def _initialize_strategy_library(self):
        """Initialize the strategy library"""
        self._strategy_library = self._load_strategy_library()

    def _load_strategies(self):
        """Load strategy modules"""
        strategies = {}

        try:
            # Initialize built-in strategies
            strategies["rsi"] = RSIStrategy()
            strategies["macd"] = MACDStrategy()
            strategies["sma"] = DummyStrategy("sma")  # Fallback for SMA

            print("Successfully loaded RSI and MACD strategies")
        except Exception as e:
            print(f"Error loading built-in strategies: {str(e)}")
            # Fallback to dummy implementations
            strategies["sma"] = DummyStrategy("sma")
            strategies["rsi"] = DummyStrategy("rsi")
            strategies["macd"] = DummyStrategy("macd")
            print("Using dummy implementations for strategies")

        return strategies

    def _load_strategy_library(self):
        """Load the library of strategy profiles and performance history"""
        try:
            filepath = "data/strategy_library.json"
            if os.path.exists(filepath):
                with open(filepath, 'r') as file:
                    return json.load(file)

            # If no library exists, create it with default risk profiles
            default_library = {
                "strategies": {
                    "sma": {
                        "name": "SMA Crossover",
                        "description": "Simple Moving Average crossover strategy",
                        "risk_profile": "medium",
                        "parameters": {"short_period": 10, "long_period": 30},
                        "suitable_market_conditions": ["trending", "low_volatility"]
                    },
                    "rsi": {
                        "name": "RSI Oscillator",
                        "description": "Relative Strength Index based trading",
                        "risk_profile": "medium",
                        "parameters": {"overbought": 70, "oversold": 30, "period": 14},
                        "suitable_market_conditions": ["ranging", "high_volatility"]
                    },
                    "macd": {
                        "name": "MACD Indicator",
                        "description": "Moving Average Convergence Divergence",
                        "risk_profile": "high",
                        "parameters": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
                        "suitable_market_conditions": ["trending", "medium_volatility"]
                    }
                },
                "risk_profiles": {
                    "low": {
                        "max_trades_per_day": 3,
                        "max_position_size_pct": 5,
                        "stop_loss_pct": 2,
                        "take_profit_pct": 4
                    },
                    "medium": {
                        "max_trades_per_day": 8,
                        "max_position_size_pct": 10,
                        "stop_loss_pct": 5,
                        "take_profit_pct": 8
                    },
                    "high": {
                        "max_trades_per_day": 15,
                        "max_position_size_pct": 20,
                        "stop_loss_pct": 10,
                        "take_profit_pct": 15
                    }
                }
            }

            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Save the default library
            with open(filepath, 'w') as file:
                json.dump(default_library, file, indent=2)

            return default_library
        except Exception as e:
            print(f"Error loading strategy library: {str(e)}")
            return {"strategies": {}, "risk_profiles": {}}

    def _save_strategy_library(self):
        """Save the strategy library to storage"""
        try:
            filepath = "data/strategy_library.json"
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w') as file:
                json.dump(self._strategy_library, file, indent=2)
        except Exception as e:
            print(f"Error saving strategy library: {str(e)}")

    def _get_default_strategy(self, symbol: str):
        """Get the default strategy for a symbol"""
        default_name = self.config.get("default_strategy", "sma")
        return self.strategies.get(default_name, next(iter(self.strategies.values())))

    def _load_performance_data(self):
        """Load strategy performance data from storage"""
        try:
            filepath = "data/strategy_performance.json"
            if os.path.exists(filepath):
                with open(filepath, 'r') as file:
                    return json.load(file)
            return {}
        except Exception as e:
            print(f"Error loading strategy performance data: {str(e)}")
            return {}

    def _save_performance_data(self):
        """Save strategy performance data to storage"""
        try:
            filepath = "data/strategy_performance.json"
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w') as file:
                json.dump(self.strategy_performance, file, indent=2)
        except Exception as e:
            print(f"Error saving strategy performance data: {str(e)}")

    def add_new_strategy(self, name: str, description: str, risk_profile: str = "medium", parameters: Dict = None):
        """Add a new strategy to the library"""
        if parameters is None:
            parameters = {}

        if name not in self._strategy_library["strategies"]:
            self._strategy_library["strategies"][name] = {
                "name": name,
                "description": description,
                "risk_profile": risk_profile,
                "parameters": parameters,
                "suitable_market_conditions": [],
                "performance_history": {},
                "created_at": datetime.now().isoformat()
            }

            self._save_strategy_library()
            return True
        return False

    def update_strategy_risk_profile(self, name: str, risk_profile: str):
        """Update the risk profile of a strategy"""
        if name in self._strategy_library["strategies"]:
            self._strategy_library["strategies"][name]["risk_profile"] = risk_profile
            self._save_strategy_library()
            return True
        return False

    def get_strategies_by_risk_profile(self, risk_profile: str):
        """Get strategies matching a specific risk profile"""
        return {
            name: details for name, details in self._strategy_library["strategies"].items()
            if details.get("risk_profile") == risk_profile
        }

    def get_risk_profile_details(self, risk_profile: str):
        """Get details for a specific risk profile"""
        return self._strategy_library.get("risk_profiles", {}).get(risk_profile, {})

    def analyze_strategy_performance(self, market_data: Dict[str, Any], sentiment_data: Optional[Dict[str, Any]] = None):
        """Analyze recent performance of different strategies"""
        if not market_data:
            return

        # Load existing performance data
        self.strategy_performance = self._load_performance_data()

        # Update performance metrics for each strategy and symbol
        for symbol in self.config.get("symbols", ["BTC", "ETH", "SOL", "MATIC"]):
            if symbol not in market_data:
                continue

            symbol_data = market_data[symbol]

            # Ensure the symbol exists in the performance data
            if symbol not in self.strategy_performance:
                self.strategy_performance[symbol] = {}

            # Evaluate each strategy
            for strategy_name, strategy in self.strategies.items():
                if strategy_name not in self.strategy_performance[symbol]:
                    self.strategy_performance[symbol][strategy_name] = {
                        "win_rate": 0.0,
                        "profit_factor": 0.0,
                        "avg_return": 0.0,
                        "sharpe_ratio": 0.0,
                        "trades": 0,
                        "last_updated": datetime.now().isoformat()
                    }

                # Get historical price data
                price_data = self._get_price_data(symbol, 30)  # Get last 30 data points

                if not price_data or len(price_data) < 10:
                    continue

                # Backtest the strategy on recent data
                performance = self._backtest_strategy(strategy, price_data)

                # Update the performance metrics
                if performance:
                    self.strategy_performance[symbol][strategy_name].update(performance)
                    self.strategy_performance[symbol][strategy_name]["last_updated"] = datetime.now().isoformat()

                # Update strategy library with performance data
                if strategy_name in self._strategy_library["strategies"]:
                    if "performance_history" not in self._strategy_library["strategies"][strategy_name]:
                        self._strategy_library["strategies"][strategy_name]["performance_history"] = {}

                    if symbol not in self._strategy_library["strategies"][strategy_name]["performance_history"]:
                        self._strategy_library["strategies"][strategy_name]["performance_history"][symbol] = []

                    # Add this performance point to history
                    self._strategy_library["strategies"][strategy_name]["performance_history"][symbol].append({
                        "timestamp": datetime.now().isoformat(),
                        "win_rate": performance.get("win_rate", 0),
                        "profit_factor": performance.get("profit_factor", 0),
                        "avg_return": performance.get("avg_return", 0),
                        "sharpe_ratio": performance.get("sharpe_ratio", 0),
                        "trades": performance.get("trades", 0)
                    })

                    # Limit history to last 100 points
                    if len(self._strategy_library["strategies"][strategy_name]["performance_history"][symbol]) > 100:
                        self._strategy_library["strategies"][strategy_name]["performance_history"][symbol] = \
                            self._strategy_library["strategies"][strategy_name]["performance_history"][symbol][-100:]

        # Save updated performance data
        self._save_performance_data()
        self._save_strategy_library()

        # Train ML models with updated data
        self._train_ml_models()

    def _get_price_data(self, symbol: str, lookback: int = 30) -> List[float]:
        """Get historical price data for a symbol (simulated)"""
        # In a real implementation, this would fetch actual price data
        # For now, generate some mock data
        try:
            filepath = f"data/market_data_{symbol.lower()}.json"
            if os.path.exists(filepath):
                with open(filepath, 'r') as file:
                    data = json.load(file)
                    return data.get("prices", [])[-lookback:]

            # If no data file exists, generate synthetic data
            base_price = {
                "BTC": 45000,
                "ETH": 2500,
                "SOL": 100,
                "MATIC": 1.5
            }.get(symbol, 100)

            # Generate slightly random walk prices
            volatility = 0.02  # 2% volatility
            prices = [base_price]
            for _ in range(lookback - 1):
                change = np.random.normal(0, volatility)
                prices.append(prices[-1] * (1 + change))

            return prices
        except Exception as e:
            print(f"Error getting price data for {symbol}: {str(e)}")
            return []

    def _backtest_strategy(self, strategy, price_data) -> Dict[str, float]:
        """Backtest a strategy on historical price data"""
        if not price_data or len(price_data) < 5:
            return None

        trades = []
        position = 0  # 0 = no position, 1 = long, -1 = short
        entry_price = 0
        trade_count = 0
        winning_trades = 0
        total_return = 0
        returns = []

        # Run the strategy through the price data
        for i, price in enumerate(price_data):
            # Skip the first few data points to allow for indicator calculation
            if i < 3:
                continue

            # Get a window of price data up to the current point
            window = price_data[:i+1]

            # Get the strategy's signal
            try:
                signal = strategy.get_signal({
                    "market_trend": "neutral",  # Default values for backtesting
                    "market_confidence": 50,
                    "sentiment": "neutral",
                    "sentiment_score": 0,
                    "price": price,
                    "price_history": window
                })
            except Exception:
                # If strategy doesn't have get_signal, try simpler methods
                try:
                    signal = strategy.analyze(window)
                except Exception:
                    try:
                        signal = strategy.analyze(price)
                    except Exception:
                        signal = "hold"

            # Process the signal
            if signal == "buy" and position <= 0:
                # Enter long position
                if position < 0:  # Close any existing short position
                    profit_pct = (entry_price - price) / entry_price
                    trades.append(profit_pct)
                    returns.append(profit_pct)
                    trade_count += 1
                    if profit_pct > 0:
                        winning_trades += 1

                position = 1
                entry_price = price

            elif signal == "sell" and position >= 0:
                # Enter short position
                if position > 0:  # Close any existing long position
                    profit_pct = (price - entry_price) / entry_price
                    trades.append(profit_pct)
                    returns.append(profit_pct)
                    trade_count += 1
                    if profit_pct > 0:
                        winning_trades += 1

                position = -1
                entry_price = price

        # Close any open position at the end
        if position != 0:
            final_price = price_data[-1]
            if position > 0:
                profit_pct = (final_price - entry_price) / entry_price
            else:
                profit_pct = (entry_price - final_price) / entry_price

            trades.append(profit_pct)
            returns.append(profit_pct)
            trade_count += 1
            if profit_pct > 0:
                winning_trades += 1

        # Calculate performance metrics
        if not trades:
            return {
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_return": 0.0,
                "sharpe_ratio": 0.0,
                "trades": 0
            }

        winning_trades_pct = winning_trades / trade_count if trade_count > 0 else 0

        # Separate winning and losing trades
        winning_trades_returns = [t for t in trades if t > 0]
        losing_trades_returns = [t for t in trades if t < 0]

        total_gains = sum(winning_trades_returns) if winning_trades_returns else 0
        total_losses = abs(sum(losing_trades_returns)) if losing_trades_returns else 0
        profit_factor = total_gains / total_losses if total_losses > 0 else total_gains if total_gains > 0 else 0

        avg_return = sum(trades) / len(trades)

        # Calculate Sharpe Ratio (assuming no risk-free rate)
        if len(returns) > 1:
            returns_std = np.std(returns)
            sharpe_ratio = (avg_return / returns_std) if returns_std > 0 else 0
        else:
            sharpe_ratio = 0

        return {
            "win_rate": round(winning_trades_pct, 3),
            "profit_factor": round(profit_factor, 3),
            "avg_return": round(avg_return, 4),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "trades": trade_count
        }

    def _train_ml_models(self):
        """Train machine learning models to optimize strategy selection"""
        if not self.strategy_performance:
            return

        for symbol in self.strategy_performance:
            # Prepare data for ML model
            data = []
            labels = []

            # Get strategy performance for this symbol
            symbol_performance = self.strategy_performance[symbol]

            # Skip if we don't have enough data
            if len(symbol_performance) < 2:
                continue

            # Find best performing strategy based on composite score
            best_strategy = None
            best_score = -float('inf')

            for strategy_name, metrics in symbol_performance.items():
                # Calculate a composite score
                score = (
                    metrics.get("win_rate", 0) * 0.3 +
                    metrics.get("profit_factor", 0) * 0.3 +
                    metrics.get("avg_return", 0) * 100 * 0.2 +
                    metrics.get("sharpe_ratio", 0) * 0.2
                )

                if score > best_score:
                    best_score = score
                    best_strategy = strategy_name

            # If we can't determine the best strategy, skip
            if not best_strategy:
                continue

            # Create training data from historical performance
            # In a real implementation, this would use more features from market conditions
            try:
                # Get recent market data for features
                market_data_path = f"data/market_data_{symbol.lower()}.json"
                if os.path.exists(market_data_path):
                    with open(market_data_path, 'r') as file:
                        market_data = json.load(file)

                    # Extract features for model training
                    price_data = market_data.get("prices", [])
                    if len(price_data) < 20:
                        continue

                    # Create features from price data
                    for i in range(10, len(price_data) - 5):
                        window = price_data[i-10:i]

                        # Calculate features
                        features = self._extract_features(window)
                        data.append(features)

                        # For labels, simulate which strategy would have performed best
                        # In real implementation, use actual performance data
                        predicted_returns = {}
                        for strategy_name in symbol_performance:
                            # Simple approximation of returns
                            # In real implementation, calculate actual returns from backtests
                            predicted_returns[strategy_name] = np.random.normal(
                                symbol_performance[strategy_name].get("avg_return", 0),
                                0.01
                            )

                        # Pick strategy with highest expected return
                        best_for_window = max(predicted_returns, key=predicted_returns.get)
                        labels.append(best_for_window)

                    # Ensure we have enough data points
                    if len(data) < 10 or len(labels) < 10:
                        continue

                    # Train a Random Forest classifier
                    try:
                        X = np.array(data)
                        y = np.array(labels)

                        # Split data into training and testing sets
                        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                        # Train the model
                        model = RandomForestClassifier(n_estimators=50, random_state=42)
                        model.fit(X_train, y_train)

                        # Evaluate the model
                        y_pred = model.predict(X_test)
                        accuracy = accuracy_score(y_test, y_pred)

                        print(f"Trained ML model for {symbol} with accuracy: {accuracy:.2f}")

                        # Save the model
                        self.ml_models[symbol] = model
                    except Exception as e:
                        print(f"Error training ML model for {symbol}: {str(e)}")
            except Exception as e:
                print(f"Error preparing ML training data for {symbol}: {str(e)}")

    def _extract_features(self, price_data: List[float]) -> List[float]:
        """Extract features from price data for ML model"""
        if not price_data or len(price_data) < 2:
            return [0, 0, 0, 0, 0]

        # Calculate simple features from price data
        returns = [(price_data[i] / price_data[i-1]) - 1 for i in range(1, len(price_data))]

        features = [
            price_data[-1] / price_data[0] - 1,  # Overall price change
            np.mean(returns),                      # Average return
            np.std(returns),                       # Volatility
            np.percentile(returns, 75) - np.percentile(returns, 25),  # IQR of returns
            np.mean(price_data[-3:]) / np.mean(price_data[:3]) - 1    # Recent trend
        ]

        return features

    def select_strategy_ml(self, symbol: str, market_data: Dict[str, Any]) -> str:
        """Use machine learning to select the best strategy for current market conditions"""
        if symbol not in self.ml_models:
            # If no ML model, fall back to traditional selection
            return None

        try:
            # Extract features from recent market data
            price_data = market_data.get("recent_prices", [])
            if len(price_data) < 10:
                return None

            features = self._extract_features(price_data)

            # Make prediction with ML model
            features_array = np.array([features])
            prediction = self.ml_models[symbol].predict(features_array)[0]

            # Check if predicted strategy exists
            if prediction in self.strategies:
                return prediction
        except Exception as e:
            print(f"Error using ML model for strategy selection: {str(e)}")

        return None

    def select_strategy(self, symbol: str, market_analysis: Dict[str, Any], sentiment_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Select the best strategy for a symbol based on recent performance and market conditions"""
        if not market_analysis:
            return {
                "symbol": symbol,
                "signal": "hold",
                "strategy_name": "none",
                "risk_profile": "none",
                "confidence": 0,
                "reason": "Insufficient market data"
            }

        # First try ML-based selection
        strategy_name = self.select_strategy_ml(symbol, market_analysis)

        if not strategy_name:
            # Use market condition based selection
            market_trend = market_analysis.get("trend", "neutral")

            # Strategy preference based on market conditions
            if market_trend in ["strongly_bullish", "strongly_bearish"]:
                # In strong trends, prefer MACD
                strategy_name = "macd"
            elif market_trend == "neutral":
                # In ranging markets, prefer RSI
                strategy_name = "rsi"
            else:
                # In moderate trends, use performance-based selection
                best_strategy = None
                best_score = -float('inf')

                for name, metrics in self.strategy_performance.get(symbol, {}).items():
                    if name not in self.strategies:
                        continue

                    score = (
                        metrics.get("win_rate", 0) * 0.3 +
                        metrics.get("profit_factor", 0) * 0.3 +
                        metrics.get("avg_return", 0) * 100 * 0.2 +
                        metrics.get("sharpe_ratio", 0) * 0.2
                    )

                    if score > best_score:
                        best_score = score
                        best_strategy = name

                strategy_name = best_strategy if best_strategy else "sma"

        # Get the selected strategy
        strategy = self.strategies[strategy_name]
        strategy_risk = self._get_strategy_risk_profile(strategy_name)

        # Update strategy map
        self.current_strategy_map[symbol] = strategy

        # Create market context
        context = {
            "symbol": symbol,
            "market_trend": market_analysis.get("trend", "neutral"),
            "market_confidence": market_analysis.get("confidence", 50),
            "sentiment": sentiment_analysis.get("sentiment", "neutral") if sentiment_analysis else "neutral",
            "sentiment_score": sentiment_analysis.get("score", 0) if sentiment_analysis else 0,
            "price_history": market_analysis.get("price_history", [])
        }

        # Get signal from strategy
        signal = strategy.get_signal(context)

        # Calculate confidence
        confidence = self._calculate_signal_confidence(
            context["market_trend"],
            context["market_confidence"],
            context["sentiment"],
            context["sentiment_score"],
            strategy
        )

        # Get strategy metrics for reasoning
        metrics = self.strategy_performance.get(symbol, {}).get(strategy_name, {})
        reason = (f"Selected {strategy_name.upper()} strategy based on {context['market_trend']} market trend. "
                 f"Strategy metrics - Win Rate: {metrics.get('win_rate', 0):.2%}, "
                 f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")

        return {
            "symbol": symbol,
            "signal": signal,
            "strategy_name": str(strategy),
            "risk_profile": strategy_risk,
            "confidence": confidence,
            "reason": reason,
            "parameters": strategy.params
        }

    def _get_strategy_risk_profile(self, strategy_name: str) -> str:
        """Get the risk profile for a strategy"""
        if not strategy_name:
            return "medium"

        # Clean up strategy name if needed
        clean_name = strategy_name.lower().replace("strategy", "")

        # Check if in library
        if clean_name in self._strategy_library["strategies"]:
            return self._strategy_library["strategies"][clean_name].get("risk_profile", "medium")

        # Default values for known strategies
        default_profiles = {
            "sma": "low",
            "rsi": "medium",
            "macd": "medium",
            "bollinger": "medium",
            "ichimoku": "high",
            "fibonacci": "high"
        }

        return default_profiles.get(clean_name, "medium")

    def _calculate_signal_confidence(self, market_trend, market_confidence, sentiment, sentiment_score, strategy):
        """Calculate confidence in the signal based on market and sentiment alignment"""
        # Base confidence from market analysis
        confidence = market_confidence / 100.0  # Convert to 0-1 scale

        # Adjust based on market trend alignment with signal
        # If signal is buy and trend is bullish, increase confidence
        try:
            signal = strategy.last_signal
        except:
            signal = "hold"

        if signal == "buy" and market_trend in ["bullish", "strongly_bullish"]:
            confidence += 0.1
        elif signal == "sell" and market_trend in ["bearish", "strongly_bearish"]:
            confidence += 0.1
        elif signal != "hold" and market_trend == "neutral":
            confidence -= 0.1

        # Adjust based on sentiment alignment
        sentiment_factor = 0
        if sentiment == "positive" and signal == "buy":
            sentiment_factor = 0.1
        elif sentiment == "negative" and signal == "sell":
            sentiment_factor = 0.1
        elif sentiment != "neutral" and signal != "hold" and sentiment != signal:
            sentiment_factor = -0.1

        confidence += sentiment_factor * abs(sentiment_score)

        # Ensure confidence is in 0-1 range
        confidence = max(0.0, min(1.0, confidence))

        return round(confidence * 100, 1)  # Convert back to percentage

    def process_market_update(self, symbol, market_analysis=None, sentiment_analysis=None, liquidity_analysis=None):
        """Process market updates and select the best strategy"""
        print(f"Processing market update for {symbol}")

        # If we don't have market analysis, we can't make a decision
        if not market_analysis:
            return {
                "symbol": symbol,
                "signal": "hold",
                "strategy": "none",
                "risk_profile": "none",
                "confidence": 0,
                "reason": "Insufficient data for decision making"
            }

        # If sentiment analysis is disabled, set default neutral values
        if sentiment_analysis is None:
            sentiment_analysis = {
                "sentiment": "neutral",
                "score": 0.5,
                "signal": {"signal": "hold", "confidence": 50}
            }

        # Gather all available signals
        signals = []

        # Add market analysis signal
        if market_analysis and "signal" in market_analysis:
            signals.append({
                "source": "market_analysis",
                "signal": market_analysis["signal"],
                "confidence": market_analysis.get("confidence", 50),
                "timestamp": market_analysis.get("timestamp", datetime.now().isoformat())
            })

        # Add sentiment signal
        if sentiment_analysis and "signal" in sentiment_analysis:
            signals.append({
                "source": "sentiment_analysis",
                "signal": sentiment_analysis["signal"],
                "confidence": sentiment_analysis.get("confidence", 50),
                "timestamp": datetime.now().isoformat()
            })

        # Add liquidity analysis signal
        if liquidity_analysis and "signal" in liquidity_analysis:
            signals.append({
                "source": "liquidity_analysis",
                "signal": liquidity_analysis["signal"],
                "confidence": liquidity_analysis.get("confidence", 50),
                "timestamp": liquidity_analysis.get("timestamp", datetime.now().isoformat())
            })

        # Add on-chain signals if available (not implemented yet)


        # Select the best strategy for this symbol
        strategy_result = self.select_strategy(symbol, market_analysis, sentiment_analysis)

        # Get the risk profile for this strategy
        risk_profile = strategy_result.get("risk_profile", "medium")
        risk_settings = self.get_risk_profile_details(risk_profile)

        # Generate a trading decision
        trading_decision = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "price": market_analysis.get("current_price", 0) if market_analysis else 0,
            "signal": strategy_result.get("signal", "hold"),
            "confidence": strategy_result.get("confidence", 50),
            "strategy": strategy_result.get("strategy_name", "unknown"),
            "risk_profile": risk_profile,
            "reason": strategy_result.get("reason", "No reason provided"),
            "parameters": strategy_result.get("parameters", {}),
            "market_conditions": strategy_result.get("market_conditions", []),
            "execution_advice": liquidity_analysis.get("execution_advice") if liquidity_analysis else None
        }

        # Log the decision
        self._log_trading_decision(trading_decision)

        return trading_decision

    @property
    def strategy_library(self):
        """Return the strategy library containing available strategies and their profiles"""
        return self._strategy_library

    def optimize_strategy_parameters(self, strategy_name: str, symbol: str) -> Dict[str, Any]:
        """
        Optimize parameters for a given strategy based on historical performance

        Args:
            strategy_name: Name of the strategy to optimize
            symbol: Trading symbol (e.g. 'BTC', 'ETH')

        Returns:
            Dict containing optimized parameters
        """
        # Normalize strategy name
        strategy_key = strategy_name.lower().replace('strategy', '')

        if strategy_key not in self.strategies:
            print(f"Strategy {strategy_name} not found. Available strategies: {list(self.strategies.keys())}")
            return None

        try:
            # Get historical price data
            price_data = self._get_price_data(symbol, lookback=60)  # 60 periods for optimization

            if not price_data or len(price_data) < 30:
                print(f"Insufficient price data for {symbol}")
                return None

            # Get strategy default parameters
            strategy = self.strategies[strategy_key]
            default_params = self._strategy_library["strategies"].get(
                strategy_key,
                {}
            ).get("parameters", {})

            if not default_params:
                print(f"No parameters found for {strategy_name}")
                return None

            # Parameter ranges for optimization
            param_ranges = {
                "short_period": range(5, 21, 2),
                "long_period": range(20, 51, 5),
                "rsi_period": range(10, 31, 2),
                "overbought": range(65, 81, 5),
                "oversold": range(20, 36, 5),
                "fast_period": range(8, 16, 2),
                "slow_period": range(20, 32, 4),
                "signal_period": range(7, 12, 1)
            }

            best_params = {}
            best_performance = -float('inf')

            # Simple grid search optimization
            for param_name, param_range in param_ranges.items():
                if param_name in default_params:
                    for value in param_range:
                        test_params = default_params.copy()
                        test_params[param_name] = value

                        # Update strategy parameters
                        try:
                            strategy.update_parameters(test_params)

                            # Backtest with these parameters
                            performance = self._backtest_strategy(strategy, price_data)

                            if performance:
                                # Calculate composite score
                                score = (
                                    performance.get("win_rate", 0) * 0.3 +
                                    performance.get("profit_factor", 0) * 0.3 +
                                    performance.get("avg_return", 0) * 100 * 0.2 +
                                    performance.get("sharpe_ratio", 0) * 0.2
                                )

                                if score > best_performance:
                                    best_performance = score
                                    best_params[param_name] = value
                                    print(f"Found better parameters for {strategy_name}: {param_name}={value}, score={score:.3f}")
                        except Exception as e:
                            print(f"Error testing parameters: {str(e)}")
                            continue

            # Update strategy library with optimized parameters
            if best_params:
                if strategy_key in self._strategy_library["strategies"]:
                    try:
                        self._strategy_library["strategies"][strategy_key]["parameters"].update(best_params)
                        self._save_strategy_library()
                        print(f"Updated parameters for {strategy_name}: {best_params}")
                    except Exception as e:
                        print(f"Error updating strategy library: {str(e)}")

            return best_params

        except Exception as e:
            print(f"Error optimizing parameters for {strategy_name}: {str(e)}")
            return None

    def get_strategy_performance(self) -> Dict[str, Any]:
        """
        Get performance metrics for all strategies across all symbols

        Returns:
            Dict containing performance metrics by symbol and strategy
        """
        try:
            # Load latest performance data
            performance_data = self._load_performance_data()

            # If no performance data, analyze recent performance
            if not performance_data:
                market_data = {}
                for symbol in self.config.get("symbols", ["BTC", "ETH", "SOL", "MATIC"]):
                    prices = self._get_price_data(symbol)
                    if prices:
                        market_data[symbol] = {"prices": prices}

                self.analyze_strategy_performance(market_data)
                performance_data = self._load_performance_data()

            # Format performance data for output
            formatted_metrics = {}

            for symbol, strategies in performance_data.items():
                formatted_metrics[symbol] = {}

                for strategy_name, metrics in strategies.items():
                    # Round numeric values for better readability
                    formatted_metrics[symbol][strategy_name] = {
                        "win_rate": round(metrics.get("win_rate", 0) * 100, 2),
                        "profit_factor": round(metrics.get("profit_factor", 0), 2),
                        "avg_return": round(metrics.get("avg_return", 0) * 100, 2),
                        "sharpe_ratio": round(metrics.get("sharpe_ratio", 0), 2),
                        "trades": metrics.get("trades", 0),
                        "last_updated": metrics.get("last_updated", "")
                    }

            return formatted_metrics
        except Exception as e:
            print(f"Error getting strategy performance: {str(e)}")
            return {}

    def _log_trading_decision(self, decision):
        """Log a trading decision to file"""
        try:
            filepath = "data/trading_decisions.json"

            # Ensure the directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Load existing decisions
            decisions = []
            if os.path.exists(filepath):
                with open(filepath, 'r') as file:
                    try:
                        decisions = json.load(file)
                    except:
                        decisions = []

            # Add the new decision
            decisions.append(decision)

            # Keep only the last 1000 decisions
            if len(decisions) > 1000:
                decisions = decisions[-1000:]

            # Save the updated decisions
            with open(filepath, 'w') as file:
                json.dump(decisions, file, indent=2)

        except Exception as e:
            print(f"Error logging trading decision: {str(e)}")

    def get_strategy_performance(self, symbol=None):
        """Get performance metrics for strategies"""
        if not self.strategy_performance:
            self.strategy_performance = self._load_performance_data()

        if symbol:
            return self.strategy_performance.get(symbol, {})
        return self.strategy_performance

    def get_strategy_library(self):
        """Get the full strategy library"""
        return self._strategy_library

    def get_current_market_regime(self):
        """Determine the current market regime based on trend and volatility"""
        # This method is used by the meeting coordinator to provide context
        try:
            # Get market data for BTC as a proxy for overall market
            btc_data = self._get_price_data("BTC", 30)
            if not btc_data or len(btc_data) < 10:
                return "neutral"

            # Calculate returns
            returns = [btc_data[i]/btc_data[i-1] - 1 for i in range(1, len(btc_data))]

            # Calculate volatility (standard deviation of returns)
            volatility = np.std(returns) * 100  # Convert to percentage

            # Calculate overall trend
            overall_trend = btc_data[-1] / btc_data[0] - 1

            # Determine market regime
            if overall_trend > 0.05:  # 5% up
                if volatility > 3:
                    return "bullish_volatile"
                else:
                    return "bullish_stable"
            elif overall_trend < -0.05:  # 5% down
                if volatility > 3:
                    return "bearish_volatile"
                else:
                    return "bearish_stable"
            else:
                if volatility > 2:
                    return "choppy"
                else:
                    return "consolidating"
        except Exception as e:
            print(f"Error determining market regime: {str(e)}")
            return "neutral"



class DummyStrategy(BaseStrategy):
    """Fallback strategy implementation"""
    def __init__(self, name):
        super().__init__(name.upper())
        self._params = {
            "period": 14,
            "overbought": 70,
            "oversold": 30
        }

    def analyze(self, price_data):
        """Simple analysis returning hold signal"""
        return "hold"

    def get_signal(self, context):
        """Get trading signal based on context"""
        if context.get("market_trend") == "strongly_bullish":
            self.last_signal = "buy"
        elif context.get("market_trend") == "strongly_bearish":
            self.last_signal = "sell"
        else:
            self.last_signal = "hold"
        return self.last_signal
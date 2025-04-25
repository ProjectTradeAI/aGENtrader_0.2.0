"""
Improved Simplified Trading Test

A robust simplified test for EC2 deployment that doesn't require AutoGen but still
provides meaningful testing capabilities for trading strategies.
"""

import os
import sys
import json
import time
import random
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"simplified_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("improved_simplified_test")

class SimpleTrader:
    """Simple trader that implements various trading strategies for backtesting."""
    
    def __init__(self, initial_balance: float = 10000.0, risk_per_trade: float = 0.02):
        """
        Initialize the trader.
        
        Args:
            initial_balance: Initial account balance
            risk_per_trade: Risk per trade as percentage of account (0.02 = 2%)
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.position = None
        self.trades = []
        self.equity_curve = []
        
        # Track max values
        self.max_balance = initial_balance
        self.min_balance = initial_balance
        
    def reset(self):
        """Reset the trader to initial state."""
        self.balance = self.initial_balance
        self.position = None
        self.trades = []
        self.equity_curve = []
        self.max_balance = self.initial_balance
        self.min_balance = self.initial_balance
    
    def update_equity(self, timestamp: str, current_price: float):
        """Update the equity curve."""
        equity = self.balance
        if self.position:
            # Add unrealized profit/loss from current position
            equity += self.position['size'] * (current_price - self.position['entry_price'])
        
        self.equity_curve.append({"timestamp": timestamp, "equity": equity})
        
        # Update max/min balance
        self.max_balance = max(self.max_balance, equity)
        self.min_balance = min(self.min_balance, equity)
        
        return equity
    
    def open_position(self, trade_type: str, entry_price: float, timestamp: str, 
                     stop_loss_pct: float = 0.02, take_profit_pct: float = 0.04):
        """
        Open a new position.
        
        Args:
            trade_type: 'long' or 'short'
            entry_price: Entry price
            timestamp: Entry timestamp
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            
        Returns:
            Boolean indicating success
        """
        if self.position is not None:
            logger.warning("Cannot open position - already have an open position")
            return False
        
        # Calculate position size based on risk
        risk_amount = self.balance * self.risk_per_trade
        position_size = risk_amount / (entry_price * stop_loss_pct)
        cost = position_size * entry_price
        
        if cost > self.balance:
            logger.warning("Cannot open position - insufficient balance")
            return False
        
        if trade_type == 'long':
            stop_level = entry_price * (1 - stop_loss_pct)
            take_profit = entry_price * (1 + take_profit_pct)
        else:  # short
            stop_level = entry_price * (1 + stop_loss_pct)
            take_profit = entry_price * (1 - take_profit_pct)
        
        # Create position
        self.position = {
            "type": trade_type,
            "entry_price": entry_price,
            "size": position_size,
            "entry_time": timestamp,
            "stop_loss": stop_level,
            "take_profit": take_profit
        }
        
        # Update balance
        self.balance -= cost
        
        logger.info(f"Opened {trade_type.upper()} position at ${entry_price:.2f}, size: {position_size:.4f}, balance: ${self.balance:.2f}")
        return True
    
    def close_position(self, exit_price: float, timestamp: str, reason: str = "manual"):
        """
        Close the current position.
        
        Args:
            exit_price: Exit price
            timestamp: Exit timestamp
            reason: Reason for closing ('stop_loss', 'take_profit', 'signal', 'manual')
            
        Returns:
            Dictionary with trade information
        """
        if self.position is None:
            logger.warning("Cannot close position - no open position")
            return None
        
        # Calculate profit/loss
        if self.position['type'] == 'long':
            exit_value = self.position['size'] * exit_price
            entry_value = self.position['size'] * self.position['entry_price']
        else:  # short
            exit_value = 2 * self.position['size'] * self.position['entry_price'] - self.position['size'] * exit_price
            entry_value = self.position['size'] * self.position['entry_price']
        
        profit_loss = exit_value - entry_value
        profit_loss_pct = (profit_loss / entry_value) * 100
        
        # Update balance
        self.balance += exit_value
        
        # Record trade
        trade = {
            "type": self.position['type'],
            "entry_time": self.position['entry_time'],
            "entry_price": self.position['entry_price'],
            "exit_time": timestamp,
            "exit_price": exit_price,
            "size": self.position['size'],
            "profit_loss": profit_loss,
            "profit_loss_pct": profit_loss_pct,
            "exit_reason": reason
        }
        self.trades.append(trade)
        
        logger.info(f"Closed {self.position['type'].upper()} position at ${exit_price:.2f}, P/L: ${profit_loss:.2f} ({profit_loss_pct:.2f}%), balance: ${self.balance:.2f}, reason: {reason}")
        
        # Clear position
        self.position = None
        
        return trade
    
    def check_position_exits(self, current_price: float, timestamp: str):
        """
        Check if current price hits stop loss or take profit levels.
        
        Args:
            current_price: Current price
            timestamp: Current timestamp
            
        Returns:
            Boolean indicating if position was closed
        """
        if self.position is None:
            return False
        
        if self.position['type'] == 'long':
            if current_price <= self.position['stop_loss']:
                self.close_position(current_price, timestamp, "stop_loss")
                return True
            elif current_price >= self.position['take_profit']:
                self.close_position(current_price, timestamp, "take_profit")
                return True
        else:  # short
            if current_price >= self.position['stop_loss']:
                self.close_position(current_price, timestamp, "stop_loss")
                return True
            elif current_price <= self.position['take_profit']:
                self.close_position(current_price, timestamp, "take_profit")
                return True
        
        return False
    
    def calculate_indicators(self, data: List[Dict[str, Any]], current_idx: int, lookback: int = 20):
        """
        Calculate technical indicators for the current bar.
        
        Args:
            data: List of historical bars
            current_idx: Index of current bar
            lookback: Number of bars to look back
            
        Returns:
            Dictionary of indicators
        """
        # Ensure we have enough data
        if current_idx < lookback:
            return None
        
        # Get relevant price data
        prices = [bar['close'] for bar in data[current_idx-lookback:current_idx+1]]
        
        # Simple Moving Averages
        sma_short = sum(prices[-5:]) / 5  # 5-period SMA
        sma_med = sum(prices[-10:]) / 10  # 10-period SMA
        sma_long = sum(prices) / len(prices)  # lookback-period SMA
        
        # Calculate RSI (simplified)
        gains = [prices[i] - prices[i-1] for i in range(1, len(prices)) if prices[i] > prices[i-1]]
        losses = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices)) if prices[i] < prices[i-1]]
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0.001  # Avoid division by zero
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Calculate basic MACD
        ema12 = sum(prices[-12:]) / 12 if len(prices) >= 12 else None
        ema26 = sum(prices[-26:]) / 26 if len(prices) >= 26 else None
        macd = ema12 - ema26 if ema12 and ema26 else None
        
        # Simple volatility measure (standard deviation)
        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        volatility = variance ** 0.5
        
        return {
            'sma_short': sma_short,
            'sma_med': sma_med,
            'sma_long': sma_long,
            'rsi': rsi,
            'macd': macd,
            'volatility': volatility,
            'current_price': prices[-1],
            'prev_price': prices[-2]
        }
    
    def moving_average_crossover_strategy(self, indicators: Optional[Dict[str, Any]]):
        """
        Simple moving average crossover strategy.
        
        Args:
            indicators: Dictionary of technical indicators
            
        Returns:
            Signal ('buy', 'sell', or None)
        """
        if not indicators:
            return None
        
        # Check for crossover
        if indicators['sma_short'] > indicators['sma_long'] and indicators['prev_price'] < indicators['sma_long']:
            return 'buy'
        elif indicators['sma_short'] < indicators['sma_long'] and indicators['prev_price'] > indicators['sma_long']:
            return 'sell'
        
        return None
    
    def rsi_strategy(self, indicators: Optional[Dict[str, Any]]):
        """
        RSI-based trading strategy.
        
        Args:
            indicators: Dictionary of technical indicators
            
        Returns:
            Signal ('buy', 'sell', or None)
        """
        if not indicators or 'rsi' not in indicators:
            return None
        
        # Buy when RSI crosses above 30 (oversold)
        if indicators['rsi'] > 30 and indicators['rsi'] < 40:
            return 'buy'
        # Sell when RSI crosses below 70 (overbought)
        elif indicators['rsi'] > 70:
            return 'sell'
        
        return None
    
    def combined_strategy(self, indicators: Optional[Dict[str, Any]]):
        """
        Combined trading strategy using multiple indicators.
        
        Args:
            indicators: Dictionary of technical indicators
            
        Returns:
            Signal ('buy', 'sell', or None)
        """
        if not indicators:
            return None
        
        ma_signal = self.moving_average_crossover_strategy(indicators)
        rsi_signal = self.rsi_strategy(indicators)
        
        # Only buy when both strategies agree
        if ma_signal == 'buy' and rsi_signal == 'buy':
            return 'buy'
        # Sell when either strategy says sell
        elif ma_signal == 'sell' or rsi_signal == 'sell':
            return 'sell'
        
        return None
    
    def get_trading_signal(self, data: List[Dict[str, Any]], current_idx: int, strategy: str = 'ma_crossover'):
        """
        Get trading signal for the current bar.
        
        Args:
            data: List of historical bars
            current_idx: Index of current bar
            strategy: Strategy to use ('ma_crossover', 'rsi', 'combined')
            
        Returns:
            Signal ('buy', 'sell', or None)
        """
        indicators = self.calculate_indicators(data, current_idx)
        
        if strategy == 'ma_crossover':
            return self.moving_average_crossover_strategy(indicators)
        elif strategy == 'rsi':
            return self.rsi_strategy(indicators)
        elif strategy == 'combined':
            return self.combined_strategy(indicators)
        else:
            logger.warning(f"Unknown strategy: {strategy}")
            return None

def generate_mock_market_data(symbol: str, start_date: str, end_date: str, interval: str, 
                             volatility: float = 0.015, trend: float = 0.0001) -> List[Dict[str, Any]]:
    """
    Generate mock market data for testing.
    
    Args:
        symbol: Trading symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Time interval (1m, 5m, 15m, 1h, 4h, 1d)
        volatility: Price volatility factor
        trend: Long-term trend factor (positive for uptrend, negative for downtrend)
        
    Returns:
        List of market data points
    """
    logger.info(f"Generating mock data for {symbol} from {start_date} to {end_date} with interval {interval}")
    
    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Determine interval in minutes
    interval_minutes = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440
    }.get(interval, 60)  # Default to 1h
    
    # Generate data points
    data = []
    current_time = start
    base_price = 80000.0  # Base price for BTC
    price = base_price
    
    # Add some randomness to make it more realistic
    trend_changes = []
    for i in range(5):  # Create 5 trend change points
        change_point = start + timedelta(days=random.randint(0, (end - start).days))
        new_trend = random.uniform(-0.0005, 0.0005)
        trend_changes.append((change_point, new_trend))
    
    current_trend = trend
    
    while current_time <= end:
        # Check for trend changes
        for change_point, new_trend in trend_changes:
            if current_time.date() == change_point.date():
                current_trend = new_trend
                break
        
        # Generate price movement
        random_walk = random.normalvariate(0, 1) * volatility
        trend_component = current_trend * (1 + random.uniform(-0.5, 0.5))
        price_change = random_walk + trend_component
        
        price = price * (1 + price_change)
        
        # Calculate OHLC
        open_price = price
        high_price = price * (1 + random.uniform(0, volatility * 1.5))
        low_price = price * (1 - random.uniform(0, volatility * 1.5))
        close_price = price * (1 + random.normalvariate(0, volatility * 0.5))
        
        # Ensure high is highest and low is lowest
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)
        
        # Generate volume
        base_volume = random.uniform(100, 1000) * (price / 10000)
        
        # Add time-of-day volume pattern for intraday data
        if interval_minutes < 1440:
            hour = current_time.hour
            if 8 <= hour <= 10 or 14 <= hour <= 16:  # Market open and close hours
                base_volume *= 1.5
            elif 0 <= hour <= 5:  # Overnight hours
                base_volume *= 0.6
        
        # Add volatility-based volume
        volume = base_volume * (1 + abs(price_change) * 10)
        
        # Add data point
        data_point = {
            "symbol": symbol,
            "timestamp": current_time.isoformat(),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": round(volume, 2)
        }
        data.append(data_point)
        
        # Move to next interval
        current_time += timedelta(minutes=interval_minutes)
    
    logger.info(f"Generated {len(data)} data points")
    return data

def run_backtest(data: List[Dict[str, Any]], strategy: str = "ma_crossover", 
                initial_balance: float = 10000.0, risk_per_trade: float = 0.02) -> Dict[str, Any]:
    """
    Run a backtest on the provided data.
    
    Args:
        data: Market data
        strategy: Trading strategy to use
        initial_balance: Initial account balance
        risk_per_trade: Risk per trade as percentage of account
        
    Returns:
        Backtest results
    """
    logger.info(f"Running backtest with strategy '{strategy}', initial balance ${initial_balance}, risk {risk_per_trade:.1%}")
    
    # Initialize trader
    trader = SimpleTrader(initial_balance=initial_balance, risk_per_trade=risk_per_trade)
    
    # Use a warmup period to allow indicators to calculate properly
    warmup_period = 30
    
    # Run the backtest
    for i in range(warmup_period, len(data)):
        current_bar = data[i]
        current_price = current_bar['close']
        timestamp = current_bar['timestamp']
        
        # Update equity curve
        trader.update_equity(timestamp, current_price)
        
        # Check for exit conditions if we have an open position
        if trader.position:
            # Check for stop loss or take profit
            exit_triggered = trader.check_position_exits(current_price, timestamp)
            
            # If no exit was triggered by stops, check for signal-based exit
            if not exit_triggered:
                signal = trader.get_trading_signal(data, i, strategy)
                if (trader.position['type'] == 'long' and signal == 'sell') or \
                   (trader.position['type'] == 'short' and signal == 'buy'):
                    trader.close_position(current_price, timestamp, "signal")
        
        # Check for entry conditions if we don't have a position
        else:
            signal = trader.get_trading_signal(data, i, strategy)
            if signal == 'buy':
                trader.open_position('long', current_price, timestamp)
            elif signal == 'sell':
                trader.open_position('short', current_price, timestamp)
    
    # Close any remaining position at the end of the test
    if trader.position:
        trader.close_position(data[-1]['close'], data[-1]['timestamp'], "end_of_test")
    
    # Calculate performance metrics
    winning_trades = [t for t in trader.trades if t['profit_loss'] > 0]
    losing_trades = [t for t in trader.trades if t['profit_loss'] <= 0]
    
    # Prevent division by zero
    total_trades = len(trader.trades)
    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    
    # Calculate profit/loss statistics
    total_profit = sum(t['profit_loss'] for t in winning_trades)
    total_loss = sum(t['profit_loss'] for t in losing_trades)
    net_profit = total_profit + total_loss
    
    # Calculate average win/loss
    avg_win = total_profit / len(winning_trades) if winning_trades else 0
    avg_loss = total_loss / len(losing_trades) if losing_trades else 0
    
    # Calculate profit factor
    profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
    
    # Calculate max drawdown
    max_drawdown = 0
    peak = initial_balance
    for point in trader.equity_curve:
        if point['equity'] > peak:
            peak = point['equity']
        drawdown = (peak - point['equity']) / peak * 100
        max_drawdown = max(max_drawdown, drawdown)
    
    # Calculate Sharpe ratio (simplified)
    if len(trader.equity_curve) > 1:
        daily_returns = []
        for i in range(1, len(trader.equity_curve)):
            if trader.equity_curve[i-1]['equity'] > 0:  # Prevent division by zero
                daily_return = (trader.equity_curve[i]['equity'] - trader.equity_curve[i-1]['equity']) / trader.equity_curve[i-1]['equity']
                daily_returns.append(daily_return)
        
        if daily_returns:
            mean_return = sum(daily_returns) / len(daily_returns)
            std_dev = (sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
            sharpe_ratio = (mean_return / std_dev) * (252 ** 0.5) if std_dev > 0 else 0
        else:
            sharpe_ratio = 0
    else:
        sharpe_ratio = 0
    
    # Create results
    results = {
        "strategy": strategy,
        "initial_balance": initial_balance,
        "final_balance": trader.balance,
        "net_profit": net_profit,
        "return_pct": (net_profit / initial_balance) * 100,
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
        "equity_curve": trader.equity_curve,
        "trades": trader.trades,
        "timestamp": datetime.now().isoformat()
    }
    
    return results

def format_results(results: Dict[str, Any]) -> str:
    """
    Format results as text.
    
    Args:
        results: Dictionary with backtest results
        
    Returns:
        Formatted text
    """
    output = []
    output.append("=" * 60)
    output.append(f"BACKTEST RESULTS - {results['strategy'].upper()} STRATEGY")
    output.append("=" * 60)
    output.append(f"Initial Balance:      ${results['initial_balance']:.2f}")
    output.append(f"Final Balance:        ${results['final_balance']:.2f}")
    output.append(f"Net Profit:           ${results['net_profit']:.2f} ({results['return_pct']:.2f}%)")
    output.append(f"Total Trades:         {results['total_trades']}")
    output.append(f"Winning Trades:       {results['winning_trades']} ({results['win_rate']:.2f}%)")
    output.append(f"Losing Trades:        {results['losing_trades']} ({100-results['win_rate']:.2f}%)")
    output.append(f"Average Win:          ${results['avg_win']:.2f}")
    output.append(f"Average Loss:         ${results['avg_loss']:.2f}")
    output.append(f"Profit Factor:        {results['profit_factor']:.2f}")
    output.append(f"Maximum Drawdown:     {results['max_drawdown_pct']:.2f}%")
    output.append(f"Sharpe Ratio:         {results['sharpe_ratio']:.2f}")
    output.append("=" * 60)
    
    return "\n".join(output)

def save_results(results: Dict[str, Any], output_dir: str = "results") -> str:
    """
    Save results to a file.
    
    Args:
        results: Dictionary with backtest results
        output_dir: Directory to save results
        
    Returns:
        Path to output file
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    symbol = results.get("symbol", "BTCUSDT")
    strategy = results.get("strategy", "unknown")
    
    filename = f"{symbol}_{strategy}_backtest_{timestamp}.json"
    output_path = os.path.join(output_dir, filename)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    return output_path

def compare_strategies(data: List[Dict[str, Any]], strategies: List[str], initial_balance: float = 10000.0) -> Dict[str, Any]:
    """
    Compare multiple trading strategies.
    
    Args:
        data: Market data
        strategies: List of strategies to compare
        initial_balance: Initial account balance
        
    Returns:
        Dictionary with comparison results
    """
    logger.info(f"Comparing {len(strategies)} strategies: {', '.join(strategies)}")
    
    results = {}
    for strategy in strategies:
        logger.info(f"Testing strategy: {strategy}")
        strategy_results = run_backtest(data, strategy, initial_balance)
        results[strategy] = strategy_results
    
    # Calculate overall winner
    best_strategy = max(results.keys(), key=lambda s: results[s]['net_profit'])
    worst_strategy = min(results.keys(), key=lambda s: results[s]['net_profit'])
    
    # Create comparison
    comparison = {
        "strategies": strategies,
        "best_strategy": best_strategy,
        "worst_strategy": worst_strategy,
        "results": results,
        "summary": {
            strategy: {
                "net_profit": results[strategy]["net_profit"],
                "return_pct": results[strategy]["return_pct"],
                "win_rate": results[strategy]["win_rate"],
                "profit_factor": results[strategy]["profit_factor"],
                "sharpe_ratio": results[strategy]["sharpe_ratio"]
            } for strategy in strategies
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return comparison

def format_comparison(comparison: Dict[str, Any]) -> str:
    """
    Format strategy comparison as text.
    
    Args:
        comparison: Dictionary with comparison results
        
    Returns:
        Formatted text
    """
    output = []
    output.append("=" * 60)
    output.append("STRATEGY COMPARISON")
    output.append("=" * 60)
    
    # Add summary table
    output.append(f"{'Strategy':<15} {'Return %':<10} {'Win Rate':<10} {'Profit Factor':<15} {'Sharpe':<10}")
    output.append("-" * 60)
    
    for strategy in comparison['strategies']:
        summary = comparison['summary'][strategy]
        output.append(f"{strategy:<15} {summary['return_pct']:>9.2f}% {summary['win_rate']:>9.2f}% {summary['profit_factor']:>14.2f} {summary['sharpe_ratio']:>9.2f}")
    
    output.append("-" * 60)
    output.append(f"Best Strategy: {comparison['best_strategy']}")
    output.append(f"Worst Strategy: {comparison['worst_strategy']}")
    output.append("=" * 60)
    
    return "\n".join(output)

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run improved simplified trading test')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--interval', type=str, default='1h', help='Trading interval')
    parser.add_argument('--start_date', type=str, default='2025-02-15', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, default='2025-03-15', help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial_balance', type=float, default=10000.0, help='Initial account balance')
    parser.add_argument('--risk_per_trade', type=float, default=0.02, help='Risk per trade (e.g., 0.02 for 2%)')
    parser.add_argument('--strategy', type=str, default='ma_crossover', choices=['ma_crossover', 'rsi', 'combined'], help='Trading strategy')
    parser.add_argument('--compare', action='store_true', help='Compare all strategies')
    parser.add_argument('--output_dir', type=str, default='results', help='Output directory')
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    start_time = time.time()
    logger.info(f"Starting improved test for {args.symbol} from {args.start_date} to {args.end_date}")
    
    # Generate mock market data
    data = generate_mock_market_data(
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        interval=args.interval
    )
    
    if args.compare:
        # Compare all strategies
        strategies = ['ma_crossover', 'rsi', 'combined']
        comparison = compare_strategies(data, strategies, args.initial_balance)
        
        # Print and save comparison
        comparison_text = format_comparison(comparison)
        print(comparison_text)
        
        # Save comparison
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        comparison_file = os.path.join(args.output_dir, f"strategy_comparison_{timestamp}.json")
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        logger.info(f"Comparison saved to {comparison_file}")
    else:
        # Run backtest with single strategy
        results = run_backtest(
            data=data,
            strategy=args.strategy,
            initial_balance=args.initial_balance,
            risk_per_trade=args.risk_per_trade
        )
        
        # Save results
        output_file = save_results(results, args.output_dir)
        
        # Print formatted results
        print(format_results(results))
    
    end_time = time.time()
    logger.info(f"Test completed in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
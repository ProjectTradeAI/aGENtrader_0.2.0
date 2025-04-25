"""
Run Simplified Trading Test

This script simulates a trading test without requiring AutoGen.
It's designed to run on cloud instances with minimal dependencies.
"""

import os
import sys
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"simplified_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("simplified_test")

def generate_mock_market_data(symbol: str, start_date: str, end_date: str, interval: str) -> List[Dict[str, Any]]:
    """
    Generate mock market data for testing.
    
    Args:
        symbol: Trading symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Time interval (1m, 5m, 15m, 1h, 4h, 1d)
        
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
    
    while current_time <= end:
        # Skip weekends for traditional markets (not needed for crypto)
        # Generate price movement
        price_change = random.uniform(-0.01, 0.01)  # -1% to +1%
        price = price * (1 + price_change)
        
        # Calculate OHLC
        open_price = price
        high_price = price * random.uniform(1.0, 1.02)  # 0% to 2% higher
        low_price = price * random.uniform(0.98, 1.0)   # 0% to 2% lower
        close_price = price
        
        # Generate volume
        volume = random.uniform(100, 1000) * (price / 10000)  # Higher price, higher volume
        
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

def run_simple_backtest(data: List[Dict[str, Any]], initial_balance: float = 10000.0, risk_per_trade: float = 0.02) -> Dict[str, Any]:
    """
    Run a simple backtest on the provided data.
    
    Args:
        data: Market data
        initial_balance: Initial account balance
        risk_per_trade: Risk per trade as percentage of account
        
    Returns:
        Backtest results
    """
    logger.info(f"Running simple backtest with initial balance ${initial_balance} and risk {risk_per_trade:.1%}")
    
    balance = initial_balance
    position = None
    trades = []
    equity_curve = []
    max_balance = initial_balance
    min_balance = initial_balance
    
    # Simple moving average strategy
    short_window = 5
    long_window = 20
    
    # Only trade on a subset of the data to allow for indicators to warm up
    trading_data = data[long_window:]
    
    for i, candle in enumerate(trading_data):
        timestamp = candle['timestamp']
        current_price = candle['close']
        
        # Record equity at this point
        equity = balance if position is None else balance + position['size'] * (current_price - position['entry_price'])
        equity_curve.append({"timestamp": timestamp, "equity": equity})
        
        # Update max/min balance
        max_balance = max(max_balance, equity)
        min_balance = min(min_balance, equity)
        
        # Calculate indicators
        short_ma = sum(data[i + j]['close'] for j in range(short_window)) / short_window
        long_ma = sum(data[i + j]['close'] for j in range(long_window)) / long_window
        
        # Trading logic
        if position is None:  # No position, look for entry
            if short_ma > long_ma:  # Bullish crossover
                risk_amount = balance * risk_per_trade
                position_size = risk_amount / (current_price * 0.02)  # Assume 2% stop loss
                cost = position_size * current_price
                
                if cost <= balance:  # Ensure we have enough balance
                    position = {
                        "type": "long",
                        "entry_price": current_price,
                        "size": position_size,
                        "entry_time": timestamp,
                        "stop_loss": current_price * 0.98,  # 2% stop loss
                        "take_profit": current_price * 1.04  # 4% take profit
                    }
                    balance -= cost
                    logger.info(f"Opened LONG position at ${current_price:.2f}, size: {position_size:.4f}, balance: ${balance:.2f}")
        
        else:  # We have a position, check for exit
            if position['type'] == 'long':
                # Check stop loss or take profit
                if current_price <= position['stop_loss'] or current_price >= position['take_profit'] or short_ma < long_ma:
                    # Close position
                    exit_value = position['size'] * current_price
                    profit_loss = exit_value - (position['size'] * position['entry_price'])
                    balance += exit_value
                    
                    trade_record = {
                        "type": position['type'],
                        "entry_time": position['entry_time'],
                        "entry_price": position['entry_price'],
                        "exit_time": timestamp,
                        "exit_price": current_price,
                        "size": position['size'],
                        "profit_loss": profit_loss,
                        "profit_loss_pct": (profit_loss / (position['size'] * position['entry_price'])) * 100
                    }
                    trades.append(trade_record)
                    
                    logger.info(f"Closed LONG position at ${current_price:.2f}, P/L: ${profit_loss:.2f} ({trade_record['profit_loss_pct']:.2f}%), balance: ${balance:.2f}")
                    position = None
    
    # Calculate performance metrics
    winning_trades = [t for t in trades if t['profit_loss'] > 0]
    losing_trades = [t for t in trades if t['profit_loss'] <= 0]
    
    # Prevent division by zero
    total_trades = len(trades)
    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    
    # Final equity
    final_balance = balance if position is None else balance + position['size'] * (data[-1]['close'] - position['entry_price'])
    net_profit = final_balance - initial_balance
    return_pct = (net_profit / initial_balance) * 100
    
    # Max drawdown
    max_drawdown = 0
    peak = initial_balance
    for point in equity_curve:
        if point['equity'] > peak:
            peak = point['equity']
        drawdown = (peak - point['equity']) / peak * 100
        max_drawdown = max(max_drawdown, drawdown)
    
    # Calculate Sharpe ratio (simplified)
    daily_returns = []
    for i in range(1, len(equity_curve)):
        daily_return = (equity_curve[i]['equity'] - equity_curve[i-1]['equity']) / equity_curve[i-1]['equity']
        daily_returns.append(daily_return)
    
    if len(daily_returns) > 0:
        mean_return = sum(daily_returns) / len(daily_returns)
        std_dev = (sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
        sharpe_ratio = (mean_return / std_dev) * (252 ** 0.5) if std_dev > 0 else 0
    else:
        sharpe_ratio = 0
    
    results = {
        "initial_balance": initial_balance,
        "final_balance": final_balance,
        "net_profit": net_profit,
        "return_pct": return_pct,
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate": win_rate,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown_pct": max_drawdown,
        "equity_curve": equity_curve,
        "trades": trades,
        "timestamp": datetime.now().isoformat(),
        "output_file": f"simplified_backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    }
    
    return results

def main():
    """Main entry point"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run simplified trading test')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--interval', type=str, default='1h', help='Trading interval')
    parser.add_argument('--start_date', type=str, default='2025-02-15', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, default='2025-03-15', help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial_balance', type=float, default=10000.0, help='Initial account balance')
    parser.add_argument('--risk_per_trade', type=float, default=0.02, help='Risk per trade (e.g., 0.02 for 2%)')
    parser.add_argument('--output_dir', type=str, default='results', help='Output directory')
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    start_time = time.time()
    logger.info(f"Starting simplified test for {args.symbol} from {args.start_date} to {args.end_date}")
    
    # Generate mock market data
    data = generate_mock_market_data(
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        interval=args.interval
    )
    
    # Run backtest
    results = run_simple_backtest(
        data=data,
        initial_balance=args.initial_balance,
        risk_per_trade=args.risk_per_trade
    )
    
    # Save results
    output_file = os.path.join(
        args.output_dir,
        f"simplified_test_{args.symbol}_{args.interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    end_time = time.time()
    logger.info(f"Test completed in {end_time - start_time:.2f} seconds")
    logger.info(f"Results saved to {output_file}")
    
    # Print summary
    print("\n=== SIMPLIFIED TEST RESULTS ===")
    print(f"Symbol: {args.symbol}, Interval: {args.interval}")
    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Initial Balance: ${args.initial_balance:.2f}")
    print(f"Final Balance: ${results['final_balance']:.2f}")
    print(f"Net Profit: ${results['net_profit']:.2f} ({results['return_pct']:.2f}%)")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Winning Trades: {results['winning_trades']}")
    print(f"Losing Trades: {results['losing_trades']}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown_pct']:.2f}%")
    print("================================")

if __name__ == "__main__":
    main()
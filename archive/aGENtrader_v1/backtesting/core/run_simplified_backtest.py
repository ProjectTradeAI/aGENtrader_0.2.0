#!/usr/bin/env python3
"""
Simplified Backtesting Script

Runs a simplified paper trading simulation using the built-in mechanisms
without relying on the full decision session infrastructure.
"""

import os
import json
import sys
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Set up logging
log_dir = "data/logs/backtests"
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"{log_dir}/simplified_backtest_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def load_config(config_file: str) -> Dict[str, Any]:
    """Load backtest configuration from file"""
    with open(config_file, 'r') as f:
        return json.load(f)

def generate_demo_market_data(
    symbol: str,
    start_price: float = 50000.0,
    volatility: float = 0.02,
    num_days: int = 30,
    interval: str = "1h"
) -> List[Dict[str, Any]]:
    """
    Generate simulated market data for backtesting
    
    Args:
        symbol: Trading symbol
        start_price: Starting price
        volatility: Price volatility (standard deviation)
        num_days: Number of days to generate
        interval: Time interval
        
    Returns:
        List of market data points
    """
    import numpy as np
    from datetime import datetime, timedelta
    
    # Determine number of data points based on interval
    points_per_day = 24  # Default for 1h
    if interval == "15m":
        points_per_day = 96
    elif interval == "30m":
        points_per_day = 48
    elif interval == "1h":
        points_per_day = 24
    elif interval == "4h":
        points_per_day = 6
    elif interval == "1d":
        points_per_day = 1
    
    num_points = num_days * points_per_day
    
    # Generate price movements with some randomness and trend
    np.random.seed(42)  # For reproducibility
    returns = np.random.normal(0.0002, volatility, num_points)  # Slight upward bias
    
    # Add some trending behavior
    trend = np.sin(np.linspace(0, 4 * np.pi, num_points)) * 0.001
    returns = returns + trend
    
    # Calculate price series
    price_series = start_price * (1 + returns).cumprod()
    
    # Generate datetime series
    end_time = datetime.now()
    start_time = end_time - timedelta(days=num_days)
    
    if interval == "15m":
        time_delta = timedelta(minutes=15)
    elif interval == "30m":
        time_delta = timedelta(minutes=30)
    elif interval == "1h":
        time_delta = timedelta(hours=1)
    elif interval == "4h":
        time_delta = timedelta(hours=4)
    elif interval == "1d":
        time_delta = timedelta(days=1)
    else:
        time_delta = timedelta(hours=1)
    
    time_series = [start_time + i * time_delta for i in range(num_points)]
    
    # Create market data records
    market_data = []
    for i in range(num_points):
        price = price_series[i]
        timestamp = time_series[i]
        
        # Add some randomness to OHLC
        high_low_range = price * 0.005  # 0.5% range
        high = price + np.random.uniform(0, high_low_range)
        low = price - np.random.uniform(0, high_low_range)
        open_price = np.random.uniform(low, high)
        
        # Volume with some randomness
        volume = np.random.uniform(50, 200) * price / 1000
        
        market_data.append({
            "timestamp": timestamp.isoformat(),
            "open": float(open_price),
            "high": float(high),
            "low": float(low),
            "close": float(price),
            "volume": float(volume),
            "interval": interval,
            "symbol": symbol
        })
    
    return market_data

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    import numpy as np
    
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    
    if down == 0:
        return 100
    
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)
    
    for i in range(period, len(prices)):
        delta = deltas[i-1]
        
        if delta > 0:
            upval = delta
            downval = 0
        else:
            upval = 0
            downval = -delta
            
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        
        rs = up / down if down != 0 else float('inf')
        rsi[i] = 100. - 100. / (1. + rs)
    
    return rsi

def generate_decision(price: float, rsi: float) -> Dict[str, Any]:
    """
    Generate a simple trading decision based on RSI
    
    Args:
        price: Current price
        rsi: RSI value
        
    Returns:
        Decision dictionary
    """
    action = "HOLD"
    confidence = 50.0
    risk_level = "medium"
    reasoning = "Default HOLD decision based on neutral RSI"
    
    if rsi < 30:
        action = "BUY"
        confidence = min(100, 70 + (30 - rsi) * 2)
        reasoning = f"Oversold condition detected with RSI at {rsi:.2f}"
    elif rsi > 70:
        action = "SELL"
        confidence = min(100, 70 + (rsi - 70) * 2)
        reasoning = f"Overbought condition detected with RSI at {rsi:.2f}"
    else:
        # Adjust confidence based on proximity to oversold/overbought
        if rsi < 50:
            # Closer to oversold
            confidence = 50 - (50 - rsi)
            reasoning = f"Neutral RSI at {rsi:.2f}, slightly favoring bullish bias"
        else:
            # Closer to overbought
            confidence = 50 + (rsi - 50)
            reasoning = f"Neutral RSI at {rsi:.2f}, slightly favoring bearish bias"
    
    return {
        "action": action,
        "confidence": confidence,
        "price": price,
        "risk_level": risk_level,
        "reasoning": reasoning,
        "timestamp": datetime.now().isoformat()
    }

def run_backtest(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a simplified backtest using the specified configuration
    
    Args:
        config: Backtest configuration
        
    Returns:
        Backtest results
    """
    from agents.paper_trading import PaperTradingSystem
    
    logger.info(f"Starting simplified backtest with configuration: {json.dumps(config, indent=2)}")
    
    # Initialize paper trading system
    pts = PaperTradingSystem(
        data_dir="data/paper_trading/backtests",
        default_account_id=f"backtest_{timestamp}",
        initial_balance=config['initial_balance']
    )
    
    # Generate synthetic data for backtesting (if we can't load real data)
    try:
        from utils.market_data import get_historical_data
        historical_data = get_historical_data(
            symbol=config['symbol'],
            interval=config['interval'],
            start_time=config.get('start_date'),
            end_time=config.get('end_date')
        )
        
        if not historical_data or len(historical_data) == 0:
            logger.warning("No historical data found in database, using generated data")
            historical_data = generate_demo_market_data(
                symbol=config['symbol'],
                start_price=70000.0,
                volatility=0.02,
                num_days=30,
                interval=config['interval']
            )
    except Exception as e:
        logger.warning(f"Error loading data from database: {str(e)}. Using generated data")
        historical_data = generate_demo_market_data(
            symbol=config['symbol'],
            start_price=70000.0,
            volatility=0.02,
            num_days=30,
            interval=config['interval']
        )
    
    if not historical_data or len(historical_data) == 0:
        logger.error("No historical data found for the specified parameters")
        return {"status": "error", "message": "No historical data found"}
    
    logger.info(f"Loaded {len(historical_data)} historical data points")
    
    # Extract prices for technical indicators
    import numpy as np
    prices = np.array([d.get('close') for d in historical_data])
    
    # Calculate RSI
    rsi_values = calculate_rsi(prices)
    
    # Store metrics for each time step
    metrics = []
    decisions = []
    portfolio_values = []
    
    # Run the backtest
    logger.info("Starting backtest simulation...")
    start_time = time.time()
    
    # Skip the first few data points to have enough history for technical indicators
    start_idx = min(24, len(historical_data) // 10)
    
    for i in range(start_idx, len(historical_data), 4):  # Process every 4 hours
        current_data = historical_data[i]
        current_time = current_data.get('timestamp')
        current_price = current_data.get('close')
        current_rsi = rsi_values[i]
        
        logger.info(f"Processing data point {i} of {len(historical_data)}: {current_time} - ${current_price} - RSI: {current_rsi:.2f}")
        
        # Generate decision based on RSI
        decision = generate_decision(current_price, current_rsi)
        decisions.append(decision)
        
        # Add symbol to the decision
        decision["symbol"] = config['symbol']
        decision["current_price"] = current_price
        decision["timestamp"] = current_time
        
        # Execute decision in the paper trading system
        execution_result = pts.execute_from_decision(decision)
        
        # Get account summary
        account = pts.get_account()
        account_summary = account.get_account_summary()
        portfolio_value = account_summary.get("total_value", account.balance)
        
        portfolio_values.append({
            "timestamp": current_time,
            "price": current_price,
            "portfolio_value": portfolio_value,
            "rsi": current_rsi
        })
        
        # Record metrics for this time step
        positions = account.get_all_positions()
        metrics.append({
            "timestamp": current_time,
            "price": current_price,
            "rsi": current_rsi,
            "decision": decision.get('action'),
            "confidence": decision.get('confidence'),
            "portfolio_value": portfolio_value,
            "positions": len(positions),
            "balance": account.balance,
            "equity": portfolio_value
        })
        
        # Log progress
        if i % 20 == 0:
            logger.info(f"Backtest progress: {i}/{len(historical_data)} data points processed")
            logger.info(f"Current portfolio value: ${portfolio_value:.2f}")
            
    end_time = time.time()
    
    # Calculate performance metrics
    initial_value = config['initial_balance']
    account = pts.get_account()
    account_summary = account.get_account_summary()
    final_value = account_summary.get("total_value", account.balance)
    total_return = (final_value / initial_value - 1) * 100
    
    # Calculate drawdown
    max_value = initial_value
    max_drawdown = 0
    
    for pv in portfolio_values:
        value = pv['portfolio_value']
        max_value = max(max_value, value)
        drawdown = (max_value - value) / max_value * 100
        max_drawdown = max(max_drawdown, drawdown)
    
    # Calculate win rate
    trades = account.trades
    winning_trades = [t for t in trades if t.get('profit_loss', 0) > 0]
    win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
    
    # Get positions
    positions = account.get_all_positions()
    
    # Prepare results
    results = {
        "status": "success",
        "symbol": config['symbol'],
        "interval": config['interval'],
        "start_date": config.get('start_date'),
        "end_date": config.get('end_date'),
        "initial_balance": config['initial_balance'],
        "final_balance": account_summary.get("balance", initial_value),
        "final_equity": final_value,
        "total_return_pct": total_return,
        "max_drawdown_pct": max_drawdown,
        "trades": len(trades),
        "winning_trades": len(winning_trades),
        "win_rate": win_rate,
        "backtest_duration_seconds": end_time - start_time,
        "metrics": metrics,
        "trade_history": trades,
        "open_positions": positions
    }
    
    # Save results
    results_file = f"{log_dir}/simplified_backtest_results_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Backtest completed. Results saved to {results_file}")
    logger.info(f"Performance: Initial ${initial_value} → Final ${final_value:.2f} ({total_return:.2f}%)")
    logger.info(f"Max Drawdown: {max_drawdown:.2f}%")
    logger.info(f"Win Rate: {win_rate:.2f}% ({len(winning_trades)}/{len(trades)} trades)")
    
    return results

def run_with_different_parameters(config: Dict[str, Any], modifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run multiple backtests with different parameter sets
    
    Args:
        config: Base configuration
        modifications: List of parameter modifications
        
    Returns:
        List of backtest results
    """
    results = []
    
    for i, mods in enumerate(modifications):
        logger.info(f"Running backtest variation {i+1}/{len(modifications)}")
        
        # Create a modified config
        test_config = config.copy()
        for key, value in mods.items():
            test_config[key] = value
            
        # Run backtest with this config
        result = run_backtest(test_config)
        result["parameter_set"] = mods
        results.append(result)
        
    # Save comparison
    comparison_file = f"{log_dir}/parameter_comparison_{timestamp}.json"
    comparison_data = {
        "base_config": config,
        "results": [
            {
                "parameter_set": r.get("parameter_set"),
                "total_return_pct": r.get("total_return_pct"),
                "max_drawdown_pct": r.get("max_drawdown_pct"),
                "win_rate": r.get("win_rate"),
                "trades": r.get("trades")
            }
            for r in results
        ]
    }
    
    with open(comparison_file, 'w') as f:
        json.dump(comparison_data, f, indent=2, default=str)
        
    logger.info(f"Parameter comparison saved to {comparison_file}")
    
    return results

def main():
    """Main function"""
    if not os.path.exists("backtesting_config.json"):
        logger.error("Configuration file backtesting_config.json not found")
        return
    
    config = load_config("backtesting_config.json")
    
    # Run basic backtest
    results = run_backtest(config)
    
    # Try different parameter sets
    parameter_sets = [
        {"take_profit_pct": 3.0, "stop_loss_pct": 2.0},
        {"take_profit_pct": 8.0, "stop_loss_pct": 5.0},
        {"trade_size_pct": 10.0, "max_positions": 10},
        {"trailing_stop_pct": 1.5}
    ]
    
    variation_results = run_with_different_parameters(config, parameter_sets)
    
    logger.info("Simplified backtest process completed successfully")

if __name__ == "__main__":
    main()
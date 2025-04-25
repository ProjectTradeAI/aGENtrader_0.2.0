#!/usr/bin/env python3
"""
Simplified Backtest for Market Data Testing

This script runs a simplified backtest against the market_data table to verify
the data access and multi-agent framework integration.
"""
import os
import sys
import json
import logging
import argparse
import psycopg2
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simplified_backtest")

def get_market_data(symbol, interval, start_date, end_date):
    """Get market data from the database"""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable is not set")
        return None
    
    try:
        logger.info(f"Connecting to database: {db_url[:10]}...{db_url[-10:]}")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        logger.info(f"Fetching market data for {symbol} {interval} from {start_date} to {end_date}")
        cursor.execute("""
            SELECT 
                timestamp, open, high, low, close, volume
            FROM market_data 
            WHERE symbol=%s AND interval=%s
                AND timestamp >= %s
                AND timestamp <= %s
            ORDER BY timestamp
        """, (symbol, interval, start_date, end_date))
        
        rows = cursor.fetchall()
        logger.info(f"Retrieved {len(rows)} candles")
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            data.append({
                "timestamp": row[0].strftime("%Y-%m-%d %H:%M:%S"),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5])
            })
        
        conn.close()
        return data
    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
        return None

def run_simple_backtest(symbol, interval, start_date, end_date, initial_balance=10000):
    """Run a simple backtest using market data"""
    logger.info(f"Running backtest for {symbol} {interval} from {start_date} to {end_date}")
    
    # Get market data
    market_data = get_market_data(symbol, interval, start_date, end_date)
    if not market_data:
        logger.error("Failed to get market data")
        return None
    
    # Initialize backtest state
    balance = initial_balance
    position = 0  # 0 = cash, 1 = long
    entry_price = 0
    trades = []
    equity_curve = []
    
    # Record initial equity
    equity_curve.append({
        "timestamp": market_data[0]["timestamp"],
        "equity": balance,
        "price": market_data[0]["close"]
    })
    
    # Simple moving average strategy
    short_period = 5
    long_period = 20
    
    # Skip first 20 candles as we need enough data for moving averages
    for i in range(long_period, len(market_data)):
        # Calculate moving averages
        short_ma = sum(candle["close"] for candle in market_data[i-short_period:i]) / short_period
        long_ma = sum(candle["close"] for candle in market_data[i-long_period:i]) / long_period
        
        current_price = market_data[i]["close"]
        current_time = market_data[i]["timestamp"]
        
        # Calculate equity
        if position == 0:
            equity = balance
        else:
            # Calculate position value
            position_size = balance / entry_price
            equity = position_size * current_price
        
        # Record equity
        equity_curve.append({
            "timestamp": current_time,
            "equity": equity,
            "price": current_price
        })
        
        # Previous moving averages
        prev_short_ma = sum(candle["close"] for candle in market_data[i-short_period-1:i-1]) / short_period
        prev_long_ma = sum(candle["close"] for candle in market_data[i-long_period-1:i-1]) / long_period
        
        # Check for crossovers
        prev_short_above = prev_short_ma > prev_long_ma
        current_short_above = short_ma > long_ma
        
        # Trading logic
        if position == 0 and not prev_short_above and current_short_above:
            # Buy signal
            position = 1
            entry_price = current_price
            trades.append({
                "type": "BUY",
                "price": current_price,
                "timestamp": current_time,
                "balance": balance
            })
            logger.info(f"BUY at {current_price} ({current_time})")
        elif position == 1 and prev_short_above and not current_short_above:
            # Sell signal
            position_size = balance / entry_price
            new_balance = position_size * current_price
            pnl = (new_balance - balance) / balance * 100
            
            trades.append({
                "type": "SELL",
                "price": current_price,
                "timestamp": current_time,
                "entry_price": entry_price,
                "pnl_percentage": pnl,
                "old_balance": balance,
                "new_balance": new_balance
            })
            
            balance = new_balance
            position = 0
            logger.info(f"SELL at {current_price} ({current_time}), PnL: {pnl:.2f}%")
    
    # Close any open position at the end
    if position == 1:
        position_size = balance / entry_price
        new_balance = position_size * market_data[-1]["close"]
        pnl = (new_balance - balance) / balance * 100
        
        trades.append({
            "type": "SELL",
            "price": market_data[-1]["close"],
            "timestamp": market_data[-1]["timestamp"],
            "entry_price": entry_price,
            "pnl_percentage": pnl,
            "old_balance": balance,
            "new_balance": new_balance
        })
        
        balance = new_balance
        position = 0
        logger.info(f"Final SELL at {market_data[-1]['close']}, PnL: {pnl:.2f}%")
    
    # Calculate performance metrics
    total_pnl = (balance - initial_balance) / initial_balance * 100
    winning_trades = [t for t in trades if t.get("type") == "SELL" and t.get("pnl_percentage", 0) > 0]
    losing_trades = [t for t in trades if t.get("type") == "SELL" and t.get("pnl_percentage", 0) <= 0]
    win_rate = len(winning_trades) / max(1, len(winning_trades) + len(losing_trades)) * 100
    
    logger.info(f"Backtest completed: Balance ${balance:.2f}, PnL: {total_pnl:.2f}%")
    logger.info(f"Win rate: {win_rate:.2f}% ({len(winning_trades)}/{len(winning_trades) + len(losing_trades)})")
    
    # Compile results
    results = {
        "symbol": symbol,
        "interval": interval,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "initial_balance": initial_balance,
        "final_balance": balance,
        "total_pnl_percentage": total_pnl,
        "win_rate": win_rate,
        "total_trades": len(winning_trades) + len(losing_trades),
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "trades": trades,
        "equity_curve": equity_curve
    }
    
    # Save results
    os.makedirs("results", exist_ok=True)
    result_file = f"results/backtest_{symbol}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {result_file}")
    return results

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run a simplified backtest")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--interval", type=str, default="1h", help="Timeframe interval")
    parser.add_argument("--start_date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--initial_balance", type=float, default=10000.0, help="Initial balance")
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Parse dates
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        start_date = datetime.now() - timedelta(days=30)
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    else:
        end_date = datetime.now()
    
    # Run backtest
    result = run_simple_backtest(
        args.symbol,
        args.interval,
        start_date,
        end_date,
        args.initial_balance
    )
    
    if not result:
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

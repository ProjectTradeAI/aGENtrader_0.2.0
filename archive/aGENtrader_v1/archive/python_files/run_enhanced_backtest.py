#!/usr/bin/env python3
"""
Enhanced Backtesting Script

Runs a paper trading simulation using our enhanced multi-agent system
with both the GlobalMarketAnalyst and LiquidityAnalyst integrated.
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
log_file = f"{log_dir}/backtest_{timestamp}.log"

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

def run_backtest(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a backtest using the specified configuration
    
    Args:
        config: Backtest configuration
        
    Returns:
        Backtest results
    """
    from orchestration.decision_session import DecisionSession
    from agents.paper_trading import PaperTradingSystem
    
    logger.info(f"Starting backtest with configuration: {json.dumps(config, indent=2)}")
    
    # Initialize paper trading system
    pts = PaperTradingSystem(
        symbol=config['symbol'],
        initial_balance=config['initial_balance'],
        trade_size_percent=config['trade_size_pct'],
        max_positions=config['max_positions'],
        take_profit_percent=config['take_profit_pct'],
        stop_loss_percent=config['stop_loss_pct'],
        enable_trailing_stop=config['enable_trailing_stop'],
        trailing_stop_percent=config['trailing_stop_pct']
    )
    
    # Load historical data
    from utils.market_data import get_historical_data
    historical_data = get_historical_data(
        symbol=config['symbol'],
        interval=config['interval'],
        start_time=config.get('start_date'),
        end_time=config.get('end_date')
    )
    
    if not historical_data or len(historical_data) == 0:
        logger.error("No historical data found for the specified parameters")
        return {"status": "error", "message": "No historical data found"}
    
    logger.info(f"Loaded {len(historical_data)} historical data points")
    
    # Store metrics for each time step
    metrics = []
    decisions = []
    portfolio_values = []
    
    # Set up decision session with specialized agent configuration
    session_config = {
        "use_global_market_analyst": config.get('use_global_market_analyst', False),
        "use_liquidity_analyst": config.get('use_liquidity_analyst', False),
        "risk_level": config.get('risk_level', 'medium'),
        "session_mode": config.get('session_mode', 'agent'),
        "track_performance": True
    }
    
    # Run the backtest
    logger.info("Starting backtest simulation...")
    start_time = time.time()
    
    # Skip the first few data points to have enough history for technical indicators
    start_idx = min(24, len(historical_data) // 10)
    
    for i in range(start_idx, len(historical_data), 4):  # Process every 4 hours
        current_data = historical_data[i]
        current_time = current_data.get('timestamp')
        current_price = current_data.get('close')
        
        logger.info(f"Processing data point {i} of {len(historical_data)}: {current_time} - ${current_price}")
        
        # Create a decision session with the current data point
        decision_session = DecisionSession(
            symbol=config['symbol'],
            price=current_price,
            **session_config
        )
        
        # Make trading decision
        decision = decision_session.run_session()
        decisions.append(decision)
        
        # Process the decision in the paper trading system
        pts.process_decision(decision, current_price, current_time)
        
        # Record portfolio value
        portfolio_value = pts.get_portfolio_value(current_price)
        portfolio_values.append({
            "timestamp": current_time,
            "price": current_price,
            "portfolio_value": portfolio_value
        })
        
        # Record metrics for this time step
        metrics.append({
            "timestamp": current_time,
            "price": current_price,
            "decision": decision.get('action'),
            "confidence": decision.get('confidence'),
            "portfolio_value": portfolio_value,
            "positions": len(pts.positions),
            "balance": pts.balance,
            "equity": portfolio_value
        })
        
        # Log progress
        if i % 20 == 0:
            logger.info(f"Backtest progress: {i}/{len(historical_data)} data points processed")
            logger.info(f"Current portfolio value: ${portfolio_value:.2f}")
            
    end_time = time.time()
    
    # Calculate performance metrics
    initial_value = config['initial_balance']
    final_value = pts.get_portfolio_value(historical_data[-1].get('close'))
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
    trades = pts.get_closed_trades()
    winning_trades = [t for t in trades if t['profit_loss'] > 0]
    win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
    
    # Prepare results
    results = {
        "status": "success",
        "symbol": config['symbol'],
        "interval": config['interval'],
        "start_date": config.get('start_date'),
        "end_date": config.get('end_date'),
        "initial_balance": config['initial_balance'],
        "final_balance": pts.balance,
        "final_equity": final_value,
        "total_return_pct": total_return,
        "max_drawdown_pct": max_drawdown,
        "trades": len(trades),
        "winning_trades": len(winning_trades),
        "win_rate": win_rate,
        "backtest_duration_seconds": end_time - start_time,
        "metrics": metrics,
        "trade_history": pts.get_closed_trades(),
        "open_positions": pts.positions,
        "use_global_market_analyst": config.get('use_global_market_analyst', False),
        "use_liquidity_analyst": config.get('use_liquidity_analyst', False)
    }
    
    # Save results
    results_file = f"{log_dir}/backtest_results_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Backtest completed. Results saved to {results_file}")
    logger.info(f"Performance: Initial ${initial_value} → Final ${final_value:.2f} ({total_return:.2f}%)")
    logger.info(f"Max Drawdown: {max_drawdown:.2f}%")
    logger.info(f"Win Rate: {win_rate:.2f}% ({len(winning_trades)}/{len(trades)} trades)")
    
    return results

def run_control_backtest(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a control backtest without specialized analysts
    
    Args:
        config: Backtest configuration
        
    Returns:
        Backtest results
    """
    control_config = config.copy()
    control_config['use_global_market_analyst'] = False
    control_config['use_liquidity_analyst'] = False
    
    logger.info("Running control backtest without specialized analysts")
    return run_backtest(control_config)

def compare_results(enhanced_results: Dict[str, Any], control_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare enhanced and control backtest results
    
    Args:
        enhanced_results: Results from enhanced backtest
        control_results: Results from control backtest
        
    Returns:
        Comparison metrics
    """
    # Calculate differences
    return_difference = enhanced_results['total_return_pct'] - control_results['total_return_pct']
    drawdown_difference = control_results['max_drawdown_pct'] - enhanced_results['max_drawdown_pct']
    win_rate_difference = enhanced_results['win_rate'] - control_results['win_rate']
    
    comparison = {
        "enhanced_return": enhanced_results['total_return_pct'],
        "control_return": control_results['total_return_pct'],
        "return_difference": return_difference,
        "enhanced_drawdown": enhanced_results['max_drawdown_pct'],
        "control_drawdown": control_results['max_drawdown_pct'],
        "drawdown_improvement": drawdown_difference,
        "enhanced_win_rate": enhanced_results['win_rate'],
        "control_win_rate": control_results['win_rate'],
        "win_rate_improvement": win_rate_difference
    }
    
    # Save comparison
    comparison_file = f"{log_dir}/comparison_{timestamp}.json"
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    logger.info("=== BACKTEST COMPARISON ===")
    logger.info(f"Return: Enhanced {enhanced_results['total_return_pct']:.2f}% vs Control {control_results['total_return_pct']:.2f}% (Diff: {return_difference:.2f}%)")
    logger.info(f"Drawdown: Enhanced {enhanced_results['max_drawdown_pct']:.2f}% vs Control {control_results['max_drawdown_pct']:.2f}% (Improvement: {drawdown_difference:.2f}%)")
    logger.info(f"Win Rate: Enhanced {enhanced_results['win_rate']:.2f}% vs Control {control_results['win_rate']:.2f}% (Diff: {win_rate_difference:.2f}%)")
    
    return comparison

def main():
    """Main function"""
    if not os.path.exists("backtesting_config.json"):
        logger.error("Configuration file backtesting_config.json not found")
        return
    
    config = load_config("backtesting_config.json")
    
    # Run both enhanced and control backtests
    enhanced_results = run_backtest(config)
    
    # Run a control backtest without the specialized analysts for comparison
    control_results = run_control_backtest(config)
    
    # Compare results
    compare_results(enhanced_results, control_results)
    
    logger.info("Backtest process completed successfully")

if __name__ == "__main__":
    main()
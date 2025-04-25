"""
Quick Paper Trading Simulation

Runs a complete paper trading simulation that completes quickly for testing purposes.
It uses a simulated decision with a preset technical indicator value.
"""

import os
import sys
import json
import time
import logging
import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("quick_paper_trading")

try:
    from agents.paper_trading import PaperTradingSystem
    from orchestration.decision_session import DecisionSession
    from utils.test_logging import TestLogger
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    sys.exit(1)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run a quick paper trading simulation")
    
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading symbol (default: BTCUSDT)")
    parser.add_argument("--cycles", type=int, default=3, help="Number of trading cycles (default: 3)")
    parser.add_argument("--initial-balance", type=float, default=10000.0, help="Initial cash balance (default: 10000.0)")
    parser.add_argument("--output-dir", default="data/paper_trading_quick", help="Output directory for results (default: data/paper_trading_quick)")
    parser.add_argument("--rsi", type=float, default=25.0, help="RSI test value (default: 25.0, lower values are more bullish)")
    
    return parser.parse_args()

def get_latest_price(symbol: str) -> float:
    """Get the latest price for a trading symbol from the database"""
    try:
        from agents.database_retrieval_tool import get_latest_price as get_db_price
        import json
        
        price_json = get_db_price(symbol)
        price_data = json.loads(price_json)
        return float(price_data["close"])
    except Exception as e:
        logger.error(f"Error getting latest price: {str(e)}")
        return 0.0

def run_simulation(args):
    """Run a quick paper trading simulation"""
    # Generate a simulation ID
    sim_id = f"quick_sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Setup test logger
    test_logger = TestLogger(f"{args.output_dir}/logs", prefix="quick_sim")
    
    try:
        # Initialize paper trading system
        trading_system = PaperTradingSystem(
            data_dir=f"{args.output_dir}/{sim_id}",
            default_account_id=sim_id,
            initial_balance=args.initial_balance
        )
        
        print(f"\nPaper trading initialized with ${args.initial_balance}")
        
        # Get initial portfolio
        initial_portfolio = trading_system.get_portfolio()
        
        # Setup for cycle results
        cycle_results = []
        
        # Process each cycle
        for cycle in range(1, args.cycles + 1):
            print(f"\n{'=' * 80}")
            print(f"Starting cycle {cycle}/{args.cycles} at {datetime.now().isoformat()}")
            print(f"{'=' * 80}")
            
            cycle_start_time = datetime.now()
            
            # Get current price
            current_price = get_latest_price(args.symbol)
            print(f"Latest {args.symbol} price: ${current_price}")
            
            # Get portfolio before cycle
            portfolio_before = trading_system.get_portfolio()
            print(f"Portfolio before cycle {cycle}:")
            print(f"  Total Equity: ${portfolio_before['total_equity']}")
            print(f"  Cash Balance: ${portfolio_before['cash_balance']}")
            
            if portfolio_before["positions"]:
                print("  Positions:")
                for position in portfolio_before["positions"]:
                    print(f"    {position['symbol']}: {position['size']} @ ${position['entry_price']} (Value: ${position['current_value']})")
            
            # Initialize decision session
            session_id = f"{sim_id}_cycle{cycle}"
            decision_session = DecisionSession(
                symbol=args.symbol,
                session_id=session_id,
                config_path="config/decision_session.json"
            )
            
            print(f"Running simulated decision session for {args.symbol}...")
            
            # Create simulated session data with custom RSI value
            session_data = {
                "session_id": session_id,
                "symbol": args.symbol,
                "current_price": current_price,
                "timestamp": datetime.now().isoformat(),
                "market_data": {
                    "technical_indicators": {
                        "rsi": {"value": args.rsi}  # Use "value" key to match expected format
                    }
                }
            }
            
            # Get simulated decision
            decision = decision_session._run_simulated_session(session_data)
            
            # Ensure required fields are present
            if decision:
                decision["symbol"] = args.symbol
                decision["current_price"] = current_price
            
            if not decision:
                print("No decision generated, skipping execution")
                continue
            
            print(f"Decision: {decision['action']} {args.symbol} (Confidence: {decision['confidence']}%)")
            print(f"Reasoning: {decision['reasoning'][:100]}...")
            
            # Execute the trading decision
            print(f"\nExecuting decision in paper trading system...")
            execution_result = trading_system.execute_from_decision(decision)
            
            # Print execution result
            status = execution_result["status"]
            if status == "success":
                trade = execution_result["trade"]
                print(f"Trade executed: {trade['side']} {trade['size']} {trade['symbol']} at ${trade['entry_price']}")
                print(f"Total value: ${trade['cost']}")
            elif status == "skipped":
                print(f"Trade skipped: {execution_result['message']}")
            else:
                print(f"Trade failed: {execution_result['message']}")
            
            # Update market prices for positions in the trading system
            for position in trading_system.get_account().get_all_positions():
                symbol = position["symbol"]
                if symbol == args.symbol:
                    # Manual update of position prices
                    position["current_price"] = current_price
                    position["current_value"] = position["size"] * current_price
            
            # Get updated portfolio
            portfolio_after = trading_system.get_portfolio()
            print(f"Portfolio after cycle {cycle}:")
            print(f"  Total Equity: ${portfolio_after['total_equity']}")
            print(f"  Cash Balance: ${portfolio_after['cash_balance']}")
            
            if portfolio_after["positions"]:
                print("  Positions:")
                for position in portfolio_after["positions"]:
                    print(f"    {position['symbol']}: {position['size']} @ ${position['entry_price']} (Value: ${position['current_value']})")
            
            # Calculate cycle metrics
            cycle_equity_before = portfolio_before['total_equity']
            cycle_equity_after = portfolio_after['total_equity']
            cycle_pnl = cycle_equity_after - cycle_equity_before
            cycle_pnl_percent = (cycle_pnl / cycle_equity_before) * 100 if cycle_equity_before > 0 else 0
            
            print(f"Cycle {cycle} P&L: ${cycle_pnl:.2f} ({cycle_pnl_percent:.2f}%)")
            
            # Save cycle results
            cycle_result = {
                "cycle": cycle,
                "timestamp": datetime.now().isoformat(),
                "symbol": args.symbol,
                "price": current_price,
                "decision": decision,
                "execution_result": execution_result,
                "portfolio_before": portfolio_before,
                "portfolio_after": portfolio_after,
                "pnl": cycle_pnl,
                "pnl_percent": cycle_pnl_percent
            }
            
            cycle_results.append(cycle_result)
            
            # Save cycle results to file
            os.makedirs(f"{args.output_dir}/{sim_id}", exist_ok=True)
            with open(f"{args.output_dir}/{sim_id}/cycle_{cycle}.json", "w") as f:
                json.dump(cycle_result, f, indent=2)
            
            # Wait a moment between cycles
            time.sleep(1)
            
            # Vary the RSI value to get different decisions in each cycle
            if args.rsi < 40:
                args.rsi += 20  # Make it more neutral/bearish in the next cycle
            else:
                args.rsi = 30  # Reset to bullish
        
        # Final price update before getting portfolio
        current_price = get_latest_price(args.symbol)
        
        # Manually update position prices
        for position in trading_system.get_account().get_all_positions():
            symbol = position["symbol"]
            if symbol == args.symbol:
                position["current_price"] = current_price
                position["current_value"] = position["size"] * current_price
        
        # Get final portfolio and performance metrics
        final_portfolio = trading_system.get_portfolio()
        trades = trading_system.get_trade_history()
        metrics = trading_system.get_performance_metrics()
        
        # Calculate overall performance
        initial_equity = initial_portfolio['total_equity']
        final_equity = final_portfolio['total_equity']
        pnl = final_equity - initial_equity
        pnl_percent = (pnl / initial_equity) * 100 if initial_equity > 0 else 0
        
        print("\nSimulation completed successfully")
        print(f"Initial portfolio value: ${initial_equity}")
        print(f"Final portfolio value: ${final_equity}")
        print(f"P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
        print(f"Total trades: {len(trades)}")
        
        # Save simulation summary
        summary = {
            "id": sim_id,
            "symbol": args.symbol,
            "cycles": args.cycles,
            "cycles_completed": len(cycle_results),
            "initial_balance": args.initial_balance,
            "initial_equity": initial_equity,
            "final_equity": final_equity,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "trades_count": len(trades),
            "start_time": test_logger.timestamp,
            "end_time": datetime.now().isoformat(),
            "metrics": metrics
        }
        
        with open(f"{args.output_dir}/{sim_id}/summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        # Save full simulation data
        test_logger.save_full_session({
            "summary": summary,
            "cycles": cycle_results,
            "trades": trades,
            "final_portfolio": final_portfolio,
            "metrics": metrics
        }, f"quick_sim_{args.symbol}")
        
        print(f"Simulation results saved to {args.output_dir}/{sim_id}/")
        
        return {
            "status": "success",
            "summary": summary,
            "cycles": cycle_results
        }
    
    except Exception as e:
        logger.error(f"Error in simulation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    """Main entry point"""
    args = parse_arguments()
    
    print("\n" + "=" * 80)
    print(f" Quick Paper Trading Simulation for {args.symbol} ".center(80, "="))
    print("=" * 80 + "\n")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(f"{args.output_dir}/logs", exist_ok=True)
    
    # Run simulation
    result = run_simulation(args)
    
    if result["status"] == "success":
        print("\nQuick paper trading simulation completed successfully")
        
        summary = result["summary"]
        print(f"Symbol: {summary['symbol']}")
        print(f"Cycles completed: {summary['cycles_completed']}/{summary['cycles']}")
        print(f"P&L: ${summary['pnl']:.2f} ({summary['pnl_percent']:.2f}%)")
        print(f"Trades: {summary['trades_count']}")
    else:
        print(f"\nQuick paper trading simulation failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
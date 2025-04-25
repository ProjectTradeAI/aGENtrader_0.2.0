"""
Paper Trading Simulation Runner

Runs a complete paper trading simulation using the multi-agent system
for analysis and decision making, and the paper trading system for
trade execution.

This script can be used for:
1. Backtesting trading strategies
2. Forward testing with real-time market data
3. Evaluating agent decision quality with simulated trades
"""

import os
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
import traceback
from typing import Dict, Any, List, Optional

from utils.test_logging import TestLogger, display_header

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("paper_trading_sim")

def check_openai_api_key() -> bool:
    """Check if OpenAI API key is available"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OpenAI API key not found in environment variables.")
        print("Please set the OPENAI_API_KEY environment variable and try again.")
        return False
    return True

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run paper trading simulation")
    
    parser.add_argument(
        "--symbol", 
        type=str, 
        default="BTCUSDT",
        help="Trading symbol to simulate (default: BTCUSDT)"
    )
    
    parser.add_argument(
        "--initial-balance", 
        type=float, 
        default=10000.0,
        help="Initial account balance in USDT (default: 10000.0)"
    )
    
    parser.add_argument(
        "--cycles", 
        type=int, 
        default=3,
        help="Number of trading cycles to simulate (default: 3)"
    )
    
    parser.add_argument(
        "--cycle-interval", 
        type=int, 
        default=60,
        help="Interval between trading cycles in seconds (default: 60)"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/paper_trading_sim",
        help="Output directory for simulation results (default: data/paper_trading_sim)"
    )
    
    parser.add_argument(
        "--detailed-logging", 
        action="store_true",
        help="Enable detailed logging of agent conversations"
    )
    
    parser.add_argument(
        "--simplified", 
        action="store_true",
        help="Use simplified decision making (skip agent-based decision)"
    )
    
    return parser.parse_args()

def run_simulation(args):
    """
    Run paper trading simulation
    
    Args:
        args: Command line arguments
    """
    # Create simulation ID
    sim_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize test logger
    test_logger = TestLogger(log_dir=f"{args.output_dir}/logs", prefix=sim_id)
    
    display_header(f"Paper Trading Simulation for {args.symbol}")
    print(f"Simulation ID: {sim_id}")
    print(f"Symbol: {args.symbol}")
    print(f"Initial Balance: ${args.initial_balance}")
    print(f"Cycles: {args.cycles}")
    print(f"Cycle Interval: {args.cycle_interval} seconds")
    
    # Log simulation start
    test_logger.log_session_start("simulation", {
        "id": sim_id,
        "symbol": args.symbol,
        "initial_balance": args.initial_balance,
        "cycles": args.cycles,
        "cycle_interval": args.cycle_interval
    })
    
    try:
        # Initialize paper trading system
        from agents.paper_trading import PaperTradingSystem
        
        trading_system = PaperTradingSystem(
            data_dir=f"{args.output_dir}/{sim_id}",
            default_account_id=sim_id,
            initial_balance=args.initial_balance
        )
        
        # Get initial portfolio
        initial_portfolio = trading_system.get_portfolio()
        print(f"Paper trading initialized with ${initial_portfolio['total_equity']}")
        
        # Import decision session module
        try:
            from orchestration.decision_session import DecisionSession
            decision_module_available = True
            print("Using DecisionSession for trading decisions")
        except ImportError:
            decision_module_available = False
            print("DecisionSession module not available, using simplified collaborative test")
            from test_simplified_collaborative import test_simplified_collaborative
        
        # Run simulation cycles
        cycle_results = []
        
        for cycle in range(1, args.cycles + 1):
            cycle_start_time = datetime.now()
            print(f"\n{'='*80}")
            print(f"Starting cycle {cycle}/{args.cycles} at {cycle_start_time.isoformat()}")
            print(f"{'='*80}")
            
            # Get latest market data
            try:
                from agents.database_retrieval_tool import get_latest_price
                import json
                
                price_data_json = get_latest_price(args.symbol)
                if not price_data_json:
                    raise ValueError(f"No price data found for {args.symbol}")
                
                price_data = json.loads(price_data_json)
                current_price = price_data["close"]
                timestamp = price_data["timestamp"]
                
                print(f"Latest {args.symbol} price: ${current_price} at {timestamp}")
            except Exception as e:
                logger.error(f"Error getting market data: {str(e)}")
                print(f"Error getting market data: {str(e)}")
                continue
            
            # Get current portfolio status
            portfolio_before = trading_system.get_portfolio()
            print(f"Portfolio before cycle {cycle}:")
            print(f"  Total Equity: ${portfolio_before['total_equity']}")
            print(f"  Cash Balance: ${portfolio_before['cash_balance']}")
            
            if portfolio_before["positions"]:
                print("  Positions:")
                for position in portfolio_before["positions"]:
                    print(f"    {position['symbol']}: {position['quantity']} @ ${position['avg_price']} (Value: ${position['value']})")
            
            # Generate trading decision
            decision = None
            
            if decision_module_available:
                # Use DecisionSession for decision
                try:
                    session_id = f"{sim_id}_cycle{cycle}"
                    decision_session = DecisionSession(
                        symbol=args.symbol,
                        session_id=session_id,
                        config_path="config/decision_session.json"
                    )
                    
                    # If simplified flag is set, use the simulated session directly
                    if args.simplified:
                        print(f"Running simplified decision session for {args.symbol}...")
                        # Create simulated session with current market data and a test RSI value
                        # This will trigger the rule-based decision in the simulated session
                        session_data = {
                            "session_id": session_id,
                            "symbol": args.symbol,
                            "current_price": current_price,
                            "timestamp": datetime.now().isoformat(),
                            "market_data": {
                                "technical_indicators": {
                                    "rsi": {"rsi": 28.5}  # Low RSI to trigger BUY decision
                                }
                            }
                        }
                        decision = decision_session._run_simulated_session(session_data)
                    else:
                        print(f"Running full agent-based decision session for {args.symbol}...")
                        result = decision_session.run_session()
                        decision = result.get("decision")
                    
                    if not decision:
                        print("Decision session completed but no decision was made")
                        continue
                    
                    print(f"Decision: {decision['action']} {args.symbol} (Confidence: {decision['confidence']}%)")
                    print(f"Reasoning: {decision['reasoning'][:100]}...")
                except Exception as e:
                    logger.error(f"Error in decision session: {str(e)}")
                    print(f"Error in decision session: {str(e)}")
                    continue
            else:
                # Use simplified collaborative test for decision
                try:
                    print(f"Running simplified collaborative test for {args.symbol}...")
                    test_simplified_collaborative(args.symbol)
                    
                    # Look for the decision file in the latest log directory
                    import glob
                    
                    # Find latest session directory
                    log_dirs = sorted(glob.glob("data/logs/current_tests/sessions/collab_*_full.json"))
                    if not log_dirs:
                        print("No decision files found")
                        continue
                    
                    latest_log = log_dirs[-1]
                    
                    # Load the decision
                    with open(latest_log, "r") as f:
                        session_data = json.load(f)
                    
                    decision = session_data.get("decision")
                    
                    if not decision:
                        print("Collaborative test completed but no decision was made")
                        continue
                    
                    print(f"Decision: {decision['action']} {args.symbol} (Confidence: {decision['confidence']}%)")
                    if "reasoning" in decision:
                        print(f"Reasoning: {decision['reasoning'][:100]}...")
                except Exception as e:
                    logger.error(f"Error in collaborative test: {str(e)}")
                    print(f"Error in collaborative test: {str(e)}")
                    continue
            
            if not decision:
                print(f"No decision generated in cycle {cycle}, skipping execution")
                continue
            
            # Execute the trading decision
            print(f"\nExecuting decision in paper trading system...")
            execution_result = trading_system.execute_from_decision(decision)
            
            # Print execution result
            status = execution_result["status"]
            if status == "success":
                trade = execution_result["trade"]
                print(f"Trade executed: {trade['side']} {trade['quantity']} {trade['symbol']} at ${trade['price']}")
                print(f"Total value: ${trade['value']}")
            elif status == "skipped":
                print(f"Trade skipped: {execution_result['message']}")
            else:
                print(f"Trade failed: {execution_result['message']}")
            
            # Get updated portfolio
            portfolio_after = trading_system.get_portfolio()
            print(f"Portfolio after cycle {cycle}:")
            print(f"  Total Equity: ${portfolio_after['total_equity']}")
            print(f"  Cash Balance: ${portfolio_after['cash_balance']}")
            
            if portfolio_after["positions"]:
                print("  Positions:")
                for position in portfolio_after["positions"]:
                    print(f"    {position['symbol']}: {position['quantity']} @ ${position['avg_price']} (Value: ${position['value']})")
            
            # Calculate cycle metrics
            cycle_equity_before = portfolio_before['total_equity']
            cycle_equity_after = portfolio_after['total_equity']
            cycle_pnl = cycle_equity_after - cycle_equity_before
            cycle_pnl_percent = (cycle_pnl / cycle_equity_before) * 100 if cycle_equity_before > 0 else 0
            
            print(f"Cycle {cycle} P&L: ${cycle_pnl:.2f} ({cycle_pnl_percent:.2f}%)")
            
            # Record cycle results
            cycle_result = {
                "cycle": cycle,
                "timestamp": datetime.now().isoformat(),
                "symbol": args.symbol,
                "price": current_price,
                "decision": decision,
                "execution_result": execution_result,
                "portfolio_before": portfolio_before,
                "portfolio_after": portfolio_after,
                "equity_before": cycle_equity_before,
                "equity_after": cycle_equity_after,
                "pnl": cycle_pnl,
                "pnl_percent": cycle_pnl_percent
            }
            
            cycle_results.append(cycle_result)
            
            # Save cycle results
            cycle_output_path = f"{args.output_dir}/{sim_id}/cycle_{cycle}.json"
            os.makedirs(os.path.dirname(cycle_output_path), exist_ok=True)
            
            with open(cycle_output_path, "w") as f:
                json.dump(cycle_result, f, indent=2)
            
            # Wait for next cycle if not the last one
            if cycle < args.cycles:
                cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
                wait_time = max(0, args.cycle_interval - cycle_duration)
                
                if wait_time > 0:
                    print(f"\nWaiting {wait_time:.1f} seconds until next cycle...")
                    time.sleep(wait_time)
        
        # Get final portfolio and performance metrics
        final_portfolio = trading_system.get_portfolio()
        trades = trading_system.get_trade_history()
        metrics = trading_system.get_performance_metrics()
        
        # Calculate overall performance
        initial_equity = initial_portfolio['total_equity']
        final_equity = final_portfolio['total_equity']
        pnl = final_equity - initial_equity
        pnl_percent = (pnl / initial_equity) * 100
        
        print("\nSimulation completed successfully")
        print(f"Initial portfolio value: ${initial_equity}")
        print(f"Final portfolio value: ${final_equity}")
        print(f"P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
        print(f"Total trades: {len(trades)}")
        
        # Save simulation summary
        simulation_summary = {
            "id": sim_id,
            "symbol": args.symbol,
            "cycles": args.cycles,
            "cycle_interval": args.cycle_interval,
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
        
        summary_path = f"{args.output_dir}/{sim_id}/summary.json"
        with open(summary_path, "w") as f:
            json.dump(simulation_summary, f, indent=2)
        
        # Log simulation end
        test_logger.log_session_end("simulation", {
            "status": "success",
            "initial_equity": initial_equity,
            "final_equity": final_equity,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "trades_count": len(trades),
            "cycles_completed": len(cycle_results)
        })
        
        # Save full simulation data
        simulation_data = {
            "summary": simulation_summary,
            "cycles": cycle_results,
            "trades": trades,
            "final_portfolio": final_portfolio,
            "metrics": metrics
        }
        
        test_logger.save_full_session(simulation_data, f"simulation_{args.symbol}")
        
        print(f"Simulation results saved to {args.output_dir}/{sim_id}/")
        
        return {
            "status": "success",
            "summary": simulation_summary,
            "cycles": cycle_results
        }
    
    except Exception as e:
        logger.error(f"Error in simulation: {str(e)}")
        logger.error(traceback.format_exc())
        
        test_logger.log_session_end("simulation", {
            "status": "error",
            "error": str(e)
        })
        
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Check if OpenAI API key is available
    if not check_openai_api_key():
        return
    
    # Create output directories
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(f"{args.output_dir}/logs", exist_ok=True)
    
    # Run the simulation
    result = run_simulation(args)
    
    if result["status"] == "success":
        print("\nPaper trading simulation completed successfully")
        
        summary = result["summary"]
        print(f"Symbol: {summary['symbol']}")
        print(f"Cycles completed: {summary['cycles_completed']}/{summary['cycles']}")
        print(f"P&L: ${summary['pnl']:.2f} ({summary['pnl_percent']:.2f}%)")
        print(f"Trades: {summary['trades_count']}")
    else:
        print(f"\nPaper trading simulation failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
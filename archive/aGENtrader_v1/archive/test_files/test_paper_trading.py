"""
Paper Trading System Test

Tests the paper trading system's ability to simulate trades based on agent decisions.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import traceback

from agents.paper_trading import PaperTradingSystem, PaperTradingAccount
from utils.test_logging import TestLogger, display_header

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_paper_trading")

def test_paper_trading_basic():
    """Test basic paper trading functionality"""
    display_header("Basic Paper Trading Test")
    
    # Initialize test data directory with a unique timestamp
    test_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_data_dir = f"data/test_paper_trading_{test_time}"
    
    print(f"Initializing paper trading system in {test_data_dir}")
    
    # Initialize paper trading system
    trading_system = PaperTradingSystem(
        data_dir=test_data_dir,
        default_account_id="test_account",
        initial_balance=10000.0
    )
    
    # Get account
    account = trading_system.get_account()
    
    # Check initial state
    portfolio = trading_system.get_portfolio()
    print(f"Initial portfolio: ${portfolio['total_equity']} (Cash: ${portfolio['cash_balance']})")
    
    # Execute a buy trade
    buy_decision = {
        "action": "buy",
        "symbol": "BTCUSDT",
        "confidence": 80,
        "reasoning": "Strong uptrend detected in BTC price with increasing volume"
    }
    
    print("\nExecuting BUY decision...")
    buy_result = trading_system.execute_from_decision(buy_decision)
    
    if buy_result["status"] == "success":
        trade = buy_result["trade"]
        print(f"Trade executed: {trade['side']} {trade['quantity']} {trade['symbol']} at ${trade['price']}")
        print(f"Total value: ${trade['value']}")
    else:
        print(f"Trade failed: {buy_result['message']}")
    
    # Get updated portfolio
    portfolio = trading_system.get_portfolio()
    print(f"\nUpdated portfolio: ${portfolio['total_equity']} (Cash: ${portfolio['cash_balance']})")
    print("Positions:")
    for position in portfolio["positions"]:
        print(f"  {position['symbol']}: {position['quantity']} @ ${position['avg_price']} (Value: ${position['value']})")
    
    # Execute a sell trade
    sell_decision = {
        "action": "sell",
        "symbol": "BTCUSDT",
        "confidence": 60,
        "reasoning": "Taking partial profits after price increase"
    }
    
    print("\nExecuting SELL decision...")
    sell_result = trading_system.execute_from_decision(sell_decision)
    
    if sell_result["status"] == "success":
        trade = sell_result["trade"]
        print(f"Trade executed: {trade['side']} {trade['quantity']} {trade['symbol']} at ${trade['price']}")
        print(f"Total value: ${trade['value']}")
    else:
        print(f"Trade failed: {sell_result['message']}")
    
    # Get final portfolio
    portfolio = trading_system.get_portfolio()
    print(f"\nFinal portfolio: ${portfolio['total_equity']} (Cash: ${portfolio['cash_balance']})")
    
    if portfolio["positions"]:
        print("Remaining positions:")
        for position in portfolio["positions"]:
            print(f"  {position['symbol']}: {position['quantity']} @ ${position['avg_price']} (Value: ${position['value']})")
    else:
        print("No open positions")
    
    # Get trade history
    trades = trading_system.get_trade_history()
    print(f"\nTrade history ({len(trades)} trades):")
    for trade in trades:
        print(f"  {trade['timestamp']}: {trade['side']} {trade['quantity']} {trade['symbol']} @ ${trade['price']}")
    
    # Get performance metrics
    metrics = trading_system.get_performance_metrics()
    print(f"\nPerformance metrics:")
    print(f"  Returns: {metrics['returns']:.2f}%")
    print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"  Win Rate: {metrics['win_rate']:.2f}%")
    
    return {
        "status": "success",
        "portfolio": portfolio,
        "trades": trades,
        "metrics": metrics
    }

def test_paper_trading_with_agent_decisions(symbol: str = "BTCUSDT"):
    """
    Test paper trading with simulated agent decisions
    
    Args:
        symbol: Trading symbol to test with
    
    Returns:
        Test results dictionary
    """
    test_logger = TestLogger(log_dir="data/logs/paper_trading_tests", prefix="paper_trading")
    
    display_header(f"Paper Trading Test with Agent Decisions for {symbol}")
    test_logger.log_session_start("paper_trading", {"symbol": symbol})
    
    try:
        # Initialize paper trading system with database connection
        from agents.database_retrieval_tool import DatabaseRetrievalTool
        db_tool = DatabaseRetrievalTool()
        
        # Setup test data directory with a unique timestamp
        test_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_data_dir = f"data/test_paper_trading_{test_time}"
        
        # Initialize paper trading system
        trading_system = PaperTradingSystem(
            data_dir=test_data_dir,
            default_account_id=f"test_{symbol}",
            initial_balance=10000.0,
            db_retrieval_tool=db_tool
        )
        
        print(f"Initializing paper trading system for {symbol} in {test_data_dir}")
        
        # Get initial market data
        try:
            from agents.database_retrieval_tool import get_latest_price
            import json
            
            price_data_json = get_latest_price(symbol)
            if not price_data_json:
                raise ValueError(f"No price data found for {symbol}")
            
            price_data = json.loads(price_data_json)
            current_price = price_data["close"]
            timestamp = price_data["timestamp"]
            
            print(f"Latest {symbol} price: ${current_price} at {timestamp}")
        except Exception as e:
            logger.error(f"Error getting latest price: {str(e)}")
            test_logger.log_session_end("paper_trading", {"status": "error", "error": str(e)})
            return {"status": "error", "error": str(e)}
        
        # Get recent market data for context
        try:
            from agents.database_retrieval_tool import get_recent_market_data
            
            recent_data_json = get_recent_market_data(symbol, 10)
            if recent_data_json:
                recent_data = json.loads(recent_data_json)
                print(f"Retrieved {len(recent_data['data'])} recent data points")
            else:
                print("No recent data available")
        except Exception as e:
            logger.error(f"Error getting recent data: {str(e)}")
        
        # Create a sequence of test trading decisions based on market data
        test_decisions = [
            {
                "action": "buy",
                "symbol": symbol,
                "confidence": 85,
                "reasoning": "Strong support level identified with rising volume",
                "price": current_price,
                "timestamp": timestamp
            },
            {
                "action": "buy",
                "symbol": symbol,
                "confidence": 65,
                "reasoning": "Adding to position after price consolidation",
                "price": current_price * 1.01,  # Simulate a slight price increase
                "timestamp": timestamp
            },
            {
                "action": "sell",
                "symbol": symbol,
                "confidence": 70,
                "reasoning": "Taking partial profits at resistance level",
                "price": current_price * 1.03,  # Simulate a price increase
                "timestamp": timestamp
            },
            {
                "action": "hold",
                "symbol": symbol,
                "confidence": 55,
                "reasoning": "Market indecision, waiting for clearer signal",
                "price": current_price * 1.02,
                "timestamp": timestamp
            },
            {
                "action": "sell",
                "symbol": symbol,
                "confidence": 90,
                "reasoning": "Bearish reversal pattern detected, liquidating remaining position",
                "price": current_price * 0.99,  # Simulate a price decrease
                "timestamp": timestamp
            }
        ]
        
        # Execute each decision and record results
        results = []
        
        for i, decision in enumerate(test_decisions):
            print(f"\nExecuting decision {i+1}/{len(test_decisions)}: {decision['action']} {symbol}")
            print(f"Reasoning: {decision['reasoning']}")
            
            # Update the current price in the trading system (simulating market movement)
            if "price" in decision:
                # This hack allows us to simulate price changes for testing
                trading_system._fallback_price = lambda s: decision["price"] if s == symbol else 0
            
            # Execute the decision
            execution_result = trading_system.execute_from_decision(decision)
            results.append(execution_result)
            
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
            portfolio = trading_system.get_portfolio()
            print(f"Updated portfolio: ${portfolio['total_equity']} (Cash: ${portfolio['cash_balance']})")
            
            if portfolio["positions"]:
                print("Positions:")
                for position in portfolio["positions"]:
                    print(f"  {position['symbol']}: {position['quantity']} @ ${position['avg_price']} (Value: ${position['value']})")
        
        # Get final portfolio and performance metrics
        final_portfolio = trading_system.get_portfolio()
        trades = trading_system.get_trade_history()
        metrics = trading_system.get_performance_metrics()
        
        print("\nTest completed successfully")
        print(f"Final portfolio value: ${final_portfolio['total_equity']}")
        print(f"Total trades: {len(trades)}")
        
        # Calculate P&L
        initial_equity = 10000.0
        final_equity = final_portfolio['total_equity']
        pnl = final_equity - initial_equity
        pnl_percent = (pnl / initial_equity) * 100
        
        print(f"P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
        
        # Log session end
        test_logger.log_session_end("paper_trading", {
            "status": "success",
            "initial_equity": initial_equity,
            "final_equity": final_equity,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "trades_count": len(trades)
        })
        
        # Save full session data
        session_data = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "initial_equity": initial_equity,
            "final_equity": final_equity,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "decisions": test_decisions,
            "execution_results": results,
            "final_portfolio": final_portfolio,
            "trades": trades,
            "metrics": metrics
        }
        
        test_logger.save_full_session(session_data, f"paper_trading_{symbol}")
        
        return {
            "status": "success",
            "portfolio": final_portfolio,
            "trades": trades,
            "metrics": metrics,
            "pnl": pnl,
            "pnl_percent": pnl_percent
        }
    
    except Exception as e:
        logger.error(f"Error in paper trading test: {str(e)}")
        logger.error(traceback.format_exc())
        
        test_logger.log_session_end("paper_trading", {
            "status": "error",
            "error": str(e)
        })
        
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def test_integration_with_decision_session(symbol: str = "BTCUSDT"):
    """
    Test integration with the existing agent decision session
    
    This test demonstrates how the paper trading system integrates
    with the existing decision session to execute trades based on
    agent recommendations.
    
    Args:
        symbol: Trading symbol to test with
        
    Returns:
        Test results dictionary
    """
    test_logger = TestLogger(log_dir="data/logs/paper_trading_tests", prefix="integration")
    
    display_header(f"Paper Trading Integration Test with Decision Session for {symbol}")
    test_logger.log_session_start("integration", {"symbol": symbol})
    
    try:
        # Initialize paper trading system
        trading_system = PaperTradingSystem(
            data_dir=f"data/paper_trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            default_account_id=f"integration_{symbol}",
            initial_balance=10000.0
        )
        
        # Import decision session
        try:
            from orchestration.decision_session import DecisionSession
            
            # Initialize decision session
            decision_session = DecisionSession(
                symbol=symbol,
                session_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                config_path="config/decision_session.json"
            )
            
            print(f"Decision session initialized for {symbol}")
        except ImportError:
            # Fall back to simulated decision session
            print("Decision session module not available, using simulated decisions")
            return test_paper_trading_with_agent_decisions(symbol)
        
        # Get current market data
        try:
            from agents.database_retrieval_tool import get_latest_price
            import json
            
            price_data_json = get_latest_price(symbol)
            if not price_data_json:
                raise ValueError(f"No price data found for {symbol}")
            
            price_data = json.loads(price_data_json)
            current_price = price_data["close"]
            timestamp = price_data["timestamp"]
            
            print(f"Latest {symbol} price: ${current_price} at {timestamp}")
        except Exception as e:
            logger.error(f"Error getting latest price: {str(e)}")
            test_logger.log_session_end("integration", {"status": "error", "error": str(e)})
            return {"status": "error", "error": str(e)}
        
        # Run the decision session
        print(f"Running decision session for {symbol}...")
        
        try:
            result = decision_session.run_session()
            decision = result.get("decision")
            
            if not decision:
                print("Decision session completed but no decision was made")
                test_logger.log_session_end("integration", {"status": "incomplete", "reason": "No decision"})
                return {"status": "incomplete", "reason": "No decision"}
            
            print(f"Decision: {decision['action']} {symbol} (Confidence: {decision['confidence']}%)")
            print(f"Reasoning: {decision['reasoning'][:100]}...")
        except Exception as e:
            logger.error(f"Error running decision session: {str(e)}")
            test_logger.log_session_end("integration", {"status": "error", "error": str(e)})
            return {"status": "error", "error": str(e)}
        
        # Execute the decision in paper trading
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
        portfolio = trading_system.get_portfolio()
        print(f"Updated portfolio: ${portfolio['total_equity']} (Cash: ${portfolio['cash_balance']})")
        
        # Log session end
        test_logger.log_session_end("integration", {
            "status": "success",
            "decision": decision,
            "execution_result": execution_result,
            "portfolio": portfolio
        })
        
        # Save full session data
        session_data = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "decision_session_result": result,
            "decision": decision,
            "execution_result": execution_result,
            "portfolio": portfolio
        }
        
        test_logger.save_full_session(session_data, f"integration_{symbol}")
        
        return {
            "status": "success",
            "decision": decision,
            "execution_result": execution_result,
            "portfolio": portfolio
        }
    
    except Exception as e:
        logger.error(f"Error in integration test: {str(e)}")
        logger.error(traceback.format_exc())
        
        test_logger.log_session_end("integration", {
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
    display_header("Paper Trading System Tests")
    
    # Create test directories
    os.makedirs("data/logs/paper_trading_tests", exist_ok=True)
    os.makedirs("data/paper_trading", exist_ok=True)
    
    print("Running basic paper trading test...")
    basic_result = test_paper_trading_basic()
    
    if basic_result["status"] == "success":
        print("\nBasic paper trading test completed successfully")
        
        # Run more advanced test with agent decisions
        print("\nRunning paper trading test with agent decisions...")
        agent_result = test_paper_trading_with_agent_decisions()
        
        if agent_result["status"] == "success":
            print("\nPaper trading test with agent decisions completed successfully")
            
            # Try integration test if basic tests pass
            print("\nRunning integration test with decision session...")
            integration_result = test_integration_with_decision_session()
            
            if integration_result["status"] == "success":
                print("\nIntegration test completed successfully")
            else:
                print(f"\nIntegration test failed: {integration_result.get('error', 'Unknown error')}")
        else:
            print(f"\nPaper trading test with agent decisions failed: {agent_result.get('error', 'Unknown error')}")
    else:
        print(f"\nBasic paper trading test failed: {basic_result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
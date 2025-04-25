"""
Portfolio Risk Management Test

This script tests the portfolio management and risk analysis capabilities
of the trading system, including:

1. Risk analyzer functions (VaR, maximum position size, etc.)
2. Position sizing optimization
3. Portfolio risk analysis
4. Integration with the paper trading system

Usage:
    python test_portfolio_risk_management.py --symbol BTCUSDT --risk_tolerance 0.02 --risk_profile moderate
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("risk_management_test")

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Portfolio Risk Management Test")
    
    parser.add_argument("--symbol", type=str, default="BTCUSDT",
                      help="Trading symbol to test")
    parser.add_argument("--risk_tolerance", type=float, default=0.02,
                      help="Risk tolerance as percentage of portfolio (default: 0.02 = 2%%)")
    parser.add_argument("--risk_profile", type=str, default="moderate", 
                      choices=["conservative", "moderate", "aggressive"],
                      help="Risk profile for portfolio optimization")
    parser.add_argument("--initial_balance", type=float, default=10000.0,
                      help="Initial account balance in USDT")
    parser.add_argument("--output_dir", type=str, default="data/risk_tests",
                      help="Directory for test output")
    
    return parser.parse_args()

def check_openai_api_key() -> bool:
    """Check if OpenAI API key is available"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return False
    return True

def get_latest_price(symbol: str) -> float:
    """Get the latest price for a trading symbol from the database"""
    from agents.database_retrieval_tool import get_latest_price as get_db_latest_price
    
    try:
        # Get latest market data
        latest_price_json = get_db_latest_price(symbol=symbol)
        if latest_price_json:
            market_data = json.loads(latest_price_json)
            if market_data and "close" in market_data:
                price = float(market_data["close"])
                return price
        
        # Return a fallback price for testing if database is not available
        logger.warning(f"Could not get latest price for {symbol}, using mock price")
        if symbol == "BTCUSDT":
            return 60000.0
        elif symbol == "ETHUSDT":
            return 3000.0
        else:
            return 100.0
    except Exception as e:
        logger.error(f"Error getting latest price: {str(e)}")
        return 0.0

def test_risk_analyzer(args):
    """Test the risk analyzer component"""
    from agents.portfolio_management import RiskAnalyzer
    
    print("\n=== Testing Risk Analyzer ===\n")
    
    # Create risk analyzer with specified risk tolerance
    risk_analyzer = RiskAnalyzer(risk_tolerance=args.risk_tolerance)
    
    # Get current price for the symbol
    current_price = get_latest_price(args.symbol)
    if current_price <= 0:
        logger.error(f"Invalid price for {args.symbol}: {current_price}")
        return None
    
    print(f"Current price for {args.symbol}: ${current_price}")
    
    # Test calculate_value_at_risk
    print("\n1. Testing Value at Risk calculation:")
    position_value = args.initial_balance * 0.25  # 25% of portfolio
    var_result = risk_analyzer.calculate_value_at_risk(
        symbol=args.symbol,
        position_value=position_value,
        lookback_days=30,
        interval="1h"
    )
    
    print(f"Position value: ${position_value}")
    print(f"VaR ({var_result['confidence_level']*100:.0f}%): ${var_result['value_at_risk']:.2f}")
    print(f"VaR as percentage: {var_result['var_percentage']*100:.2f}%")
    print(f"Status: {var_result['status']}")
    
    # Test calculate_max_position_size
    print("\n2. Testing maximum position size calculation:")
    # Simulate a stop loss 5% below current price
    stop_loss = current_price * 0.95
    max_position_result = risk_analyzer.calculate_max_position_size(
        symbol=args.symbol,
        entry_price=current_price,
        stop_loss=stop_loss,
        portfolio_value=args.initial_balance
    )
    
    print(f"Entry price: ${current_price}")
    print(f"Stop loss: ${stop_loss}")
    print(f"Max position size: ${max_position_result['max_position_size']:.2f}")
    print(f"Max quantity: {max_position_result['max_quantity']:.6f}")
    print(f"Risk amount: ${max_position_result['risk_amount']:.2f}")
    print(f"Status: {max_position_result['status']}")
    
    # Test calculate_kelly_position_size
    print("\n3. Testing Kelly criterion position sizing:")
    win_rate = 0.6  # 60% win rate
    risk_reward_ratio = 2.0  # 1:2 risk:reward
    kelly_result = risk_analyzer.calculate_kelly_position_size(
        win_rate=win_rate,
        risk_reward_ratio=risk_reward_ratio,
        portfolio_value=args.initial_balance
    )
    
    print(f"Win rate: {win_rate*100:.0f}%")
    print(f"Risk:reward ratio: 1:{risk_reward_ratio}")
    print(f"Kelly percentage: {kelly_result['kelly_percentage']*100:.2f}%")
    print(f"Capped Kelly: {kelly_result['capped_kelly']*100:.2f}%")
    print(f"Position size: ${kelly_result['position_size']:.2f}")
    print(f"Status: {kelly_result['status']}")
    
    # Test calculate_volatility_adjusted_size
    print("\n4. Testing volatility-adjusted position sizing:")
    vol_result = risk_analyzer.calculate_volatility_adjusted_size(
        symbol=args.symbol,
        portfolio_value=args.initial_balance,
        lookback_days=30,
        target_volatility=0.01  # Target 1% daily volatility
    )
    
    print(f"Daily volatility: {vol_result['daily_volatility']*100:.4f}%")
    print(f"Target volatility: {vol_result['target_volatility']*100:.2f}%")
    print(f"Volatility ratio: {vol_result['volatility_ratio']:.4f}")
    print(f"Position size: ${vol_result['position_size']:.2f}")
    print(f"Status: {vol_result['status']}")
    
    return {
        "var_result": var_result,
        "max_position_result": max_position_result,
        "kelly_result": kelly_result,
        "vol_result": vol_result
    }

def test_portfolio_manager(args, initial_portfolio=None):
    """Test the portfolio manager component"""
    from agents.portfolio_management import PortfolioManager, RiskAnalyzer
    
    print("\n=== Testing Portfolio Manager ===\n")
    
    # Create risk analyzer and portfolio manager
    risk_analyzer = RiskAnalyzer(risk_tolerance=args.risk_tolerance)
    portfolio_manager = PortfolioManager(risk_analyzer=risk_analyzer)
    
    # Get current price for the symbol
    current_price = get_latest_price(args.symbol)
    if current_price <= 0:
        logger.error(f"Invalid price for {args.symbol}: {current_price}")
        return None
    
    # Create initial portfolio if not provided
    if initial_portfolio is None:
        initial_portfolio = {
            "cash_balance": args.initial_balance * 0.7,  # 70% cash
            "positions": [
                {
                    "symbol": args.symbol,
                    "quantity": (args.initial_balance * 0.3) / current_price,
                    "avg_price": current_price * 0.95,  # Simulated entry 5% lower
                    "current_price": current_price,
                    "value": (args.initial_balance * 0.3)
                }
            ],
            "total_equity": args.initial_balance
        }
    
    print(f"Initial portfolio:")
    print(f"  Cash balance: ${initial_portfolio['cash_balance']:.2f}")
    print(f"  Total equity: ${initial_portfolio['total_equity']:.2f}")
    print(f"  Positions:")
    for position in initial_portfolio["positions"]:
        print(f"    {position['symbol']}: {position['quantity']:.6f} @ ${position['avg_price']:.2f} (Value: ${position['value']:.2f})")
    
    # Test analyze_portfolio_risk
    print("\n1. Testing portfolio risk analysis:")
    risk_analysis = risk_analyzer.analyze_portfolio_risk(initial_portfolio)
    
    print(f"Cash ratio: {risk_analysis['cash_ratio']*100:.2f}%")
    print(f"Position count: {risk_analysis.get('position_count', 0)}")
    print(f"Largest position ratio: {risk_analysis['largest_position_ratio']*100:.2f}%")
    print(f"Risk concentration: {risk_analysis['risk_concentration']*100:.2f}%")
    print(f"Diversification score: {risk_analysis['diversification_score']*100:.2f}%")
    print(f"Status: {risk_analysis['status']}")
    
    # Test get_optimal_position_size
    print("\n2. Testing optimal position sizing:")
    # Simulate a stop loss 5% below current price
    stop_loss = current_price * 0.95
    win_probability = 0.6  # 60% win probability
    risk_reward_ratio = 2.0  # 1:2 risk:reward
    
    position_result = portfolio_manager.get_optimal_position_size(
        symbol=args.symbol,
        entry_price=current_price,
        stop_loss=stop_loss,
        portfolio=initial_portfolio,
        win_probability=win_probability,
        risk_reward_ratio=risk_reward_ratio
    )
    
    print(f"Entry price: ${current_price}")
    print(f"Stop loss: ${stop_loss}")
    print(f"Win probability: {win_probability*100:.0f}%")
    print(f"Risk:reward ratio: 1:{risk_reward_ratio}")
    print(f"Optimal position size: ${position_result['position_size']:.2f}")
    print(f"Quantity: {position_result['quantity']:.6f}")
    print(f"Position as % of portfolio: {position_result['position_value_percentage']*100:.2f}%")
    print(f"Status: {position_result['status']}")
    
    # Show sizing details
    print("\nPosition sizing details:")
    details = position_result["sizing_details"]
    print(f"  Risk-based size: ${details['risk_based_size']:.2f}")
    print(f"  Kelly size: ${details['kelly_size']:.2f}")
    print(f"  Volatility size: ${details['volatility_size']:.2f}")
    print(f"  Weighted size: ${details['weighted_size']:.2f}")
    print(f"  Max size by cash: ${details['max_size_by_cash']:.2f}")
    print(f"  Max size by concentration: ${details['max_size_by_concentration']:.2f}")
    
    # Test optimize_portfolio
    print("\n3. Testing portfolio optimization:")
    optimization = portfolio_manager.optimize_portfolio(
        portfolio=initial_portfolio,
        risk_profile=args.risk_profile
    )
    
    print(f"Risk profile: {args.risk_profile}")
    if "current_cash_ratio" in optimization:
        print(f"Current cash ratio: {optimization['current_cash_ratio']*100:.2f}%")
    if "target_cash_ratio" in optimization:
        print(f"Target cash ratio: {optimization['target_cash_ratio']*100:.2f}%")
    
    print("\nRecommendations:")
    if "recommendations" in optimization:
        for rec in optimization["recommendations"]:
            if "message" in rec:
                print(f"  {rec['message']}")
            elif "action" in rec and "symbol" in rec:
                print(f"  {rec['action']} {rec['symbol']}: {rec.get('description', '')}")
    
    return {
        "risk_analysis": risk_analysis,
        "position_result": position_result,
        "optimization": optimization
    }

def test_paper_trading_integration(args):
    """Test integration with paper trading system"""
    from agents.paper_trading import PaperTradingSystem
    from orchestration.risk_optimizer import RiskOptimizer
    
    print("\n=== Testing Integration with Paper Trading ===\n")
    
    # Create paper trading system
    trading_system = PaperTradingSystem(data_dir=args.output_dir)
    
    # Initialize account with custom balance
    account = trading_system.create_account(
        account_id=f"risk_test_{int(time.time())}",
        initial_balance=args.initial_balance
    )
    
    print(f"Created test account: {account.account_id}")
    print(f"Initial balance: ${account.get_balance('USDT')}")
    
    # Get current portfolio state before trade
    portfolio_before = trading_system.get_portfolio(account.account_id)
    
    print("\nInitial portfolio:")
    print(f"  Cash balance: ${portfolio_before['cash_balance']:.2f}")
    print(f"  Total equity: ${portfolio_before['total_equity']:.2f}")
    
    # Get current price for the symbol
    current_price = get_latest_price(args.symbol)
    if current_price <= 0:
        logger.error(f"Invalid price for {args.symbol}: {current_price}")
        return None
    
    print(f"\nCurrent price for {args.symbol}: ${current_price}")
    
    # Create a trading decision
    decision = {
        "symbol": args.symbol,
        "action": "buy",
        "entry_price": current_price,
        "confidence": 0.8,  # 80% confidence
        "stop_loss": current_price * 0.95,  # 5% stop loss
        "take_profit": current_price * 1.15  # 15% take profit
    }
    
    print("\n1. Testing risk-optimized trade execution:")
    print(f"Decision: {json.dumps(decision, indent=2)}")
    
    # Execute the decision with risk optimization
    result = trading_system.execute_from_decision(
        decision=decision,
        account_id=account.account_id,
        use_risk_optimizer=True
    )
    
    print(f"\nExecution result: {result['status']}")
    print(f"Message: {result['message']}")
    
    if result['status'] == 'success':
        print("\nTrade details:")
        trade = result['trade']
        print(f"  Symbol: {trade['symbol']}")
        print(f"  Side: {trade['side']}")
        print(f"  Quantity: {trade['quantity']}")
        print(f"  Price: ${trade['price']}")
        print(f"  Value: ${trade['value']:.2f}")
        
        if 'metadata' in trade:
            print("\nRisk parameters:")
            metadata = trade['metadata']
            if 'stop_loss' in metadata:
                print(f"  Stop Loss: ${metadata['stop_loss']}")
            if 'take_profit' in metadata:
                print(f"  Take Profit: ${metadata['take_profit']}")
    
    # Get updated portfolio after trade
    portfolio_after = trading_system.get_portfolio(account.account_id)
    
    print("\nUpdated portfolio:")
    print(f"  Cash balance: ${portfolio_after['cash_balance']:.2f}")
    print(f"  Total equity: ${portfolio_after['total_equity']:.2f}")
    print(f"  Positions:")
    for position in portfolio_after["positions"]:
        print(f"    {position['symbol']}: {position['quantity']:.6f} @ ${position['avg_price']:.2f} (Value: ${position['value']:.2f})")
    
    # Test portfolio optimization
    print("\n2. Testing full portfolio optimization:")
    from agents.portfolio_management import PortfolioManager
    
    # Create portfolio manager
    portfolio_manager = PortfolioManager(risk_tolerance=args.risk_tolerance)
    
    # Get optimization recommendations
    optimization = portfolio_manager.optimize_portfolio(
        portfolio=portfolio_after,
        risk_profile=args.risk_profile
    )
    
    print(f"Risk profile: {args.risk_profile}")
    if "current_cash_ratio" in optimization:
        print(f"Current cash ratio: {optimization['current_cash_ratio']*100:.2f}%")
    if "target_cash_ratio" in optimization:
        print(f"Target cash ratio: {optimization['target_cash_ratio']*100:.2f}%")
    
    print("\nRecommendations:")
    if "recommendations" in optimization:
        for rec in optimization["recommendations"]:
            if "message" in rec:
                print(f"  {rec['message']}")
            elif "action" in rec and "symbol" in rec:
                print(f"  {rec['action']} {rec['symbol']}: {rec.get('description', '')}")
    
    # Test position adjustment
    if portfolio_after["positions"]:
        print("\n3. Testing position adjustment calculation:")
        position = portfolio_after["positions"][0]
        
        adjustment = portfolio_manager.get_position_adjustment(
            symbol=position["symbol"],
            current_price=current_price,
            current_position=position,
            portfolio=portfolio_after,
            target_allocation=0.2  # Target 20% allocation
        )
        
        print(f"Symbol: {position['symbol']}")
        print(f"Current allocation: {adjustment['current_allocation']*100:.2f}%")
        print(f"Target allocation: {adjustment['target_allocation']*100:.2f}%")
        print(f"Recommended action: {adjustment['action']}")
        print(f"Adjustment amount: ${adjustment['adjustment_value']:.2f}")
        if adjustment['action'] != 'hold':
            print(f"Quantity to {adjustment['action']}: {abs(adjustment['quantity']):.6f}")
    
    return {
        "execution_result": result,
        "portfolio_after": portfolio_after,
        "optimization": optimization
    }

def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Configure file handler for logging
    log_file = os.path.join(args.output_dir, f"risk_test_{int(time.time())}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
    
    # Log test parameters
    logger.info(f"Starting portfolio risk management test with parameters:")
    logger.info(f"  Symbol: {args.symbol}")
    logger.info(f"  Risk tolerance: {args.risk_tolerance}")
    logger.info(f"  Risk profile: {args.risk_profile}")
    logger.info(f"  Initial balance: {args.initial_balance}")
    
    try:
        # Test individual components
        print("\n=== Portfolio Risk Management Test ===")
        print(f"Symbol: {args.symbol}")
        print(f"Risk tolerance: {args.risk_tolerance*100:.0f}%")
        print(f"Risk profile: {args.risk_profile}")
        print(f"Initial balance: ${args.initial_balance}")
        
        # Test risk analyzer
        risk_analyzer_results = test_risk_analyzer(args)
        
        # Test portfolio manager
        portfolio_manager_results = test_portfolio_manager(args)
        
        # Test paper trading integration
        paper_trading_results = test_paper_trading_integration(args)
        
        # Save results to file
        results = {
            "parameters": {
                "symbol": args.symbol,
                "risk_tolerance": args.risk_tolerance,
                "risk_profile": args.risk_profile,
                "initial_balance": args.initial_balance
            },
            "risk_analyzer_results": risk_analyzer_results,
            "portfolio_manager_results": portfolio_manager_results,
            "paper_trading_results": paper_trading_results,
            "timestamp": time.time()
        }
        
        results_file = os.path.join(args.output_dir, f"risk_test_results_{int(time.time())}.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nTest completed successfully. Results saved to {results_file}")
        logger.info(f"Test completed successfully. Results saved to {results_file}")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\nTest failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
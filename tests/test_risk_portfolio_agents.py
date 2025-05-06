"""
Test script for RiskGuardAgent and PortfolioManagerAgent
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import the agents
from agents.portfolio_manager_agent import PortfolioManagerAgent
from agents.risk_guard_agent import RiskGuardAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_portfolio_manager():
    """Test PortfolioManagerAgent functionality"""
    logger.info("Testing PortfolioManagerAgent")
    
    # Initialize the agent
    portfolio_manager = PortfolioManagerAgent()
    
    # Get portfolio summary
    summary = portfolio_manager.get_portfolio_summary()
    logger.info(f"Portfolio summary: {json.dumps(summary, indent=2)}")
    
    # Create a test trade
    test_trade = {
        'trade_id': f"TEST-{int(datetime.now().timestamp())}",
        'pair': 'BTC/USDT',
        'action': 'BUY',
        'entry_price': 50000,
        'position_size': 0.1,
        'stop_loss': 48000,
        'take_profit': 55000,
        'timestamp': datetime.now().isoformat(),
        'status': 'open'
    }
    
    # Validate the trade
    validation = portfolio_manager.validate_trade(test_trade)
    logger.info(f"Trade validation: {json.dumps(validation, indent=2)}")
    
    # Run the agent
    result = portfolio_manager.run(trade_data=test_trade, take_snapshot=True)
    logger.info(f"Portfolio manager run result: {json.dumps(result, indent=2)}")
    
    # Analyze portfolio
    analysis = portfolio_manager.analyze()
    logger.info(f"Portfolio analysis: {json.dumps(analysis, indent=2)}")
    
    return True

def test_risk_guard():
    """Test RiskGuardAgent functionality"""
    logger.info("Testing RiskGuardAgent")
    
    # Initialize the agent
    risk_guard = RiskGuardAgent()
    
    # Example market data
    market_data = {
        "symbol": "BTC/USDT",
        "current_price": 50000,
        "volatility": {
            "value": 2.5,
            "period": "24h"
        },
        "volume": 1000000,
        "volume_trend": {
            "change_pct": -20
        },
        "liquidity": {
            "bid_ask_spread_pct": 0.1,
            "depth": 500000
        }
    }
    
    # Example portfolio data
    portfolio_data = {
        "portfolio_value": 10000,
        "total_exposure_pct": 30,
        "max_total_exposure_pct": 80,
        "asset_exposures": {
            "BTC/USDT": 10
        }
    }
    
    # Example trade plan
    trade_plan = {
        "symbol": "BTC/USDT",
        "signal": "BUY",
        "entry_price": 50000,
        "stop_loss": 48000,
        "take_profit": 55000,
        "position_size": 0.1,
        "confidence": 75
    }
    
    # Test market risk assessment
    market_risk = risk_guard.evaluate_market_risk(market_data)
    logger.info(f"Market risk assessment: {json.dumps(market_risk, indent=2)}")
    
    # Test position risk assessment
    position_risk = risk_guard.evaluate_position_risk(trade_plan, portfolio_data)
    logger.info(f"Position risk assessment: {json.dumps(position_risk, indent=2)}")
    
    # Test drawdown risk assessment
    drawdown_risk = risk_guard.evaluate_drawdown_risk(trade_plan)
    logger.info(f"Drawdown risk assessment: {json.dumps(drawdown_risk, indent=2)}")
    
    # Run the risk guard agent
    result = risk_guard.run(
        trade_plan=trade_plan,
        market_data=market_data,
        portfolio_data=portfolio_data
    )
    logger.info(f"Risk guard run result: {json.dumps(result, indent=2)}")
    
    # Test risk analysis
    analysis = risk_guard.analyze(symbol="BTC/USDT", market_data=market_data)
    logger.info(f"Risk analysis: {json.dumps(analysis, indent=2)}")
    
    return True

def test_integration():
    """Test integration between portfolio manager and risk guard"""
    logger.info("Testing Portfolio Manager and Risk Guard integration")
    
    # Initialize the agents
    portfolio_manager = PortfolioManagerAgent()
    risk_guard = RiskGuardAgent()
    
    # Example market data
    market_data = {
        "symbol": "BTC/USDT",
        "current_price": 50000,
        "volatility": {
            "value": 4.5,  # High volatility to trigger risk adjustment
            "period": "24h"
        },
        "volume": 1000000,
        "volume_trend": {
            "change_pct": -35  # Significant volume decrease to trigger risk
        },
        "liquidity": {
            "bid_ask_spread_pct": 0.3,  # Moderate to high spread
            "depth": 300000
        }
    }
    
    # Example trade plan with large position size (to trigger risk adjustment)
    trade_plan = {
        "symbol": "BTC/USDT",
        "signal": "BUY",
        "entry_price": 50000,
        "stop_loss": 47500,
        "take_profit": 55000,
        "position_size": 0.2,  # Larger position size
        "confidence": 75
    }
    
    # Get current portfolio state
    portfolio_state = portfolio_manager.get_portfolio_summary()
    
    # Run risk assessment
    risk_result = risk_guard.run(
        trade_plan=trade_plan,
        market_data=market_data,
        portfolio_data=portfolio_state
    )
    logger.info(f"Risk assessment: {json.dumps(risk_result, indent=2)}")
    
    # Get adjusted trade plan
    adjusted_trade_plan = risk_result.get('adjusted_trade_plan', {})
    
    # If adjustments were made, log them
    if adjusted_trade_plan.get('risk_assessment', {}).get('adjustments_made', False):
        logger.info("Risk adjustments were made to the trade plan")
        logger.info(f"Original position size: {adjusted_trade_plan['risk_assessment']['original_position_size']}")
        logger.info(f"Adjusted position size: {adjusted_trade_plan['risk_assessment']['adjusted_position_size']}")
        
        # Create a trade from the adjusted trade plan
        trade = {
            'trade_id': f"TEST-{int(datetime.now().timestamp())}",
            'pair': adjusted_trade_plan.get('symbol'),
            'action': adjusted_trade_plan.get('signal'),
            'entry_price': adjusted_trade_plan.get('entry_price'),
            'position_size': adjusted_trade_plan.get('position_size'),
            'stop_loss': adjusted_trade_plan.get('stop_loss'),
            'take_profit': adjusted_trade_plan.get('take_profit'),
            'timestamp': datetime.now().isoformat(),
            'status': 'open'
        }
    else:
        logger.info("No risk adjustments were needed for the trade plan")
        # Create a trade from the original trade plan
        trade = {
            'trade_id': f"TEST-{int(datetime.now().timestamp())}",
            'pair': trade_plan.get('symbol'),
            'action': trade_plan.get('signal'),
            'entry_price': trade_plan.get('entry_price'),
            'position_size': trade_plan.get('position_size'),
            'stop_loss': trade_plan.get('stop_loss'),
            'take_profit': trade_plan.get('take_profit'),
            'timestamp': datetime.now().isoformat(),
            'status': 'open'
        }
    
    # Process the trade with the portfolio manager
    pm_result = portfolio_manager.run(trade_data=trade, take_snapshot=True)
    logger.info(f"Portfolio manager result: {json.dumps(pm_result, indent=2)}")
    
    # Get updated portfolio state
    updated_portfolio = portfolio_manager.get_portfolio_summary()
    logger.info(f"Updated portfolio: {json.dumps(updated_portfolio, indent=2)}")
    
    return True

if __name__ == "__main__":
    logger.info("Starting tests for PortfolioManagerAgent and RiskGuardAgent")
    
    try:
        # Test portfolio manager
        test_portfolio_manager()
        
        # Test risk guard
        test_risk_guard()
        
        # Test integration
        test_integration()
        
        logger.info("All tests completed successfully")
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}", exc_info=True)
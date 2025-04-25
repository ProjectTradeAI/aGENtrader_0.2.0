"""
Test script for error handling in aGENtrader v2

This script demonstrates and tests the error handling capabilities in the aGENtrader v2 system,
including API retries, data validation, fallback mechanisms, and graceful degradation.
"""

import os
import sys
import time
import json
import random
from typing import Dict, Any, List

# Add the parent directory to the path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import utilities and agents
from utils.logger import get_logger
from utils.config import get_config
from utils.error_handler import (
    DataFetchingError, 
    ValidationError, 
    RetryExhaustedError,
    MockDataFallbackError,
    TradeExecutionError
)

# Import agents for testing
from agents.technical_analyst_agent import TechnicalAnalystAgent
from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from agents.sentiment_analyst_agent import SentimentAnalystAgent
from agents.portfolio_manager_agent import PortfolioManagerAgent
from agents.risk_guard_agent import RiskGuardAgent
from agents.position_sizer_agent import PositionSizerAgent
from agents.trade_executor_agent import TradeExecutorAgent

# Get logger and config
logger = get_logger("test_error_handling")
config = get_config()

def print_section_header(title: str) -> None:
    """Print a section header with formatting."""
    width = 80
    print("\n" + "=" * width)
    print(f"{title.center(width)}")
    print("=" * width + "\n")

def test_data_fetching_retries() -> None:
    """Test automatic retries when fetching data."""
    print_section_header("Testing Data Fetching Retries")
    
    # Create a Technical Analyst Agent for testing
    agent = TechnicalAnalystAgent()
    
    # Create a mock data source that fails a certain number of times then succeeds
    class MockFailingDataSource:
        def __init__(self, fail_count: int = 2):
            self.fail_count = fail_count
            self.current_attempt = 0
            
        def fetch_data(self, symbol: str, interval: str):
            self.current_attempt += 1
            if self.current_attempt <= self.fail_count:
                logger.warning(f"Mock data source failing on attempt {self.current_attempt}")
                raise ConnectionError(f"Mock connection error (attempt {self.current_attempt})")
            logger.info(f"Mock data source succeeding on attempt {self.current_attempt}")
            return {"price": 50000, "volume": 100, "timestamp": "2025-04-20T12:00:00Z"}
            
    # Create the mock data source
    data_source = MockFailingDataSource(fail_count=2)
    
    # Test the retry mechanism
    try:
        print(f"Fetching data with retry (expected to succeed after {data_source.fail_count} failures)...")
        result = agent.fetch_data_with_retry(data_source.fetch_data, "BTC/USDT", "1h")
        print(f"SUCCESS: Data retrieved after {data_source.current_attempt} attempts: {result}")
    except Exception as e:
        print(f"ERROR: Retry mechanism failed - {e}")
        
    # Now test with too many failures
    data_source = MockFailingDataSource(fail_count=5)  # More than max_retries
    try:
        print(f"Fetching data with retry (expected to fail after {agent.max_retries} attempts)...")
        result = agent.fetch_data_with_retry(data_source.fetch_data, "BTC/USDT", "1h")
        print(f"UNEXPECTED SUCCESS: {result}")
    except RetryExhaustedError as e:
        print(f"SUCCESS: Retry exhausted properly: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected exception type: {type(e)}: {e}")

def test_mock_fallback() -> None:
    """Test fallback to mock data when real data is unavailable."""
    print_section_header("Testing Mock Data Fallback")
    
    # Create a Technical Analyst Agent for testing
    agent = TechnicalAnalystAgent()
    
    # Define a function that always fails
    def failing_fetch(symbol: str, interval: str):
        raise ConnectionError("Simulated connection error in fetch")
        
    # Define a mock fallback function
    def mock_fallback(symbol: str, interval: str):
        return {
            "symbol": symbol,
            "interval": interval,
            "timestamp": agent.format_timestamp(),
            "action": "HOLD",
            "confidence": 50,
            "analysis": {
                "mock": True,
                "indicators": {"rsi": 50, "macd": 0}
            }
        }
    
    # Test with fallback allowed
    print("Testing with fallback allowed...")
    result = agent.handle_data_fetching_error(
        error=ConnectionError("Simulated error"),
        symbol="BTC/USDT",
        interval="1h",
        fallback_method=mock_fallback,
        allow_fallback=True
    )
    
    if "data_source" in result and result["data_source"] == "fallback":
        print(f"SUCCESS: Properly fell back to mock data with warning: {result.get('warning')}")
    else:
        print(f"ERROR: Failed to use fallback data correctly: {result}")
        
    # Test with fallback not allowed
    print("\nTesting with fallback NOT allowed...")
    result = agent.handle_data_fetching_error(
        error=ConnectionError("Simulated error"),
        symbol="BTC/USDT",
        interval="1h",
        fallback_method=mock_fallback,
        allow_fallback=False
    )
    
    if "error" in result and result["error"] is True:
        print(f"SUCCESS: Correctly returned error response without using fallback: {result['message']}")
    else:
        print(f"ERROR: Unexpectedly used fallback when not allowed: {result}")

def test_input_validation() -> None:
    """Test input validation for analyst agents."""
    print_section_header("Testing Input Validation")
    
    # Create a Sentiment Analyst Agent for testing
    agent = SentimentAnalystAgent()
    
    # Test with missing required field
    try:
        print("Testing with missing required field...")
        result = agent.validate_input_data(
            symbol="BTC/USDT",
            interval="1h",
            required_fields=["sentiment_score"],
            some_param="test"
        )
        print(f"UNEXPECTED SUCCESS: {result}")
    except ValidationError as e:
        print(f"SUCCESS: Correctly detected missing required field: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected exception type: {type(e)}: {e}")
        
    # Test with all required fields
    try:
        print("\nTesting with all required fields...")
        result = agent.validate_input_data(
            symbol="BTC/USDT",
            interval="1h",
            required_fields=["sentiment_score"],
            sentiment_score=0.75,
            some_param="test"
        )
        print(f"SUCCESS: Validated input data: {result}")
    except Exception as e:
        print(f"ERROR: Validation failed unexpectedly: {e}")
        
    # Test with missing symbol and interval (should use defaults)
    try:
        print("\nTesting with missing symbol and interval...")
        result = agent.validate_input_data(
            symbol=None,
            interval=None,
            some_param="test"
        )
        print(f"SUCCESS: Used default values: {result}")
        print(f"Default symbol: {result['symbol']}, Default interval: {result['interval']}")
    except Exception as e:
        print(f"ERROR: Failed to use defaults: {e}")

def test_trade_validation() -> None:
    """Test trade data validation."""
    print_section_header("Testing Trade Data Validation")
    
    # Import validation function
    from utils.error_handler import validate_trade_data
    
    # Test valid trade data
    valid_trade = {
        "pair": "BTC/USDT",
        "action": "BUY",
        "confidence": 75,
        "price": 50000
    }
    
    # Test invalid trade data
    invalid_trades = [
        # Missing pair
        {"action": "SELL", "confidence": 80},
        # Missing action
        {"pair": "ETH/USDT", "confidence": 70},
        # Invalid action
        {"pair": "BTC/USDT", "action": "INVALID", "confidence": 65},
        # Invalid confidence
        {"pair": "BTC/USDT", "action": "BUY", "confidence": "high"}
    ]
    
    # Test valid trade
    try:
        print("Testing valid trade data...")
        validate_trade_data(valid_trade)
        print(f"SUCCESS: Valid trade passed validation: {valid_trade}")
    except ValidationError as e:
        print(f"ERROR: Valid trade failed validation: {e}")
    
    # Test invalid trades
    for i, trade in enumerate(invalid_trades):
        try:
            print(f"\nTesting invalid trade #{i+1}: {trade}...")
            validate_trade_data(trade)
            print(f"ERROR: Invalid trade passed validation unexpectedly")
        except ValidationError as e:
            print(f"SUCCESS: Correctly rejected invalid trade: {e}")
        except Exception as e:
            print(f"ERROR: Unexpected exception type: {type(e)}: {e}")

def test_error_response_format() -> None:
    """Test error response format."""
    print_section_header("Testing Error Response Format")
    
    # Create a Liquidity Analyst Agent for testing
    agent = LiquidityAnalystAgent()
    
    # Create a test error
    test_error = ValueError("Test error message")
    
    # Get error response
    error_response = agent.build_error_response(
        error=test_error,
        symbol="BTC/USDT",
        interval="1h",
        action="HOLD",
        confidence=0
    )
    
    # Check response format
    required_fields = [
        "error", "message", "stack_trace", "symbol", "interval", 
        "timestamp", "action", "confidence", "analysis"
    ]
    
    missing_fields = [field for field in required_fields if field not in error_response]
    
    if not missing_fields:
        print(f"SUCCESS: Error response contains all required fields")
        print(f"Sample error response:")
        print(json.dumps(error_response, indent=2))
    else:
        print(f"ERROR: Error response missing fields: {missing_fields}")
        print(f"Actual response: {error_response}")

def test_trade_execution_error_handling() -> None:
    """Test trade execution error handling."""
    print_section_header("Testing Trade Execution Error Handling")
    
    # Create a Trade Executor Agent for testing
    agent = TradeExecutorAgent()
    
    # Create a sample trade decision
    sample_decision = {
        "action": "BUY",
        "pair": "BTC/USDT",
        "confidence": 80,
        "timestamp": "2025-04-20T12:00:00Z",
        "position_size": 1000
    }
    
    # Temporarily monkey patch the process_decision method to simulate errors
    original_process = agent.process_decision
    
    def mock_process_decision(decision, market_data=None):
        # Simulate random execution errors
        error_types = [
            "network_error", "market_closed", "insufficient_funds", 
            "rate_limit", "invalid_price", "none"
        ]
        error_type = random.choice(error_types)
        
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if error_type == "network_error":
            return {
                "status": "error",
                "message": "Simulated network error during execution",
                "error_type": "network",
                "timestamp": current_time
            }
        elif error_type == "market_closed":
            return {
                "status": "error",
                "message": "Market is currently closed",
                "error_type": "market_status",
                "timestamp": current_time
            }
        elif error_type == "insufficient_funds":
            return {
                "status": "error",
                "message": "Insufficient funds for trade",
                "error_type": "funds",
                "timestamp": current_time
            }
        elif error_type == "rate_limit":
            return {
                "status": "error",
                "message": "Rate limit exceeded",
                "error_type": "rate_limit",
                "timestamp": current_time
            }
        elif error_type == "invalid_price":
            return {
                "status": "error",
                "message": "Price moved outside allowed slippage",
                "error_type": "price_slippage",
                "timestamp": current_time
            }
        else:
            # No error, return success
            return {
                "status": "success",
                "message": "Trade executed successfully (simulated)",
                "trade_id": f"mock_id_{int(time.time())}",
                "timestamp": current_time,
                "decision": decision
            }
    
    # Replace the process_decision method
    agent.process_decision = mock_process_decision
    
    # Run multiple tests to catch different error types
    for i in range(5):
        print(f"\nTest execution #{i+1}:")
        result = agent.process_decision(sample_decision)
        
        if result.get("status") == "success":
            print(f"Execution succeeded: {result['message']}")
        elif result.get("status") == "error":
            print(f"Execution failed gracefully: {result['message']}")
        else:
            print(f"ERROR: Unexpected result format: {result}")
    
    # Restore the original method
    agent.process_decision = original_process
    print("\nRestored original execution method")

def test_pipeline_error_handling() -> None:
    """Test error handling in the execution pipeline."""
    print_section_header("Testing Pipeline Error Handling")
    
    # Import execution pipeline components
    from agents.portfolio_manager_agent import PortfolioManagerAgent
    from agents.risk_guard_agent import RiskGuardAgent
    from agents.position_sizer_agent import PositionSizerAgent
    from agents.trade_executor_agent import TradeExecutorAgent
    
    # Create the pipeline components
    portfolio_manager = PortfolioManagerAgent()
    risk_guard = RiskGuardAgent()
    position_sizer = PositionSizerAgent()
    trade_executor = TradeExecutorAgent()
    
    # Create a sample trading decision
    sample_decision = {
        "action": "BUY",
        "pair": "BTC/USDT",
        "confidence": 75,
        "timestamp": "2025-04-20T12:00:00Z",
        "price": 50000,
    }
    
    # Create sample market data
    sample_market_data = {
        "symbol": "BTC/USDT",
        "price": 50000,
        "volatility": 2.5,
        "volume": 1000,
        "liquidity_score": 0.8
    }
    
    # Run through pipeline and capture any errors
    try:
        # Step 1: Portfolio Manager check
        print("Step 1: Portfolio Manager check")
        portfolio_result = portfolio_manager.validate_trade(sample_decision)
        
        if portfolio_result.get("approved", False):
            print(f"Portfolio check passed: {portfolio_result.get('message', 'No message')}")
            
            # Step 2: Risk Guard check
            print("\nStep 2: Risk Guard check")
            risk_result = risk_guard.evaluate_trade_risk(sample_decision, sample_market_data)
            
            if risk_result.get("approved", False):
                print(f"Risk check passed: {risk_result.get('message', 'No message')}")
                
                # Step 3: Position Sizer calculation
                print("\nStep 3: Position Sizer calculation")
                position_result = position_sizer.calculate_position_size(
                    sample_decision, sample_market_data
                )
                
                if "position_size_usdt" in position_result:
                    print(f"Position size calculated: {position_result['position_size_usdt']} USDT")
                    
                    # Add position size to decision
                    sample_decision["position_size"] = position_result["position_size_usdt"]
                    
                    # Step 4: Trade Execution
                    print("\nStep 4: Trade Execution")
                    execution_result = trade_executor.process_decision(sample_decision, sample_market_data)
                    
                    if execution_result.get("status") == "success":
                        print(f"Trade execution succeeded: {execution_result.get('message', 'No message')}")
                    else:
                        print(f"Trade execution failed: {execution_result.get('message', 'No message')}")
                else:
                    print(f"Position sizing failed: {position_result.get('message', 'No message')}")
            else:
                print(f"Risk check failed: {risk_result.get('message', 'No message')}")
        else:
            print(f"Portfolio check failed: {portfolio_result.get('message', 'No message')}")
    except Exception as e:
        print(f"ERROR: Unhandled exception in pipeline: {type(e)}: {e}")
        
    print("\nPipeline processing complete")

def main():
    """Main test function."""
    print_section_header("aGENtrader v2 Error Handling Tests")
    
    # Run the tests
    test_data_fetching_retries()
    test_mock_fallback()
    test_input_validation()
    test_trade_validation()
    test_error_response_format()
    test_trade_execution_error_handling()
    test_pipeline_error_handling()
    
    print_section_header("All Error Handling Tests Complete")

if __name__ == "__main__":
    main()
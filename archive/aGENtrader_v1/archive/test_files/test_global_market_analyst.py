#!/usr/bin/env python
"""
Global Market Analyst Test Script

Tests the Global Market Analyst agent and its integration with the decision system.
"""

import os
import sys
import time
import logging
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/logs/test_global_analyst.log')
    ]
)
logger = logging.getLogger(__name__)

def check_openai_api_key() -> bool:
    """Check if OpenAI API key is available"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return False
    return True

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test the Global Market Analyst agent')
    parser.add_argument('--symbol', type=str, default='BTCUSDT',
                        help='Trading symbol to analyze')
    parser.add_argument('--output-dir', type=str, default='data/test_results',
                        help='Directory to save test results')
    parser.add_argument('--mock', action='store_true',
                        help='Use mock data instead of database')
    
    return parser.parse_args()

def ensure_output_directories(output_dir: str) -> None:
    """Ensure output directories exist"""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs('data/logs', exist_ok=True)

def generate_mock_market_data() -> Dict[str, Any]:
    """Generate mock market data for testing"""
    return {
        "global_indicators": {
            "dxy": {"latest": 104.25, "trend": "bullish"},
            "spx": {"latest": 5234.42, "trend": "bullish"},
            "vix": {"latest": 14.32, "trend": "bearish"}
        },
        "crypto_metrics": {
            "total_market_cap": {"latest": 2456000000000, "trend": "bullish"},
            "total1": {"latest": 1245000000000, "trend": "bullish"},
            "total2": {"latest": 678000000000, "trend": "neutral"}
        },
        "dominance": {
            "btc": {"latest": 48.5, "trend": "bearish"},
            "eth": {"latest": 16.8, "trend": "bullish"}
        },
        "correlations": {
            "btc_dxy": -0.72,
            "btc_spx": 0.65
        },
        "market_state": "Risk-on - Weaker dollar supporting crypto"
    }

def test_global_market_analyst_standalone(args):
    """Test the Global Market Analyst agent standalone"""
    try:
        from agents.global_market_analyst import GlobalMarketAnalyst
        
        logger.info("Creating Global Market Analyst")
        agent = GlobalMarketAnalyst()
        
        # Test agent definition
        agent_def = agent.get_agent_definition()
        logger.info(f"Agent name: {agent_def['name']}")
        logger.info(f"Agent description: {agent_def['description']}")
        
        # Test function registration
        functions = agent.register_functions()
        logger.info(f"Registered {len(functions['function_map'])} functions")
        logger.info(f"Function names: {list(functions['function_map'].keys())}")
        
        # If using mock data, test the analytical methods
        if args.mock:
            mock_data = generate_mock_market_data()
            formatted_data = agent.format_macro_data_for_agents(mock_data)
            logger.info(f"Formatted data length: {len(formatted_data)}")
        
        return {
            "agent_name": agent_def['name'],
            "function_count": len(functions['function_map']),
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Error in global market analyst test: {e}")
        return {
            "error": str(e),
            "status": "failure"
        }

def test_global_analyst_in_decision_session(args):
    """Test the Global Market Analyst within a decision session"""
    try:
        # Import the updated decision session
        sys.path.append('.')
        from orchestration.decision_session_updated import DecisionSession
        
        logger.info(f"Creating decision session for {args.symbol}")
        
        # Create a decision session
        session = DecisionSession(
            symbol=args.symbol,
            track_performance=False
        )
        
        # If mock mode, monkey patch the _gather_market_data method
        if args.mock:
            def mock_gather_data(self):
                mock_data = {
                    "global_market_data": generate_mock_market_data(),
                    "symbol_data": {
                        "symbol": args.symbol,
                        "current_price": 88245.67,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                return mock_data
            
            # Apply the monkey patch
            import types
            session._gather_market_data = types.MethodType(mock_gather_data, session)
        
        # Run the session
        logger.info("Running decision session")
        result = session.run_session()
        
        logger.info(f"Decision: {result.get('action', 'Unknown')} with confidence {result.get('confidence', 0)}%")
        
        return {
            "symbol": args.symbol,
            "decision": result,
            "status": "success" if "error" not in result else "failure"
        }
    
    except Exception as e:
        logger.error(f"Error in decision session test: {e}")
        return {
            "error": str(e),
            "status": "failure"
        }

def save_test_results(results: Dict[str, Any], output_dir: str, test_name: str) -> None:
    """Save test results to a file"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/{test_name}_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Add timestamp to results
        results["timestamp"] = datetime.now().isoformat()
        
        # Save results
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {filename}")
    
    except Exception as e:
        logger.error(f"Error saving test results: {e}")

def run_tests(args):
    """Run all tests"""
    results = {}
    
    # Test 1: Standalone agent
    logger.info("Running standalone agent test")
    standalone_results = test_global_market_analyst_standalone(args)
    results["standalone_test"] = standalone_results
    
    # If standalone test succeeded and OpenAI API key is available, run decision session test
    if standalone_results["status"] == "success" and check_openai_api_key():
        logger.info("Running decision session test")
        session_results = test_global_analyst_in_decision_session(args)
        results["decision_session_test"] = session_results
    else:
        logger.warning("Skipping decision session test due to failed standalone test or missing API key")
    
    # Save results
    save_test_results(results, args.output_dir, "global_analyst_test")
    
    return results

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Ensure output directories exist
    ensure_output_directories(args.output_dir)
    
    # Check if OpenAI API key is available
    api_key_available = check_openai_api_key()
    if not api_key_available:
        logger.warning("OpenAI API key not available. Some tests may be skipped.")
    
    # Run tests
    results = run_tests(args)
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    standalone_status = results.get("standalone_test", {}).get("status", "not run")
    print(f"Standalone Agent Test: {standalone_status}")
    
    session_status = results.get("decision_session_test", {}).get("status", "not run")
    print(f"Decision Session Test: {session_status}")
    
    if "decision_session_test" in results:
        decision = results["decision_session_test"].get("decision", {})
        if "action" in decision:
            print(f"Trading Decision: {decision['action']} with {decision.get('confidence', 0)}% confidence")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()
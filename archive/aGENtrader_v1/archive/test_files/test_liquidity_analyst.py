#!/usr/bin/env python3
"""
Test Script for Liquidity Analyst Agent

This script tests the functionality of the Liquidity Analyst agent.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import CustomJSONEncoder for properly serializing data types
from agents.database_retrieval_tool import CustomJSONEncoder

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test the Liquidity Analyst agent")
    
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTCUSDT",
        help="Trading symbol (default: BTCUSDT)"
    )
    
    parser.add_argument(
        "--exchange",
        type=str,
        default=None,
        help="Exchange name (default: None for all exchanges)"
    )
    
    parser.add_argument(
        "--analysis-type",
        type=str,
        choices=["exchange_flows", "funding_rates", "market_depth", "futures_basis", "volume_profile", "all"],
        default="all",
        help="Type of liquidity analysis to run (default: all)"
    )
    
    parser.add_argument(
        "--simulate-data",
        action="store_true",
        help="Run the test with simulated data (for testing when real data is not available)"
    )
    
    return parser.parse_args()

def setup_liquidity_tables(simulate: bool = False) -> bool:
    """
    Make sure the liquidity tables are set up in the database.
    
    Args:
        simulate: Whether to setup tables with simulated data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Setting up liquidity tables...")
        
        # Run the setup script
        os.system("python setup_liquidity_tables.py")
        
        if simulate:
            # Populate tables with simulated data
            logger.info("Populating tables with simulated data...")
            os.system("python fetch_liquidity_data.py --simulate --days 7")
        
        return True
    except Exception as e:
        logger.error(f"Error setting up liquidity tables: {str(e)}")
        return False

def test_exchange_flow_analysis(symbol: str, exchange: Optional[str] = None) -> Dict[str, Any]:
    """
    Test the exchange flow analysis functionality.
    
    Args:
        symbol: Trading symbol
        exchange: Exchange name (or None for all exchanges)
        
    Returns:
        Test results
    """
    try:
        from agents.liquidity_analyst import get_liquidity_analyst
        
        logger.info(f"Testing exchange flow analysis for {symbol}...")
        
        # Create a Liquidity Analyst instance
        analyst = get_liquidity_analyst()
        
        # Run the analysis
        analysis = analyst.analyze_exchange_flows(symbol, exchange)
        
        # Print results
        print("\n--- Exchange Flow Analysis Results ---")
        print(json.dumps(analysis, indent=2, cls=CustomJSONEncoder))
        
        return {
            "test": "exchange_flow_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": "error" not in analysis,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error testing exchange flow analysis: {str(e)}")
        return {
            "test": "exchange_flow_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": False,
            "error": str(e)
        }

def test_funding_rate_analysis(symbol: str, exchange: Optional[str] = None) -> Dict[str, Any]:
    """
    Test the funding rate analysis functionality.
    
    Args:
        symbol: Trading symbol
        exchange: Exchange name (or None for all exchanges)
        
    Returns:
        Test results
    """
    try:
        from agents.liquidity_analyst import get_liquidity_analyst
        
        logger.info(f"Testing funding rate analysis for {symbol}...")
        
        # Create a Liquidity Analyst instance
        analyst = get_liquidity_analyst()
        
        # Run the analysis
        analysis = analyst.analyze_funding_rates(symbol, exchange)
        
        # Print results
        print("\n--- Funding Rate Analysis Results ---")
        print(json.dumps(analysis, indent=2, cls=CustomJSONEncoder))
        
        return {
            "test": "funding_rate_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": "error" not in analysis,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error testing funding rate analysis: {str(e)}")
        return {
            "test": "funding_rate_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": False,
            "error": str(e)
        }

def test_market_depth_analysis(symbol: str, exchange: Optional[str] = None) -> Dict[str, Any]:
    """
    Test the market depth analysis functionality.
    
    Args:
        symbol: Trading symbol
        exchange: Exchange name (or None for all exchanges)
        
    Returns:
        Test results
    """
    try:
        from agents.liquidity_analyst import get_liquidity_analyst
        
        logger.info(f"Testing market depth analysis for {symbol}...")
        
        # Create a Liquidity Analyst instance
        analyst = get_liquidity_analyst()
        
        # Run the analysis
        analysis = analyst.analyze_market_depth(symbol, exchange)
        
        # Print results
        print("\n--- Market Depth Analysis Results ---")
        print(json.dumps(analysis, indent=2, cls=CustomJSONEncoder))
        
        return {
            "test": "market_depth_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": "error" not in analysis,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error testing market depth analysis: {str(e)}")
        return {
            "test": "market_depth_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": False,
            "error": str(e)
        }

def test_futures_basis_analysis(symbol: str, exchange: Optional[str] = None) -> Dict[str, Any]:
    """
    Test the futures basis analysis functionality.
    
    Args:
        symbol: Trading symbol
        exchange: Exchange name (or None for all exchanges)
        
    Returns:
        Test results
    """
    try:
        from agents.liquidity_analyst import get_liquidity_analyst
        
        logger.info(f"Testing futures basis analysis for {symbol}...")
        
        # Create a Liquidity Analyst instance
        analyst = get_liquidity_analyst()
        
        # Run the analysis
        analysis = analyst.analyze_futures_basis(symbol, exchange)
        
        # Print results
        print("\n--- Futures Basis Analysis Results ---")
        print(json.dumps(analysis, indent=2, cls=CustomJSONEncoder))
        
        return {
            "test": "futures_basis_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": "error" not in analysis,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error testing futures basis analysis: {str(e)}")
        return {
            "test": "futures_basis_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": False,
            "error": str(e)
        }

def test_volume_profile_analysis(symbol: str, exchange: Optional[str] = None) -> Dict[str, Any]:
    """
    Test the volume profile analysis functionality.
    
    Args:
        symbol: Trading symbol
        exchange: Exchange name (or None for all exchanges)
        
    Returns:
        Test results
    """
    try:
        from agents.liquidity_analyst import get_liquidity_analyst
        
        logger.info(f"Testing volume profile analysis for {symbol}...")
        
        # Create a Liquidity Analyst instance
        analyst = get_liquidity_analyst()
        
        # Run the analysis
        analysis = analyst.analyze_volume_profile(symbol, exchange)
        
        # Print results
        print("\n--- Volume Profile Analysis Results ---")
        print(json.dumps(analysis, indent=2, cls=CustomJSONEncoder))
        
        return {
            "test": "volume_profile_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": "error" not in analysis,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error testing volume profile analysis: {str(e)}")
        return {
            "test": "volume_profile_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": False,
            "error": str(e)
        }

def test_comprehensive_liquidity_analysis(symbol: str, exchange: Optional[str] = None) -> Dict[str, Any]:
    """
    Test the comprehensive liquidity analysis functionality.
    
    Args:
        symbol: Trading symbol
        exchange: Exchange name (or None for all exchanges)
        
    Returns:
        Test results
    """
    try:
        from agents.liquidity_analyst import get_liquidity_analyst
        
        logger.info(f"Testing comprehensive liquidity analysis for {symbol}...")
        
        # Create a Liquidity Analyst instance
        analyst = get_liquidity_analyst()
        
        # Run the analysis
        analysis = analyst.get_liquidity_analysis(symbol, exchange)
        
        # Print results
        print("\n--- Comprehensive Liquidity Analysis Results ---")
        print(json.dumps(analysis, indent=2, cls=CustomJSONEncoder))
        
        return {
            "test": "comprehensive_liquidity_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": "error" not in analysis,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error testing comprehensive liquidity analysis: {str(e)}")
        return {
            "test": "comprehensive_liquidity_analysis",
            "symbol": symbol,
            "exchange": exchange,
            "success": False,
            "error": str(e)
        }

def run_tests(args):
    """
    Run the specified tests.
    
    Args:
        args: Command line arguments
    """
    # Make sure we have the database tooling available
    try:
        from agents.database_retrieval_tool import get_db_connection
        conn = get_db_connection()
        if not conn:
            logger.error("Could not connect to database. Make sure DATABASE_URL is set.")
            sys.exit(1)
        conn.close()
    except ImportError:
        logger.error("Could not import database retrieval tool. Make sure it's properly installed.")
        sys.exit(1)
    
    # Make sure the liquidity tables are set up
    if not setup_liquidity_tables(args.simulate_data):
        logger.error("Failed to set up liquidity tables.")
        sys.exit(1)
    
    # Extend the database retrieval tool with liquidity data functions
    try:
        os.system("python extend_database_tool.py")
    except Exception as e:
        logger.error(f"Failed to extend database retrieval tool: {str(e)}")
        sys.exit(1)
    
    # Make sure the agent can be imported
    try:
        from agents.liquidity_analyst import get_liquidity_analyst
    except ImportError:
        logger.error("Could not import Liquidity Analyst. Make sure it's properly installed.")
        sys.exit(1)
    
    # Run the specified tests
    results = []
    
    if args.analysis_type in ["exchange_flows", "all"]:
        results.append(test_exchange_flow_analysis(args.symbol, args.exchange))
    
    if args.analysis_type in ["funding_rates", "all"]:
        results.append(test_funding_rate_analysis(args.symbol, args.exchange))
    
    if args.analysis_type in ["market_depth", "all"]:
        results.append(test_market_depth_analysis(args.symbol, args.exchange))
    
    if args.analysis_type in ["futures_basis", "all"]:
        results.append(test_futures_basis_analysis(args.symbol, args.exchange))
    
    if args.analysis_type in ["volume_profile", "all"]:
        results.append(test_volume_profile_analysis(args.symbol, args.exchange))
    
    if args.analysis_type == "all":
        results.append(test_comprehensive_liquidity_analysis(args.symbol, args.exchange))
    
    # Print summary
    print("\n=== Test Summary ===")
    for result in results:
        status = "SUCCESS" if result.get("success") else "FAILED"
        print(f"{result.get('test')}: {status}")
    
    # Calculate overall success
    success_count = sum(1 for result in results if result.get("success"))
    print(f"\nOverall: {success_count}/{len(results)} tests passed")

def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    logger.info(f"Starting Liquidity Analyst test for {args.symbol}")
    logger.info(f"Analysis type: {args.analysis_type}")
    logger.info(f"Exchange: {args.exchange if args.exchange else 'all'}")
    logger.info(f"Using simulated data: {args.simulate_data}")
    
    # Run the tests
    run_tests(args)
    
    logger.info("Liquidity Analyst test complete")

if __name__ == "__main__":
    main()
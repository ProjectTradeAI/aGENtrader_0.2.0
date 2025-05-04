"""
Direct test for the graduated conflict handling in TradePlanAgent

This test focuses specifically on the conflict handling logic in TradePlanAgent
without dependencies on other parts of the system.

Author: aGENtrader Team
Date: May 4, 2025
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Tuple, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_direct_conflict_handling')

# Add project root to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the TradePlanAgent
from agents.trade_plan_agent import TradePlanAgent, create_trade_plan_agent

def test_calculate_position_size(
    confidence: float = 75.0, 
    conflict_score: Optional[int] = None, 
    is_conflicted: bool = False,
) -> Dict[str, Any]:
    """
    Test the _calculate_position_size method directly to verify graduated conflict handling.
    
    Args:
        confidence: Decision confidence percentage
        conflict_score: Optional conflict score (0-100)
        is_conflicted: Whether the decision is explicitly marked as conflicted
        
    Returns:
        Dictionary with test results
    """
    # Create the trade plan agent
    trade_plan_agent = create_trade_plan_agent({
        "detailed_logging": True,
        "test_mode": True
    })
    
    # Call the position size calculation directly
    position_size_info = trade_plan_agent._calculate_position_size(
        confidence=confidence,
        conflict_score=conflict_score,
        is_conflicted=is_conflicted
    )
    
    # Extract results
    if isinstance(position_size_info, tuple) and len(position_size_info) >= 3:
        position_size = position_size_info[0]
        conflict_type = position_size_info[1]
        conflict_handling_applied = position_size_info[2]
    else:
        position_size = position_size_info
        conflict_type = None
        conflict_handling_applied = False
    
    # Log the results
    logger.info(f"Tested with confidence={confidence}%, conflict_score={conflict_score}, is_conflicted={is_conflicted}")
    logger.info(f"Position size: {position_size}")
    logger.info(f"Conflict type: {conflict_type}")
    logger.info(f"Conflict handling applied: {conflict_handling_applied}")
    
    # Return the results as a dictionary
    return {
        "position_size": position_size,
        "conflict_type": conflict_type,
        "conflict_handling_applied": conflict_handling_applied,
        "inputs": {
            "confidence": confidence,
            "conflict_score": conflict_score,
            "is_conflicted": is_conflicted
        }
    }

def run_graduated_conflict_tests() -> Dict[str, Dict[str, Any]]:
    """
    Run a series of tests to verify the graduated conflict handling.
    
    Returns:
        Dictionary of test results keyed by test name
    """
    # Store all results for comparison
    results = {}
    
    # Run baseline test (no conflict)
    logger.info("\n\n==================================================")
    logger.info("Testing baseline (no conflict)")
    logger.info("==================================================")
    results["baseline"] = test_calculate_position_size(
        confidence=75.0,
        conflict_score=None,
        is_conflicted=False
    )
    
    # Run test with minor conflict (below 50%)
    logger.info("\n\n==================================================")
    logger.info("Testing minor conflict (<50%)")
    logger.info("==================================================")
    results["minor_conflict"] = test_calculate_position_size(
        confidence=75.0,
        conflict_score=30,
        is_conflicted=False
    )
    
    # Run test with soft conflict (50-70%)
    logger.info("\n\n==================================================")
    logger.info("Testing soft conflict (50-70%)")
    logger.info("==================================================")
    results["soft_conflict"] = test_calculate_position_size(
        confidence=75.0,
        conflict_score=60,
        is_conflicted=False
    )
    
    # Run test with hard conflict (>70%)
    logger.info("\n\n==================================================")
    logger.info("Testing hard conflict (>70%)")
    logger.info("==================================================")
    results["hard_conflict"] = test_calculate_position_size(
        confidence=75.0,
        conflict_score=80,
        is_conflicted=False
    )
    
    # Run test with explicit conflicted flag
    logger.info("\n\n==================================================")
    logger.info("Testing explicit conflict flag")
    logger.info("==================================================")
    results["explicit_conflict"] = test_calculate_position_size(
        confidence=75.0,
        conflict_score=None,
        is_conflicted=True
    )
    
    # Print comparison table
    logger.info("\n\n==================================================")
    logger.info("COMPARISON OF RESULTS")
    logger.info("==================================================")
    
    # Extract the baseline position size for comparison
    baseline_position = results.get("baseline", {}).get("position_size", 0)
    
    if baseline_position == 0:
        logger.warning("Baseline position size is 0, cannot calculate percentages")
        return results
    
    # Print header
    logger.info(f"{'Test':<20} | {'Position Size':<13} | {'% of Baseline':<13} | {'Conflict Score':<14} | {'Conflict Type':<15} | {'Applied'}")
    logger.info(f"{'-'*20}|{'-'*15}|{'-'*15}|{'-'*16}|{'-'*17}|{'-'*10}")
    
    # Print results for each test
    for test_name, result in results.items():
        position = result.get("position_size", 0)
        percent = (position / baseline_position * 100) if baseline_position > 0 else 0
        conflict_score = result.get("inputs", {}).get("conflict_score", "None")
        conflict_type = result.get("conflict_type", "none") or "none"  # Default to "none" if None
        conflict_applied = result.get("conflict_handling_applied", False)
        
        logger.info(f"{test_name:<20} | {position:<13.2f} | {percent:<13.1f}% | {conflict_score!s:<14} | {conflict_type:<15} | {conflict_applied!s:<10}")
    
    return results

def save_results(results: Dict[str, Dict[str, Any]], filename: str = "direct_conflict_test_results.json") -> None:
    """
    Save test results to a JSON file.
    
    Args:
        results: Dictionary of test results
        filename: Output filename
    """
    try:
        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")

if __name__ == "__main__":
    try:
        results = run_graduated_conflict_tests()
        save_results(results)
        logger.info("\nAll tests completed successfully!")
    except Exception as e:
        logger.error(f"Tests failed with error: {e}", exc_info=True)
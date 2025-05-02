#!/usr/bin/env python3
"""
aGENtrader v2 Decision Agent Conflict Resolution Test

This script tests the Decision Agent conflict detection and resolution capabilities.

Usage:
  python3 tests/test_decision_conflicted.py
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from colorama import Fore, Style, init

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import decision agent
from agents.decision_agent import DecisionAgent

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize colorama
init()

def create_test_cases():
    """
    Create a set of test cases for conflict detection and resolution.
    
    Returns:
        List of test case dictionaries
    """
    return [
        {
            "name": "Strong BUY vs Strong SELL",
            "agent_analyses": {
                "technical_analysis": {
                    "action": "BUY",
                    "confidence": 90,
                    "reason": "Strong bullish patterns in technical indicators"
                },
                "sentiment_analysis": {
                    "action": "SELL",
                    "confidence": 85,
                    "reason": "Negative market sentiment from news analysis"
                },
                "liquidity_analysis": {
                    "action": "NEUTRAL",
                    "confidence": 60,
                    "reason": "Balanced liquidity conditions"
                }
            },
            "expected_signal": "CONFLICTED"
        },
        {
            "name": "Strong BUY vs Weak SELL",
            "agent_analyses": {
                "technical_analysis": {
                    "action": "BUY",
                    "confidence": 90,
                    "reason": "Strong bullish patterns in technical indicators"
                },
                "sentiment_analysis": {
                    "action": "SELL",
                    "confidence": 55,
                    "reason": "Slightly negative market sentiment"
                },
                "liquidity_analysis": {
                    "action": "NEUTRAL",
                    "confidence": 60,
                    "reason": "Balanced liquidity conditions"
                }
            },
            "expected_signal": "BUY"
        },
        {
            "name": "Multiple HOLD/NEUTRAL signals with one Strong BUY",
            "agent_analyses": {
                "technical_analysis": {
                    "action": "BUY",
                    "confidence": 95,
                    "reason": "Bullish technical patterns"
                },
                "sentiment_analysis": {
                    "action": "NEUTRAL",
                    "confidence": 60,
                    "reason": "Mixed market sentiment"
                },
                "liquidity_analysis": {
                    "action": "HOLD",
                    "confidence": 55,
                    "reason": "Slightly imbalanced order book, but no clear direction"
                },
                "funding_rate_analysis": {
                    "action": "HOLD",
                    "confidence": 50,
                    "reason": "Neutral funding rates"
                }
            },
            "expected_signal": "BUY"
        },
        {
            "name": "Equal BUY and SELL with high confidence",
            "agent_analyses": {
                "technical_analysis": {
                    "action": "BUY",
                    "confidence": 85,
                    "reason": "Bullish technical patterns"
                },
                "sentiment_analysis": {
                    "action": "SELL",
                    "confidence": 85,
                    "reason": "Negative market sentiment"
                },
                "open_interest_analysis": {
                    "action": "BUY",
                    "confidence": 85,
                    "reason": "Increasing open interest in bullish positions"
                },
                "funding_rate_analysis": {
                    "action": "SELL",
                    "confidence": 85,
                    "reason": "Negative funding rates"
                }
            },
            "expected_signal": "CONFLICTED"
        },
        {
            "name": "All NEUTRAL/HOLD signals",
            "agent_analyses": {
                "technical_analysis": {
                    "action": "NEUTRAL",
                    "confidence": 65,
                    "reason": "Sideways price action"
                },
                "sentiment_analysis": {
                    "action": "HOLD",
                    "confidence": 70,
                    "reason": "Balanced sentiment indicators"
                },
                "liquidity_analysis": {
                    "action": "NEUTRAL",
                    "confidence": 75,
                    "reason": "Balanced order books"
                }
            },
            "expected_signal": "HOLD"
        }
    ]

def run_decision_tests(test_cases, log_conflict_traces=True):
    """
    Run all decision tests with the provided test cases.
    
    Args:
        test_cases: List of test case dictionaries
        log_conflict_traces: Whether to enable conflict trace logging
        
    Returns:
        List of test results
    """
    logger.info(f"{Fore.CYAN}Running Decision Agent conflict tests...{Style.RESET_ALL}")
    
    # Create decision agent with conflict detection enabled
    decision_agent = DecisionAgent(allow_conflict_state=True)
    
    # Track test results
    results = []
    
    # Run each test case
    for idx, test_case in enumerate(test_cases):
        logger.info(f"\n{Fore.CYAN}Test Case {idx+1}: {test_case['name']}{Style.RESET_ALL}")
        
        # Symbol for the test
        test_symbol = "BTC/USDT"
        
        # Make decision
        decision = decision_agent.make_decision(
            agent_analyses=test_case["agent_analyses"],
            symbol=test_symbol,
            interval="1h"
        )
        
        # Check if result matches expected signal
        actual_signal = decision["final_signal"]
        expected_signal = test_case["expected_signal"]
        
        if actual_signal == expected_signal:
            result_color = Fore.GREEN
            result_text = "PASS"
        else:
            result_color = Fore.RED
            result_text = "FAIL"
            
        logger.info(f"Expected: {expected_signal}, Actual: {actual_signal} - {result_color}{result_text}{Style.RESET_ALL}")
        
        # Show confidence and reasoning
        confidence = decision["confidence"]
        reasoning = decision["reasoning"]
        logger.info(f"Confidence: {confidence}%")
        logger.info(f"Reasoning: {reasoning}")
        
        # Show agent contributions
        if "agent_contributions" in decision:
            logger.info("Agent contributions:")
            for agent, contribution in decision["agent_contributions"].items():
                signal = contribution["action"]
                conf = contribution["confidence"]
                weight = contribution["weight"]
                weight_conf = contribution["weighted_confidence"]
                
                # Color code the signals
                if signal == "BUY":
                    signal_color = Fore.GREEN
                elif signal == "SELL":
                    signal_color = Fore.RED
                elif signal in ["HOLD", "NEUTRAL"]:
                    signal_color = Fore.YELLOW
                else:
                    signal_color = Fore.WHITE
                
                logger.info(f"  - {agent}: {signal_color}{signal}{Style.RESET_ALL} ({conf}% confidence, weight {weight}, weighted score {weight_conf:.2f})")
        
        # Show signal counts and weighted scores
        if "signal_counts" in decision:
            logger.info("Signal breakdown:")
            for signal, count in decision["signal_counts"].items():
                logger.info(f"  - {signal}: {count} votes")
        
        # Record test result
        results.append({
            "test_case": test_case,
            "decision": decision,
            "pass": actual_signal == expected_signal
        })
    
    # Print summary
    total_tests = len(results)
    passed_tests = sum(1 for result in results if result["pass"])
    
    print("\n" + "="*80)
    print(f"{Fore.CYAN}## Test Summary ##")
    print(f"Total Tests: {total_tests}, Passed: {passed_tests}, Failed: {total_tests - passed_tests}{Style.RESET_ALL}")
    print("="*80)
    
    if passed_tests == total_tests:
        print(f"\n{Fore.GREEN}All conflict detection tests passed!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}Some tests failed. Review logs for details.{Style.RESET_ALL}")
        
    # Check if we have conflict trace logs
    if log_conflict_traces:
        try:
            log_path = os.path.join("logs", "conflicted_decisions.jsonl")
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    conflict_logs = [json.loads(line) for line in f]
                print(f"\n{Fore.CYAN}Found {len(conflict_logs)} conflict trace logs in {log_path}{Style.RESET_ALL}")
                
                # Show the last 3 conflict traces with details
                if conflict_logs:
                    print(f"\n{Fore.CYAN}Latest Conflict Traces:{Style.RESET_ALL}")
                    for log in conflict_logs[-3:]:
                        print(f"- {log['symbol']} @ {log['interval']}, Confidence: {log['confidence']}%")
                        print(f"  Reason: {log['reasoning'][:100]}...")
                        print(f"  Agent signals: " + ", ".join([f"{agent}: {data['action']} ({data['confidence']}%)" for agent, data in log['agent_scores'].items()]))
                        print()
            else:
                print(f"\n{Fore.YELLOW}No conflict trace logs found at {log_path}{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}Error reading conflict trace logs: {e}{Style.RESET_ALL}")
    
    return results

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='aGENtrader v2 Decision Agent Conflict Resolution Test',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--no-log-traces', action='store_true', help='Disable conflict trace logging')
    
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_arguments()
    
    # Create test cases
    test_cases = create_test_cases()
    
    # Run decision tests
    run_decision_tests(test_cases, log_conflict_traces=not args.no_log_traces)

if __name__ == '__main__':
    main()
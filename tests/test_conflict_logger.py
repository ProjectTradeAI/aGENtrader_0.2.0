#!/usr/bin/env python3
"""
Test for ConflictLogger functionality

This script tests the conflict logger in isolation to verify its functionality.
"""

import os
import sys
import json
import time
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import conflict logger
from utils.conflict_logger import log_conflict, ConflictLogger

def main():
    """Main test function"""
    print("Testing ConflictLogger functionality...")
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Test data
    symbol = "BTCUSDT"
    interval = "1h"
    final_signal = "CONFLICTED"
    confidence = 80.5
    reasoning = "Conflicting signals from multiple agents with high confidence"
    
    # Agent scores
    agent_scores = {
        "TechnicalAnalystAgent": {
            "action": "BUY",
            "confidence": 90,
            "weight": 1.2,
            "weighted_confidence": 108.0
        },
        "SentimentAnalystAgent": {
            "action": "SELL",
            "confidence": 85,
            "weight": 0.8,
            "weighted_confidence": 68.0
        },
        "LiquidityAnalystAgent": {
            "action": "NEUTRAL",
            "confidence": 60,
            "weight": 1.0,
            "weighted_confidence": 60.0
        }
    }
    
    # Metadata
    metadata = {
        "conflict_score": 0.85,
        "high_confidence_signals": ["BUY", "SELL"],
        "normalized_confidence": 78.4,
        "directional_confidence": 65.3,
        "signal_counts": {"BUY": 1, "SELL": 1, "NEUTRAL": 1},
        "total_confidence": {"BUY": 108.0, "SELL": 68.0, "HOLD": 0.0, "NEUTRAL": 60.0}
    }
    
    # Log the conflict
    print("Logging conflict...")
    log_conflict(
        symbol=symbol,
        interval=interval,
        final_signal=final_signal,
        confidence=confidence,
        reasoning=reasoning,
        agent_scores=agent_scores,
        metadata=metadata
    )
    
    # Give the background thread time to write the log
    time.sleep(0.5)
    
    # Check if the log file exists and contains the entry
    log_path = os.path.join("logs", "conflicted_decisions.jsonl")
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            conflict_logs = [json.loads(line) for line in f if line.strip()]
        
        if conflict_logs:
            print(f"Found {len(conflict_logs)} conflict logs.")
            last_log = conflict_logs[-1]
            print(f"Latest conflict log: {symbol} @ {interval}, Signal: {last_log['final_signal']}")
            print(f"Timestamp: {last_log['timestamp']}")
            print(f"Agent signals:")
            for agent, data in last_log['agent_scores'].items():
                print(f"  - {agent}: {data['action']} ({data['confidence']}%)")
            print("Conflict logging is working correctly!")
        else:
            print(f"No entries found in the log file: {log_path}")
    else:
        print(f"Log file not found: {log_path}")
        print("Make sure the logs directory exists and is writable.")

if __name__ == "__main__":
    main()
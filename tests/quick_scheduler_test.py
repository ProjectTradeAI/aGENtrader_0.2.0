#!/usr/bin/env python
"""
Quick test for the DecisionTriggerScheduler
"""

import logging
import sys
import time
from datetime import datetime

# Set up proper Python path
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our scheduler
from aGENtrader_v2.core.trigger_scheduler import DecisionTriggerScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("quick_test")

def main():
    """Run a quick test of the scheduler."""
    logger.info("Starting quick scheduler test")
    
    # Test 1: Basic non-aligned scheduler with 1-second interval
    logger.info("Testing non-aligned scheduler with 1s interval")
    scheduler = DecisionTriggerScheduler(
        interval="1s",
        align_to_clock=False
    )
    
    # Run two quick cycles
    for i in range(2):
        logger.info(f"Cycle {i+1} started")
        time.sleep(0.2)  # Very short work
        trigger_time, wait_duration = scheduler.wait_for_next_tick()
        logger.info(f"Cycle {i+1} triggered at {trigger_time.isoformat()}")
    
    # Test 2: Aligned scheduler
    logger.info("Testing aligned scheduler with 1s interval")
    aligned_scheduler = DecisionTriggerScheduler(
        interval="1s",
        align_to_clock=True
    )
    
    # Run one quick cycle
    logger.info("Aligned cycle started")
    time.sleep(0.2)  # Very short work
    trigger_time, wait_duration = aligned_scheduler.wait_for_next_tick()
    logger.info(f"Aligned cycle triggered at {trigger_time.isoformat()}")
    
    logger.info("Quick test completed successfully")

if __name__ == "__main__":
    main()
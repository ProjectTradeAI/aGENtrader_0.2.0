#!/usr/bin/env python
"""
DecisionTriggerScheduler

This module implements a flexible scheduler for triggering trading decisions
at precise intervals, optionally aligned to clock boundaries.
"""

import time
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, Tuple

# Configure logging
logger = logging.getLogger("aGENtrader.scheduler")

class DecisionTriggerScheduler:
    """
    A scheduler that triggers trading decisions at specified intervals,
    optionally aligned to clock boundaries.
    
    Features:
    - Schedule trading decisions at regular intervals (e.g., "1m", "5m", "1h", "4h")
    - Align triggers to clock boundaries (e.g., exactly at 08:00, 09:00 for hourly)
    - Log timing information for monitoring and diagnostics
    - Save trigger timestamps for analysis
    """
    
    def __init__(
        self, 
        interval: str = "1h", 
        align_to_clock: bool = True,
        log_file: Optional[str] = "logs/trigger_timestamps.jsonl"
    ):
        """
        Initialize the scheduler.
        
        Args:
            interval: Time interval as string (e.g., "1m", "5m", "1h", "4h", "1d")
            align_to_clock: Whether to align triggers to clock boundaries
            log_file: Path to log file for timestamps (None to disable)
        """
        self.interval_str = interval
        self.align_to_clock = align_to_clock
        self.log_file = log_file
        
        # Parse the interval string
        self.interval_seconds = self._parse_interval(interval)
        
        # Initialize cycle tracking
        self.cycle_count = 0
        self.last_trigger_time = None
        self.next_trigger_time = None
        
        # Create log directory if needed
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logger.info(
            f"Scheduler initialized: interval={interval}, "
            f"align_to_clock={align_to_clock}, "
            f"interval_seconds={self.interval_seconds}"
        )
    
    def _parse_interval(self, interval: str) -> int:
        """
        Parse an interval string like "1m", "5m", "1h", "4h", "1d" to seconds.
        
        Args:
            interval: Interval string
            
        Returns:
            Number of seconds
            
        Raises:
            ValueError: If the interval format is invalid
        """
        if not interval or not isinstance(interval, str):
            raise ValueError(f"Invalid interval: {interval}")
        
        # Extract the number and unit
        if interval[-1].isdigit():
            raise ValueError(f"Invalid interval format: {interval}. Expected format like '1m', '5m', '1h', etc.")
        
        try:
            value = int(interval[:-1])
            unit = interval[-1].lower()
        except (ValueError, IndexError):
            raise ValueError(f"Invalid interval format: {interval}")
        
        # Convert to seconds
        if unit == 's':
            return value  # seconds directly
        elif unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 60 * 60
        elif unit == 'd':
            return value * 24 * 60 * 60
        else:
            raise ValueError(f"Unsupported time unit: {unit}")
    
    def _calculate_next_trigger(self) -> datetime:
        """
        Calculate the next trigger time based on the interval and alignment setting.
        
        Returns:
            The next trigger time as a datetime object
        """
        now = datetime.utcnow()
        
        if not self.align_to_clock:
            # Simply add the interval to the current time
            return now + timedelta(seconds=self.interval_seconds)
        
        # For clock alignment, we need to find the next multiple of the interval
        if self.interval_str.endswith('s'):
            # For seconds, align to the next multiple of seconds
            seconds_value = int(self.interval_str[:-1])
            target_second = ((now.second // seconds_value) + 1) * seconds_value
            target_minute = now.minute
            
            # If the target second exceeds 59, roll over to the next minute
            if target_second >= 60:
                target_second = 0
                target_minute = (target_minute + 1) % 60
                # If we roll over minutes, we might need to roll over hours too
                if target_minute == 0:
                    target_hour = (now.hour + 1) % 24
                else:
                    target_hour = now.hour
            else:
                target_hour = now.hour
            
            target = now.replace(
                hour=target_hour,
                minute=target_minute,
                second=target_second,
                microsecond=0
            )
            
        elif self.interval_str.endswith('m'):
            # For minutes, align to the next multiple of minutes
            minutes_value = int(self.interval_str[:-1])
            target_minute = ((now.minute // minutes_value) + 1) * minutes_value
            target_hour = now.hour
            
            # If the target minute exceeds 59, roll over to the next hour
            if target_minute >= 60:
                target_minute = 0
                target_hour = (target_hour + 1) % 24
            
            target = now.replace(
                hour=target_hour,
                minute=target_minute,
                second=0,
                microsecond=0
            )
            
        elif self.interval_str.endswith('h'):
            # For hours, align to the next multiple of hours
            hours_value = int(self.interval_str[:-1])
            target_hour = ((now.hour // hours_value) + 1) * hours_value
            
            # If the target hour exceeds 23, roll over to the next day
            if target_hour >= 24:
                target_hour = 0
                target = now.replace(
                    hour=target_hour,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                target = target + timedelta(days=1)
            else:
                target = now.replace(
                    hour=target_hour,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                
        elif self.interval_str.endswith('d'):
            # For days, align to the start of the next day
            target = now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )
            target = target + timedelta(days=1)
        else:
            # Fallback: just add the interval
            target = now + timedelta(seconds=self.interval_seconds)
        
        # If the calculated time is in the past (due to logic edge cases),
        # simply add the interval to the current time
        if target <= now:
            target = now + timedelta(seconds=self.interval_seconds)
        
        return target
    
    def wait_for_next_tick(self) -> Tuple[datetime, float]:
        """
        Wait until the next scheduled trigger time.
        
        Returns:
            Tuple of (trigger_time, wait_duration_seconds)
        """
        self.cycle_count += 1
        current_time = datetime.utcnow()
        
        # If this is the first wait, calculate the initial next trigger time
        if self.next_trigger_time is None:
            self.next_trigger_time = self._calculate_next_trigger()
        
        # Calculate how long to wait
        wait_seconds = (self.next_trigger_time - current_time).total_seconds()
        
        # Log the wait
        logger.info(
            f"Cycle {self.cycle_count}: "
            f"Waiting {wait_seconds:.2f}s until next trigger at {self.next_trigger_time.isoformat()}"
        )
        
        # Don't wait if we're already past the target time
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        
        # Record the actual trigger time
        trigger_time = datetime.utcnow()
        delay = (trigger_time - self.next_trigger_time).total_seconds()
        
        # Log the trigger
        logger.info(
            f"Cycle {self.cycle_count}: "
            f"Triggered at {trigger_time.isoformat()} "
            f"(delay: {delay:.3f}s)"
        )
        
        # Save to log file if enabled
        if self.log_file:
            self._log_trigger(
                cycle=self.cycle_count,
                scheduled=self.next_trigger_time,
                actual=trigger_time,
                delay=delay,
                wait=wait_seconds
            )
        
        # Update tracking variables
        self.last_trigger_time = trigger_time
        self.next_trigger_time = self._calculate_next_trigger()
        
        return trigger_time, wait_seconds
    
    def _log_trigger(
        self, 
        cycle: int, 
        scheduled: datetime, 
        actual: datetime, 
        delay: float,
        wait: float
    ) -> None:
        """
        Log a trigger event to the log file.
        
        Args:
            cycle: Cycle number
            scheduled: Scheduled trigger time
            actual: Actual trigger time
            delay: Delay in seconds
            wait: Wait time in seconds
        """
        if not self.log_file:
            return
            
        try:
            log_entry = {
                "cycle": cycle,
                "timestamp": datetime.utcnow().isoformat(),
                "scheduled": scheduled.isoformat(),
                "actual": actual.isoformat(),
                "delay_seconds": delay,
                "wait_seconds": wait,
                "interval": self.interval_str,
                "aligned": self.align_to_clock
            }
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to write trigger log: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the scheduler.
        
        Returns:
            Dictionary with scheduler statistics
        """
        return {
            "cycle_count": self.cycle_count,
            "interval": self.interval_str,
            "interval_seconds": self.interval_seconds,
            "align_to_clock": self.align_to_clock,
            "last_trigger": self.last_trigger_time.isoformat() if self.last_trigger_time else None,
            "next_trigger": self.next_trigger_time.isoformat() if self.next_trigger_time else None
        }
    
    def __str__(self) -> str:
        """
        Get a string representation of the scheduler.
        
        Returns:
            String representation
        """
        return (
            f"DecisionTriggerScheduler(interval={self.interval_str}, "
            f"align_to_clock={self.align_to_clock}, "
            f"cycles={self.cycle_count})"
        )
    
    def __repr__(self) -> str:
        return self.__str__()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Test the scheduler
    print("Testing scheduler for 3 cycles with 10s interval")
    scheduler = DecisionTriggerScheduler(interval="10s", align_to_clock=True)
    
    for i in range(3):
        print(f"Cycle {i+1}")
        time.sleep(2)  # Simulate some work
        scheduler.wait_for_next_tick()
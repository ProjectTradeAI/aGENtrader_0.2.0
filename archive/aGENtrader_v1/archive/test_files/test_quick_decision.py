"""
Quick Decision Session Test with Timeout

This script runs a simplified trading decision test with a timeout
to ensure it completes within a reasonable time.
"""
import os
import json
import asyncio
import logging
import signal
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("quick_decision_test")

# Import necessary modules
try:
    from orchestration.decision_session import DecisionSession
except ImportError:
    logger.error("Failed to import DecisionSession")
    exit(1)

def timeout_handler(signum, frame):
    """Handle timeout signal"""
    raise TimeoutError("Decision session timed out")

async def run_decision_with_timeout(timeout: int = 120) -> Optional[Dict[str, Any]]:
    """
    Run a decision session with timeout
    
    Args:
        timeout: Timeout in seconds
        
    Returns:
        Decision result or None if timed out
    """
    # Set timeout handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    result = None
    try:
        # Create session ID with timestamp
        session_id = f"quick_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create decision session
        decision_session = DecisionSession(
            symbol="BTCUSDT",
            session_id=session_id,
            config_path="config/decision_session.json"
        )
        
        print(f"\nRunning quick decision test with {timeout}s timeout...")
        
        # Get current price for BTCUSDT from the database tool
        from agents.database_retrieval_tool import get_latest_price
        import json
        
        latest_price_json = get_latest_price("BTCUSDT")
        latest_price_data = json.loads(latest_price_json)
        current_price = latest_price_data["close"]
        
        print(f"Current price for BTCUSDT: ${current_price}")
        
        # Run simulated session for faster results with test RSI value
        session_data = {
            "session_id": session_id,
            "symbol": "BTCUSDT",
            "current_price": current_price,
            "timestamp": datetime.now().isoformat(),
            "market_data": {
                "technical_indicators": {
                    "rsi": {"rsi": 28.5}  # Low RSI to trigger BUY decision
                }
            }
        }
        
        # Run simulated session
        result = decision_session._run_simulated_session(session_data)
        
        if result:
            print(f"\nDecision: {result['action']} (Confidence: {result['confidence']}%)")
            print(f"Reasoning: {result['reasoning'][:150]}...\n")
        else:
            print("No decision produced")
            
        # Reset alarm
        signal.alarm(0)
        
        return result
    except TimeoutError:
        print(f"\nDecision session timed out after {timeout} seconds")
        return None
    except Exception as e:
        logger.error(f"Error in decision session: {str(e)}")
        print(f"Error: {str(e)}")
        return None
    finally:
        # Ensure alarm is reset
        signal.alarm(0)

def save_result(result: Dict[str, Any]) -> None:
    """Save result to file"""
    if not result:
        return
    
    output_dir = "data/logs/quick_tests"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{output_dir}/decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Result saved to {filename}")

async def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("Quick Trading Decision Test".center(80))
    print("=" * 80 + "\n")
    
    # Run decision session with 30 second timeout
    result = await run_decision_with_timeout(30)
    
    if result:
        save_result(result)
        print("\nTest completed successfully")
    else:
        print("\nTest failed to produce a decision")

if __name__ == "__main__":
    asyncio.run(main())
"""
Test script for MarketDataManager's optimized format
"""
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from agents.market_data_manager import MarketDataManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

async def test_market_data_manager():
    """Test MarketDataManager's optimized data format"""
    try:
        print("\n=== Testing Market Data Manager ===\n")
        
        # Initialize manager
        mdm = MarketDataManager()
        
        # Test parameters
        symbol = "BTCUSDT"
        interval = "1h"
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=1)
        
        # Test data retrieval with optimized format
        print("Testing optimized format...")
        success = await mdm.fetch_historical_data(symbol, interval, start_time, end_time)
        if not success:
            raise Exception("Failed to fetch historical data")
            
        data = mdm.get_market_data(symbol, interval, start_time, end_time, optimized=True)
        if not data:
            raise Exception("No data available")
            
        print("\nOptimized Data Format:")
        print(f"Symbol: {data['symbol']}")
        print(f"Timestamp: {data['timestamp']}")
        print(f"Current Price: {data['price_metrics']['current']}")
        print(f"24h High: {data['price_metrics']['high_24h']}")
        print(f"24h Low: {data['price_metrics']['low_24h']}")
        print(f"RSI: {data['technical_signals']['momentum']['rsi']:.2f}")
        print(f"Volume Trend: {data['technical_signals']['volume']['trend']:.2f}%")
        
        # Test DataFrame format
        print("\nTesting DataFrame format...")
        df = mdm.get_market_data(symbol, interval, start_time, end_time, optimized=False)
        if df is not None:
            print(f"DataFrame shape: {df.shape}")
            print("\nLatest data point:")
            print(df.tail(1))
        
        print("\n=== Test Complete ===")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        print("\n=== Test Failed ===")
    finally:
        mdm.cleanup()

def main():
    """Main entry point"""
    asyncio.run(test_market_data_manager())

if __name__ == "__main__":
    main()

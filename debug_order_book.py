"""
Order Book Debug Script

This script directly fetches order book data from Binance and prints the results
to help debug issues with the LiquidityAnalystAgent.

The purpose is to directly log the raw order book bid/ask values to understand
why the LiquidityAnalystAgent is returning wrong signals.
"""

import os
import sys
import json
from binance_data_provider import BinanceDataProvider

def main():
    """Fetch and analyze order book data directly."""
    print("=== Order Book Debug Script ===")
    
    # Create data provider
    api_key = os.getenv('BINANCE_API_KEY', '')
    api_secret = os.getenv('BINANCE_API_SECRET', '')
    
    print(f"Using API credentials: {'Available' if api_key and api_secret else 'Not available'}")
    
    provider = BinanceDataProvider(api_key=api_key, api_secret=api_secret)
    
    # Fetch order book for BTC/USDT
    symbol = "BTCUSDT"
    print(f"Fetching order book for {symbol}...")
    
    try:
        order_book = provider.fetch_market_depth(symbol, limit=100)
        
        # Basic info
        print(f"Order book data keys: {list(order_book.keys())}")
        
        # Access bids/asks
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])
        print(f"Number of bids: {len(bids)}")
        print(f"Number of asks: {len(asks)}")
        
        if bids and asks:
            # Sample data
            print(f"First 3 bids: {bids[:3]}")
            print(f"First 3 asks: {asks[:3]}")
            
            # Basic analysis
            best_bid = float(bids[0][0]) if bids else 0
            best_ask = float(asks[0][0]) if asks else 0
            spread = best_ask - best_bid
            spread_pct = (spread / best_bid) * 100 if best_bid > 0 else 0
            
            print(f"Best bid: {best_bid}")
            print(f"Best ask: {best_ask}")
            print(f"Spread: {spread} ({spread_pct:.4f}%)")
            
            # Calculate volume
            bid_volume = sum(float(b[1]) for b in bids)
            ask_volume = sum(float(a[1]) for a in asks)
            print(f"Total bid volume: {bid_volume}")
            print(f"Total ask volume: {ask_volume}")
            print(f"Bid/Ask volume ratio: {bid_volume/ask_volume if ask_volume else 'N/A'}")
            
            # Save to file for inspection
            with open('debug_order_book.json', 'w') as f:
                json.dump(order_book, f, indent=2)
            print("Saved order book to debug_order_book.json")
                
        else:
            print("No bids or asks in the order book!")
    
    except Exception as e:
        print(f"Error fetching order book: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
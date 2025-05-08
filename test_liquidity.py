import os
import sys
import json
from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from binance_data_provider import BinanceDataProvider

def main():
    print("Testing LiquidityAnalystAgent with real data...")
    
    # Create data provider and liquidity agent
    provider = BinanceDataProvider()
    agent = LiquidityAnalystAgent(data_fetcher=provider)
    
    # Test with direct order book data
    symbol = "BTCUSDT"
    print(f"Analyzing {symbol}...")
    
    # Use the order book data from the debug file
    try:
        with open('debug_order_book.json', 'r') as f:
            order_book = json.load(f)
            
        result = agent.analyze(
            symbol=symbol,
            market_data={"order_book": order_book},
            interval="1h"
        )
        
        print(f"\nResult: {result['signal']} with {result['confidence']}% confidence")
        print(f"Explanation: {result['explanation'][0]}")
        print(f"Analysis mode: {result['analysis_mode']}")
        
        if result.get('entry_zone') and result.get('stop_loss_zone'):
            print(f"Entry: ${result['entry_zone']:.2f}")
            print(f"Stop Loss: ${result['stop_loss_zone']:.2f}")
            print(f"Take Profit: ${result['metrics'].get('suggested_take_profit', 'None')}")
            
            if 'trade_direction' in result['metrics']:
                direction = result['metrics']['trade_direction']
                print(f"Trade Direction: {direction}")
                
                if 'risk_reward_ratio' in result['metrics']:
                    print(f"Risk:Reward Ratio: 1:{result['metrics']['risk_reward_ratio']}")
                
                if 'sl_description' in result['metrics'] and 'tp_description' in result['metrics']:
                    print(f"Stop Loss Position: {result['metrics']['sl_description']}")
                    print(f"Take Profit Position: {result['metrics']['tp_description']}")
    
    except Exception as e:
        print(f"Error testing liquidity agent: {str(e)}")

if __name__ == "__main__":
    main()

"""
Simple test script to demonstrate agent communication.
"""
import autogen
import json
import os
from datetime import datetime
from agents.shell_executor import ShellExecutorAgent

def main():
    print("\n=== Starting Agent Communication Test ===\n")

    # Configure LLM
    config_list = [
        {
            'model': 'gpt-3.5-turbo',
            'api_key': os.getenv('OPENAI_API_KEY')
        }
    ]

    # Create market analyst agent
    market_analyst = autogen.AssistantAgent(
        name="market_analyst",
        llm_config={"config_list": config_list},
        system_message="""You are an expert market analyst.
        When provided with market data, analyze it focusing on:
        1. Price trends and patterns
        2. Volume analysis
        3. Key support/resistance levels
        4. Trading signals

        Provide analysis in this format:
        - TREND: [Bullish/Bearish/Neutral]
        - SUPPORT: [Key price level]
        - RESISTANCE: [Key price level]
        - VOLUME: [Analysis of volume patterns]
        - SIGNALS: [Any trading signals identified]
        - RECOMMENDATION: [Trading recommendation with confidence level]"""
    )

    # Create user proxy agent
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        code_execution_config=False,  # Disable code execution
        max_consecutive_auto_reply=1  # Only allow one response
    )

    try:
        print("\nInitializing Shell Executor Agent...")
        print("-" * 50)

        # Get market data using shell executor for specific timestamp
        shell_executor = ShellExecutorAgent()
        target_time = "2025-03-20 08:00:00"  # Testing earlier timestamp
        print(f"Querying market data for BTC/USDT at {target_time}...")

        market_data = shell_executor.get_market_data(
            "BTCUSDT", 
            "1h",
            target_time=target_time
        )

        if not market_data.get("success"):
            print(f"Error getting market data: {market_data.get('error')}")
            return

        if not market_data.get("stats"):
            print("No market statistics available in the response")
            return

        print("\n=== Market Data Retrieved ===")
        print(f"Symbol: BTCUSDT")
        print(f"Timestamp: {market_data['stats'].get('timestamp', target_time)}")
        print(f"Price: ${market_data['stats']['latest_price']:,.2f}")
        print(f"Period High: ${market_data['stats']['price_high']:,.2f}")
        print(f"Period Low: ${market_data['stats']['price_low']:,.2f}")
        print(f"Price Change: ${market_data['stats']['price_change']:,.2f}")
        print(f"Price Change %: {market_data['stats']['price_change_percent']:.2f}%")
        print(f"Average Volume: {market_data['stats']['avg_volume']:,.2f}")
        print("\n" + "="*50 + "\n")

        print("Sending market data to analyst...")
        print("-" * 50)

        # Format the analysis request
        analysis_request = f"""
        Please analyze this BTC/USDT market data for {target_time}:

        Latest Market Statistics:
        - Current Price: ${market_data['stats']['latest_price']:,.2f}
        - Period High: ${market_data['stats']['price_high']:,.2f}
        - Period Low: ${market_data['stats']['price_low']:,.2f}
        - Price Change: ${market_data['stats']['price_change']:,.2f}
        - Price Change %: {market_data['stats']['price_change_percent']:.2f}%
        - Average Volume: {market_data['stats']['avg_volume']:,.2f}

        Please provide a complete analysis following the specified format.
        """
        print(analysis_request)
        print("-" * 50)

        # Get market analysis
        result = user_proxy.initiate_chat(
            market_analyst,
            message=analysis_request
        )

        print("\n=== Market Analysis ===\n")
        # Only print the market analyst's response
        for message in result.chat_history:
            if message['role'] == 'assistant' and 'TREND:' in message['content']:
                print(message['content'])
                break

        print("\n" + "="*50)

    except Exception as e:
        print(f"Error during test: {str(e)}")
    finally:
        if 'shell_executor' in locals():
            shell_executor.close()

if __name__ == "__main__":
    main()
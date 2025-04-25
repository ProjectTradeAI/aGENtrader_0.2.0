"""
Test script for Shell Executor Agent integration with other agents
"""
import autogen
import json
import os
from datetime import datetime
from agents.shell_executor import ShellExecutorAgent

def main():
    print("Starting Shell Executor Agent test...")

    # Configure agents
    config_list = [
        {
            'model': 'gpt-3.5-turbo',
            'api_key': os.getenv('OPENAI_API_KEY')
        }
    ]

    # Create shell executor agent instance
    shell_executor = ShellExecutorAgent()

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
        max_consecutive_auto_reply=1
    )

    try:
        # Get market data from shell executor
        market_data = shell_executor.get_market_data("BTCUSDT", "24h")

        if not market_data["success"]:
            print(f"Error getting market data: {market_data.get('error')}")
            return

        # Format query for market analyst
        test_query = f"""
        Please analyze this BTC/USDT market data:

        Latest Statistics:
        - Current Price: ${market_data['stats']['latest_price']:,.2f}
        - 24h High: ${market_data['stats']['price_high']:,.2f}
        - 24h Low: ${market_data['stats']['price_low']:,.2f}
        - Price Change: ${market_data['stats']['price_change']:,.2f}
        - Price Change %: {market_data['stats']['price_change_percent']:.2f}%
        - Average Volume: {market_data['stats']['avg_volume']:,.2f}

        Please provide a complete analysis following the specified format.
        """

        # Initiate the conversation
        result = user_proxy.initiate_chat(
            market_analyst,
            message=test_query
        )

        # Save test results
        output_dir = "data/test_results"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/shell_executor_test_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'market_data': market_data,
                'analysis': {
                    'messages': result.chat_history,
                    'final_response': result.chat_history[-1]['content'] if result.chat_history else None
                }
            }, f, indent=2)

        print(f"Test completed successfully. Results saved to {output_file}")

    except Exception as e:
        print(f"Error during test execution: {str(e)}")
        raise
    finally:
        shell_executor.close()

if __name__ == "__main__":
    main()
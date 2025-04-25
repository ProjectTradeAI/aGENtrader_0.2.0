"""
Test script for AutoGen market analysis with optimized data format
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
import autogen
from agents.market_data_manager import MarketDataManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

async def run_analysis():
    """Run market analysis with AutoGen agents using optimized data format"""
    try:
        print("\n=== Starting Market Analysis Test ===\n")

        # Load market data
        mdm = MarketDataManager()
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=1)  # Last 24 hours

        # Fetch and get market data in optimized format
        success = await mdm.fetch_historical_data("BTCUSDT", "1h", start_time, end_time)
        if not success:
            raise Exception("Failed to fetch market data")

        market_data = mdm.get_market_data("BTCUSDT", "1h", start_time, end_time)
        if not market_data:
            raise Exception("No market data available")

        logger.info("Successfully loaded market data")

        # Configure LLM
        config_list = [
            {
                'model': 'gpt-4',
                'api_key': os.environ.get('OPENAI_API_KEY'),
                'temperature': 0.7,
                'max_tokens': 1000,  # Reduced due to optimized format
                'timeout': 60
            }
        ]

        # Create user proxy agent
        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2,
            code_execution_config={
                "work_dir": "coding",
                "use_docker": False,
                "timeout": 60
            }
        )

        # Create market analyst agent
        market_analyst = autogen.AssistantAgent(
            name="market_analyst",
            llm_config={"config_list": config_list},
            system_message="""You are an expert market analyst specializing in cryptocurrency market data analysis.
            Your task is to analyze the provided market data and generate trading insights.

            The data is in an optimized format containing:
            - Current price metrics and daily changes
            - Technical signals (trend, momentum, volume)
            - Support and resistance levels

            Provide your analysis in this format:
            {
                "analysis": {
                    "trend": "bullish/bearish/neutral",
                    "strength": 1-10,
                    "support_levels": [price1, price2],
                    "resistance_levels": [price1, price2],
                    "ma_analysis": "above/below MA20/50/200",
                    "rsi_signal": "overbought/oversold/neutral",
                    "volume_trend": "increasing/decreasing/stable"
                },
                "recommendation": {
                    "action": "buy/sell/hold",
                    "confidence": 1-10,
                    "entry_points": [price1, price2],
                    "targets": [price1, price2],
                    "stop_loss": price,
                    "timeframe": "short/medium/long",
                    "position_size": "small/medium/large"
                },
                "risk_assessment": {
                    "market_volatility": "high/medium/low",
                    "risk_level": 1-10,
                    "key_risks": ["risk1", "risk2"]
                }
            }"""
        )

        # Test market analysis
        test_request = """
        Please analyze the current market data and provide:
        1. Technical analysis with trend identification
        2. Support and resistance levels
        3. Trading recommendation with risk assessment

        Use the optimized data format for your analysis.
        Focus on actionable insights based on the current market conditions.
        """

        # Start conversation
        logger.info("Starting market analysis conversation...")
        try:
            chat_result = await user_proxy.a_initiate_chat(
                market_analyst,
                message=test_request
            )

            # Get the last message content from chat history
            last_message = None
            if chat_result.chat_history:
                for msg in reversed(chat_result.chat_history):
                    if msg.get('role') == 'assistant' and msg.get('name') == 'market_analyst' and msg.get('content'):
                        last_message = msg['content']
                        break

            # Save results
            output_dir = "data/test_results"
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{output_dir}/market_analysis_{timestamp}.json"

            with open(output_file, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'market_data': market_data,
                    'analysis_request': test_request,
                    'analysis_response': last_message,
                    'chat_history': chat_result.chat_history
                }, f, indent=2)

            logger.info(f"Analysis results saved to: {output_file}")
            print("\n=== Market Analysis Complete ===")

        except Exception as e:
            logger.error(f"Error during analysis conversation: {str(e)}")
            print("\n=== Analysis Failed ===")

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        print("\n=== Analysis Failed ===")
    finally:
        if mdm:
            mdm.cleanup()

def main():
    """Main entry point"""
    if os.environ.get('OPENAI_API_KEY') is None:
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    asyncio.run(run_analysis())

if __name__ == "__main__":
    main()
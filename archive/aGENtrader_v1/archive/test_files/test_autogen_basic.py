"""
Basic test script for AutoGen agent communication.
"""
import autogen
import json
import os
from datetime import datetime

def main():
    print("Starting basic AutoGen test...")

    # Configure agents
    config_list = [
        {
            'model': 'gpt-3.5-turbo',
            'api_key': os.getenv('OPENAI_API_KEY')
        }
    ]

    # Create assistant agent
    assistant = autogen.AssistantAgent(
        name="assistant",
        llm_config={"config_list": config_list},
        system_message="You are a helpful assistant that provides concise analysis."
    )

    # Create user proxy agent
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
        code_execution_config={"work_dir": "coding"}
    )

    # Test conversation
    test_query = """
    Please analyze this scenario:
    - Input: Market shows increasing volume
    - Task: Provide a brief interpretation

    Requirements:
    1. Keep response under 50 words
    2. Focus on key implications
    """

    try:
        # Initiate the conversation
        result = user_proxy.initiate_chat(
            assistant,
            message=test_query
        )

        # Save test results
        output_dir = "data/test_results"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/test_result_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'query': test_query,
                'result': {
                    'messages': result.chat_history,
                    'final_response': result.chat_history[-1]['content'] if result.chat_history else None
                }
            }, f, indent=2)

        print(f"Test completed successfully. Results saved to {output_file}")

    except Exception as e:
        print(f"Error during test execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
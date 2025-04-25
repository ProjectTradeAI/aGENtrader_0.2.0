"""
Test script to verify Deepseek API connectivity
"""

import os
import requests
from dotenv import load_dotenv
import json

def test_deepseek_connection():
    """Test direct connection to Deepseek API"""
    print("Testing Deepseek API connection...")

    api_key = os.getenv("DEEPSEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEK_API_KEY environment variable is not set")

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "deepseek-chat",  # Using Deepseek's chat model
        "messages": [
            {"role": "system", "content": "You are a helpful trading assistant."},
            {"role": "user", "content": "Hello, this is a test message."}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }

    try:
        print("Making test request to Deepseek API...")
        print(f"Request payload: {json.dumps(data, indent=2)}")

        response = requests.post(url, headers=headers, json=data, timeout=30)

        # Print detailed response information
        print(f"\nResponse status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        try:
            response_content = response.json()
            print(f"Response content: {json.dumps(response_content, indent=2)}")
        except:
            print(f"Raw response content: {response.text}")

        response.raise_for_status()
        print("Successfully connected to Deepseek API!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Deepseek API: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                print(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                print(f"Raw error response: {e.response.text}")
        return False

if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    test_deepseek_connection()
"""
Simple test to verify OpenAI API key works correctly
"""

import os
import openai
from openai import OpenAI

# Get API key from environment variable
api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    print("ERROR: OPENAI_API_KEY environment variable is not set")
    exit(1)

# Display API key info
print(f"Using API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")

# Create a client
client = OpenAI(api_key=api_key)

# Try a simple completion
try:
    print("Testing API connection...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, are you working?"}
        ],
        temperature=0.7,
        max_tokens=50
    )
    
    # Print response
    print("Success! The API is working. Response:")
    print(response.choices[0].message.content)
    
except Exception as e:
    print(f"Error: {str(e)}")
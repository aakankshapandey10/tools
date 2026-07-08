"""
Setup check: confirms your Anthropic API credentials are working
before you move on to the tool-calling demo (weather_tool_demo.py).
"""

import os

from dotenv import load_dotenv
import anthropic
from anthropic import AnthropicFoundry

load_dotenv()  # loads variables from a .env file into the environment

try:
    client = AnthropicFoundry(
        api_key=os.getenv("AZURE_API_KEY"),
        base_url=os.getenv("AZURE_BASE_URL"),
    )
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=32,
        messages=[{"role": "user", "content": "Reply with just the word: ready"}],
    )
    text = next(block.text for block in response.content if block.type == "text")
    print(f"✅ Setup works. Claude replied: {text.strip()}")
    print("You're good to run: python weather_tool_demo.py")
except anthropic.AuthenticationError:
    print("❌ Authentication failed — your API key wasn't found or is invalid.")
    print("   Make sure AZURE_API_KEY and AZURE_BASE_URL are set in your .env file in this folder.")
except Exception as e:
    print(f"❌ Something went wrong: {e}")

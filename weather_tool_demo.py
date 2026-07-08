"""
Tool-calling demo: the manager/staff loop we whiteboarded.

Claude (the manager) can't check the weather itself. It asks us (the staff)
to run the get_weather tool, we do the real work, and hand the answer back.
"""

import os

from dotenv import load_dotenv
from anthropic import AnthropicFoundry

load_dotenv()  # loads variables from a .env file into the environment

client = AnthropicFoundry(
    api_key=os.getenv("AZURE_API_KEY"),
    base_url=os.getenv("AZURE_BASE_URL"),
)

# Step 1: the tool schema — the "menu" we hand to Claude.
# name = job title, description = when to call it, input_schema = the form to fill out.
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and state, e.g. San Francisco, CA",
                }
            },
            "required": ["location"],
        },
    }
]


def get_weather(location: str) -> str:
    """The 'staff member' that actually does the work. Faked here for the demo."""
    return f"72°F and sunny in {location}"


def run(user_message: str):
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        # Show Claude's turn so you can see the tool_use block when it appears.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Claude is done — print the final text answer.
            for block in response.content:
                if block.type == "text":
                    print("Claude:", block.text)
            return

        # Claude asked for one or more tools. Run each one and collect results.
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[tool call] {block.name}({block.input})")
                if block.name == "get_weather":
                    result = get_weather(block.input["location"])
                else:
                    result = f"Unknown tool: {block.name}"

                print(f"[tool result] {result}")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        # Hand the results back to Claude and loop again.
        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    question = input("Ask about the weather: ")
    run(question)

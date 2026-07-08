"""
get_weather tool (Part B) — real weather via the Open-Meteo API, no API key needed.

Same manager/staff pattern as calculator.py:
Claude asks for the tool, we do the real work (HTTP calls), we hand the answer back.
"""

import os

import requests
from dotenv import load_dotenv
from anthropic import AnthropicFoundry

load_dotenv()

client = AnthropicFoundry(
    api_key=os.getenv("AZURE_API_KEY"),
    base_url=os.getenv("AZURE_BASE_URL")
)

MODEL = "claude-haiku-4-5"  # or "claude-2.0" or "claude-instant-v1.1"

TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The name of the city to get the weather for."
                }
            },
            "required": ["location"]
        }
    }
]

# WMO weather codes -> plain-English description (subset covering the common ones)
WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "slight snow fall",
    73: "moderate snow fall",
    75: "heavy snow fall",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
}


def geocode(location: str):
    """Turn a city name into (latitude, longitude, resolved_name). Raises ValueError if not found."""
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1},

    )
    response.raise_for_status()
    data = response.json()

    results = data.get("results")
    if not results:
        raise ValueError(f"Could not find a location matching '{location}'")

    match = results[0]
    return match["latitude"], match["longitude"], match["name"]


def get_weather(location: str) -> str:
    """The 'staff member' that actually does the work — real Open-Meteo calls."""
    try:
        lat, lon, resolved_name = geocode(location)
    except ValueError as exc:
        return str(exc)

    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "current_weather": "true"},
    )
    response.raise_for_status()
    current = response.json()["current_weather"]

    temperature = current["temperature"]
    windspeed = current["windspeed"]
    description = WEATHER_CODES.get(current["weathercode"], "unknown conditions")

    return f"{temperature}°C, {description}, wind {windspeed} km/h in {resolved_name}"


def ask(question: str) -> str:
    messages = [{"role": "user", "content": question}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=TOOLS,
        messages=messages,
    )

    while response.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "get_weather":
                result = get_weather(block.input["location"])
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

    return next((block.text for block in response.content if block.type == "text"), "")


if __name__ == "__main__":
    question = input("ask me about the weather: ")
    print(ask(question))

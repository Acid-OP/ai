import os
import math
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load Serper.dev API key
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# 🧰 --- TOOL 1: Web Search using Serper.dev ---
def search_web(query):
    """Search the web using Serper.dev and return the top snippet"""
    try:
        if not SERPER_API_KEY:
            return "❌ SERPER_API_KEY not found. Please set it in your .env file."

        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": query}

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        # Try to extract the most useful text
        if "organic" in data and len(data["organic"]) > 0:
            top = data["organic"][0]
            title = top.get("title", "")
            snippet = top.get("snippet", "")
            link = top.get("link", "")
            return f"{title}: {snippet} ({link})"
        elif "answerBox" in data:
            return data["answerBox"].get("snippet", "No snippet found.")
        else:
            return "No information found online."

    except requests.exceptions.RequestException as e:
        return f"Error searching the web: {e}"


# 🧮 --- TOOL 2: Safe Calculator ---
def calculate(expression):
    """Safely evaluate mathematical expressions"""
    try:
        allowed_names = {
            "sqrt": math.sqrt,
            "pow": math.pow,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "pi": math.pi,
            "e": math.e
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error calculating: {str(e)}"


# 🌦️ --- TOOL 3: Weather via wttr.in ---
def get_weather(city):
    """Get weather information for a city"""
    try:
        url = f"https://wttr.in/{city}?format=%C+%t"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"Weather API error: {response.status_code}"
    except Exception as e:
        return f"Error getting weather: {str(e)}"


# 🧭 --- TOOL REGISTRY ---
TOOLS = {
    "search_web": search_web,
    "calculate": calculate,
    "get_weather": get_weather
}


# 📘 --- TOOL DESCRIPTIONS ---
TOOL_DESCRIPTIONS = """
You have access to these tools:

1. search_web(query: string)
   - Searches the web and returns a relevant summary.
   - Example: search_web("Who invented the telephone")

2. calculate(expression: string)
   - Safely evaluates math expressions.
   - Supports: +, -, *, /, sqrt(), pow(), sin(), cos(), pi, e
   - Example: calculate("sqrt(144) + 5")

3. get_weather(city: string)
   - Returns current weather for a city.
   - Example: get_weather("Berlin")

Use this format when calling a tool:
TOOL: tool_name
INPUT: the input value
REASON: why you're using this tool

When done, provide your final response as:
ANSWER: your final answer to the user
"""

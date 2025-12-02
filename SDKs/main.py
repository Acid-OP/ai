import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("Missing GEMINI_API_KEY")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def main():
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Explain how AI works in a few words",
    )
    print(response.text)


if __name__ == "__main__":
    main()


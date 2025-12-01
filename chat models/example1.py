from langchain_google_genai import GoogleGenerativeAI

from dotenv import load_dotenv

load_dotenv()
# Initialize the model
llm = GoogleGenerativeAI(model="gemini-pro")

# Run inference
response = llm.invoke("What is LangChain?")
print(response)

from langchain_google_genai import GoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
load_dotenv()

llm = GoogleGenerativeAI(model="gemini-pro")

messages = [
    SystemMessage("You are a helpful AI assistant that solves math problems."),
    HumanMessage("What is 81 divided by 9?")
]

result = llm.invoke(messages);
print(result)

 
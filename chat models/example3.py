from langchain_google_genai import GoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage , AIMessage

from dotenv import load_dotenv
load_dotenv()

llm = GoogleGenerativeAI(model="gemini-pro")

chat_history = [];

system_message = SystemMessage(content = "You are a helpful AI assistant")
chat_history.append(system_message)

while True:
    query = input("You: ")
    if query.lower() == "exit":
        break
    chat_history.append(HumanMessage(content=query))

    result = llm.invoke(chat_history)
    response = result
    chat_history.append(AIMessage(content=response))

    print(f"AI: {response}")

print("MESSAGE HISTORY")
print(chat_history)
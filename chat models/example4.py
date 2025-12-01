from langchain_google_genai import GoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from google.cloud import firestore
from langchain_community.memory import FirestoreChatMessageHistory

# from langchain.memory import FirestoreChatMessageHistory
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Firestore Authentication (Set your service account JSON key)
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your-service-account.json"

# Initialize Firestore client
client = firestore.Client()

# Firestore Config
SESSION_ID = "user_session_new"
COLLECTION_NAME = "chat_history"

print("Initializing Firestore client")

# Initialize Firestore chat memory
chat_history = FirestoreChatMessageHistory(
    session_id=SESSION_ID,
    collection=COLLECTION_NAME,
    client=client,
)

print("Chat History Initialized.")
print("Current Chat History:", chat_history.messages)

# Initialize Gemini LLM
llm = GoogleGenerativeAI(model="gemini-pro")

print("Start chatting with the AI. Type 'exit' to quit.")

while True:
    human_input = input("User: ")
    if human_input.lower() == "exit":
        break

    # Add user message to chat history
    chat_history.add_user_message(human_input)

    # Prepare messages for Gemini
    formatted_messages = [
        SystemMessage(content="You are a helpful AI."),
        *chat_history.messages  # Expand past messages
    ]

    # Get AI response
    ai_response = llm.invoke(formatted_messages)

    # Add AI response to chat history
    chat_history.add_ai_message(ai_response.content)

    print(f"AI: {ai_response.content}")

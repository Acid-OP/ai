import google.generativeai as genai
 # Load the key from .env file
genai.configure(api_key="Put your keys here")


# Create the Gemini model (using "gemini-1.5-flash")
model = genai.GenerativeModel("gemini-1.5-flash")

# Chat history to store the conversation
chat_history = []

# Set an initial system message
system_message = "You are a helpful AI assistant."
chat_history.append(f"System: {system_message}")

while True:
    query = input("You: ")
    if query.lower() == "exit":
        break

    # Add user message to chat history
    chat_history.append(f"Human: {query}")

    # Join chat history to create the prompt for Gemini
    prompt = "\n".join(chat_history)

    # Generate response from the model using the chat history as prompt
    response = model.generate_content(prompt)

    # Print AI's response
    print(f"AI: {response.text}")

    # Append AI response to chat history
    chat_history.append(f"AI: {response.text}")

# Optionally, print the full chat history at the end
print("---- Full Message History ----")
for message in chat_history:
    print(message)

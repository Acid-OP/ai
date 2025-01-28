import google.generativeai as genai

# Set up your Gemini API key
genai.configure(api_key="enter your key here")

# Define the prompt with instructions (SystemMessage)
system_message = "Solve the following math problems"

# User’s question (HumanMessage)
human_message = "What is 81 divided by 9?"

# Combine both to create a full prompt
prompt = f"{system_message}\n{human_message}"

# Call the model with the prompt
response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)

# Print the AI's answer (AIMessage)
print(f"Answer from AI: {response.text}")
 
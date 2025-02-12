# Chat Models - README

## Overview

This folder contains four different implementations of AI-powered chat models using Google Gemini via LangChain. These implementations showcase different functionalities, ranging from simple LLM responses to interactive chat history management using Firestore.

## Prerequisites

Before running any script, ensure you have the following installed:

- Python 3.8+
- Required Python packages (install using `pip install -r requirements.txt`)
- A valid Google API key (for Google Generative AI and Firestore, if applicable)
- `.env` file with the API key stored as `GOOGLE_API_KEY`
- Firestore credentials (for the Firestore-backed chat history script)

### Install Required Dependencies

Run the following command to install dependencies:

```sh
pip install langchain langchain-google-genai google-cloud-firestore python-dotenv
```

## Scripts Explanation

### 1. `simple_inference.py`

This script initializes the `GoogleGenerativeAI` model and performs a basic query using the Gemini model.

#### How to Run:

```sh
python simple_inference.py
```

### 2. `interactive_chat.py`

This script enables an interactive chat experience with memory by maintaining the chat history within the session.

#### How to Run:

```sh
python interactive_chat.py
```

Type messages and interact with the AI. Type `exit` to stop the chat.

### 3. `firestore_chat.py`

This script integrates Firestore to store and retrieve chat history, allowing for persistent conversations across sessions.

#### Firestore Setup:

- Set up Firestore in Google Cloud.
- Create a service account and download the JSON key file.
- Set the path to the JSON key file in the script.

#### How to Run:

```sh
python firestore_chat.py
```

## Future Improvements

- Enhance memory capabilities using vector databases.
- Implement different LLMs for comparison.
- Expand with UI integration for real-time chat applications.

---

For any issues, feel free to reach out!


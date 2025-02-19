
# Chat Model with and without Chains

## Overview
This repository demonstrates two implementations of a chat model using LangChain and Google Generative AI (Gemini Pro):
1. **With Chains**: Uses a structured pipeline (prompt → model → output parser) for generating responses.
2. **Without Chains**: Directly invokes the model with a prompt template.

## Features
- **Prompt Engineering**: Uses `ChatPromptTemplate` for structured message formatting.
- **LangChain Integration**: Implements models both with and without chains.
- **Google Generative AI (Gemini-Pro)**: Utilizes Gemini Pro for text generation.
- **Environmental Variables**: Loads API keys securely using `dotenv`.

## Setup
### Prerequisites
- Install dependencies:
  ```sh
  pip install langchain langchain-google-genai python-dotenv
  ```
- Set up a `.env` file with your API key:
  ```sh
  GOOGLE_API_KEY=your_api_key_here
  ```

## Usage
### Running the Chat Model with Chain
This implementation:
- Structures the pipeline using `ChatPromptTemplate`.
- Passes messages through the model via a chain.
- Uses `StrOutputParser` for text output formatting.

Run the script:
```sh
python chat_with_chain.py
```

### Running the Chat Model without Chain
This implementation:
- Directly constructs a prompt template.
- Calls the model without chaining additional components.

Run the script:
```sh
python chat_without_chain.py
```

## Customization
- Modify `prompt_template` to change the chat behavior.
- Adjust `model.invoke()` parameters for different topics or styles.

## Notes
- Ensure your API key is valid and stored correctly in the `.env` file.
- Experiment with different prompt structures for varied responses.

## License
This project is open-source and available under the MIT License.


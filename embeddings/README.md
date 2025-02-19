# Document Embedding and Retrieval using Hugging Face and ChromaDB

## Overview
This project demonstrates how to:
- Read a text document and generate embeddings using a Hugging Face model.
- Store the embeddings in ChromaDB for efficient retrieval.
- Query ChromaDB and retrieve the most relevant chunk of text.
- Use Hugging Face's extractive question-answering model to generate answers from the retrieved text.

## Features
- **Text Chunking**: Splits a document into smaller segments for better embedding and retrieval.
- **Embeddings with Hugging Face**: Generates embeddings using the `sentence-transformers/all-MiniLM-L6-v2` model.
- **Vector Storage with ChromaDB**: Stores and retrieves document chunks based on similarity search.
- **Extractive QA**: Uses the `distilbert-base-cased-distilled-squad` model for answering queries based on the retrieved text.

## Prerequisites
Ensure you have Node.js installed on your system.

### Install Dependencies
```sh
npm install @huggingface/inference chromadb fs path
```

### Set Up API Key
Replace `"put your hugging face api key here"` with your actual Hugging Face API key.

## Usage
### 1. Store Document Chunks in ChromaDB
The script reads the `odf.txt` file, splits it into smaller parts, generates embeddings, and stores them in ChromaDB.
```sh
node index.js
```

### 2. Query the System
After storing the document, the script runs an example query (`"Who is Gaurav?"`). You can modify this in the `runQuery` function.

### 3. Expected Output
- Retrieves the most relevant chunk from ChromaDB.
- Passes it to the QA model to extract an answer.
- Prints the final response.

## File Structure
```
project-folder/
│-- documents/
│   └── odf.txt  # Your input text file
│-- index.js  # Main script
│-- package.json
```

## Customization
- Modify `filePath` to load a different document.
- Change the `chunkSize` in `chunkDocument` function.
- Update the `runQuery` function to take user input dynamically.

## Notes
- Ensure ChromaDB is running or accessible for storing and retrieving embeddings.
- Use a proper API key to avoid request failures.

## License
This project is open-source and available under the MIT License.


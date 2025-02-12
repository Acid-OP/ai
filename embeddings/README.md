# README

## Overview
This project generates text embeddings using Hugging Face's `sentence-transformers/all-MiniLM-L6-v2` model and saves them to a JSON file. The embeddings can be used for various NLP tasks such as similarity search, clustering, and information retrieval.

## Prerequisites
Ensure you have the following installed:
- **Node.js** (Latest LTS recommended)
- **npm or yarn** (for package management)

## Installation
1. Clone the repository:
   ```sh
   git clone <repo_url>
   cd <repo_folder>
   ```
2. Install dependencies:
   ```sh
   npm install @huggingface/inference fs path
   ```

## Project Structure
```
project-root/
│── dist/
|   ├── embeddings.json            # Stores generated embeddings (included in gitignore)
│── src/
│   ├── generateEmbeddings.ts  # Main script for generating embeddings
│── documents/
│   ├── odf.txt                # Sample text file
```

## How It Works
1. Reads the text file from `../documents/odf.txt`.
2. Generates embeddings using the Hugging Face API.
3. Saves the generated embeddings to `embeddings.json`.

## Usage
Run the script to generate and store embeddings:
```sh
node src/generateEmbeddings.js
```

## Configuration
- **Text File Path:** Update `filePath` in `generateEmbeddings.ts` to point to your desired text file.
- **Hugging Face API Key:** Replace the placeholder API key in `HfInference` with your own from [Hugging Face](https://huggingface.co/settings/tokens).

## Example Output
```sh
Extracted Text: "This is an example document..."
Embeddings generated successfully!
Embeddings saved to embeddings.json
```

## Next Steps
- Implement similarity search using cosine similarity.
- Store embeddings in a database instead of a JSON file.
- Expand to multiple documents and chunk-based embeddings.

## License
This project is licensed under the MIT License.


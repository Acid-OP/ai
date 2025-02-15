import { HfInference } from "@huggingface/inference";
import { ChromaClient, IEmbeddingFunction } from "chromadb";
import fs from "fs";
import path from "path";

// Initialize Hugging Face API and ChromaDB client
const hf = new HfInference("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");
const client = new ChromaClient();

// Define paths
const embeddingsPath = path.join(__dirname, "embeddings.json");
const filePath = path.join(__dirname, "../documents/odf.txt");

// Read text file
async function readTextFile(filePath: string): Promise<string> {
    return fs.readFileSync(filePath, "utf-8");
}

// Generate embeddings using Hugging Face
async function getEmbeddings(text: string): Promise<number[]> {
    const embedding = await hf.featureExtraction({
        model: "sentence-transformers/all-MiniLM-L6-v2",
        inputs: text,
    });

    return Array.isArray(embedding[0]) ? (embedding as number[][])[0] : (embedding as number[]); // Ensure embedding is flat
}

// Chunk the document into smaller parts
function chunkDocument(text: string, chunkSize: number): string[] {
    const chunks: string[] = [];
    let startIndex = 0;

    while (startIndex < text.length) {
        let chunk = text.slice(startIndex, startIndex + chunkSize);
        chunks.push(chunk);
        startIndex += chunkSize;
    }

    return chunks;
}

// Define embedding function as a class implementing the IEmbeddingFunction interface
class MyEmbeddingFunction implements IEmbeddingFunction {
    // The embed method which generates embeddings for texts
    async embed(texts: string[]): Promise<number[][]> {
        const embeddings = await Promise.all(
            texts.map(async (text) => {
                return await getEmbeddings(text);
            })
        );
        return embeddings;
    }

    // The required generate method that ChromaDB expects
    async generate(texts: string[]): Promise<number[][]> {
        return this.embed(texts); // Simply call embed and return its result
    }
}

// Store chunks and embeddings in ChromaDB
async function storeInChromaDB(documents: string[], embeddings: number[][]) {
    const collection = await client.getOrCreateCollection({
        name: "my_collection",
        embeddingFunction: new MyEmbeddingFunction(),
    });

    // Generate IDs dynamically for each chunk
    const ids = documents.map((_, index) => `doc_chunk_${index}`);

    // Insert embeddings into ChromaDB
    await collection.upsert({
        ids,
        documents,
        embeddings,
    });

    console.log("Embeddings stored in ChromaDB successfully!");
}

// Query ChromaDB with user input and get multiple matching documents
async function queryChromaDB(query: string) {
    try {
        // Generate embedding for the query
        const queryEmbedding = await getEmbeddings(query);
        console.log("Query Embedding Generated!");

        // Get collection from ChromaDB
        const collection = await client.getCollection({
            name: "my_collection",
            embeddingFunction: new MyEmbeddingFunction(),
        });

        // Perform similarity search and fetch top 3 results
        const results = await collection.query({
            queryEmbeddings: [queryEmbedding], // Search with the generated embedding
            nResults: 3, // Retrieve top 3 closest matches
        });

        // Extract the best-matching documents (chunks)
        if (results.documents && results.documents.length > 0) {
            console.log("Best Matches:", results.documents);
            return results.documents[0]; // Return the closest document/chunk
        } else {
            console.log("No matching document found.");
            return "No relevant answer found.";
        }
    } catch (error) {
        console.error("Error querying ChromaDB:", error);
        return "Error retrieving answer.";
    }
}

// Implement QA using Hugging Face model for extractive question answering
async function getAnswerFromQAModel(question: string, context: string): Promise<string> {
    const result = await hf.questionAnswering({
        model: "distilbert-base-cased-distilled-squad",
        inputs: { question, context },
    });
    return result.answer;
}

// Query ChromaDB and use the QA model for extracting the answer
async function queryChromaDBWithQA(query: string) {
    try {
        // Generate embedding for the query
        const queryEmbedding = await getEmbeddings(query);
        console.log("Query Embedding Generated!");

        // Get collection from ChromaDB
        const collection = await client.getCollection({
            name: "my_collection",
            embeddingFunction: new MyEmbeddingFunction(),
        });

        // Perform similarity search and fetch top 3 results
        const results = await collection.query({
            queryEmbeddings: [queryEmbedding], // Search with the generated embedding
            nResults: 3, // Retrieve top 3 chunks for better context
        });

        // Extract the best-matching chunk and answer the question
        if (results.documents && results.documents.length > 0) {
            const bestMatch = results.documents[0][0]; // Get the best matching chunk
            if (bestMatch) {
                // Use the best match to get the answer from the QA model
                const answer = await getAnswerFromQAModel(query, bestMatch);
                console.log("Answer:", answer);
                return answer; // Return the extracted answer
            } else {
                console.log("Best match is null.");
                return "No relevant answer found.";
            }
        } else {
            console.log("No matching document found.");
            return "No relevant answer found.";
        }
    } catch (error) {
        console.error("Error querying ChromaDB:", error);
        return "Error retrieving answer.";
    }
}

// Example: Run a query
async function runQuery() {
    const userQuery = "Who is the father of Naruto?"; // Example input
    const answer = await queryChromaDBWithQA(userQuery); // Use the QA approach
    console.log("Answer:", answer);
}

runQuery(); // Call this function to test querying and QA

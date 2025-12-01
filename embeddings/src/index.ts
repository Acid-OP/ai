import { HfInference } from "@huggingface/inference";
import { ChromaClient, IEmbeddingFunction } from "chromadb";
import fs from "fs";
import path from "path";

// Initialize Hugging Face API and ChromaDB client
const hf = new HfInference("put your hugging face api key here ");
const client = new ChromaClient();

// Define paths
const filePath = path.join(__dirname, "../documents/odf.txt");

// Read text file
const text = fs.readFileSync(filePath, "utf-8");

// Generate embeddings using Hugging Face
async function getEmbeddings(text: string): Promise<number[]> {
    const embedding = await hf.featureExtraction({
        model: "sentence-transformers/all-MiniLM-L6-v2",
        inputs: text,
    });

    return Array.isArray(embedding[0]) ? (embedding as number[][])[0] : (embedding as number[]);
}

// Chunk the document into smaller parts
function chunkDocument(text: string, chunkSize: number = 500): string[] {
    const chunks = [];
    for (let i = 0; i < text.length; i += chunkSize) {
        chunks.push(text.slice(i, i + chunkSize));
    }
    return chunks;
}

// Define embedding function for ChromaDB
class MyEmbeddingFunction implements IEmbeddingFunction {
    async embed(texts: string[]): Promise<number[][]> {
        return Promise.all(texts.map(getEmbeddings));
    }

    async generate(texts: string[]): Promise<number[][]> {
        return this.embed(texts);
    }
}

// Store chunks and embeddings in ChromaDB
async function storeInChromaDB(chunks: string[]) {
    const collection = await client.getOrCreateCollection({
        name: "my_collection",
        embeddingFunction: new MyEmbeddingFunction(),
    });

    const embeddings = await Promise.all(chunks.map(getEmbeddings));
    const ids = chunks.map((_, index) => `chunk_${index}`);

    await collection.upsert({ ids, documents: chunks, embeddings });
    console.log("Embeddings stored in ChromaDB successfully!");
}

// Query ChromaDB
async function queryChromaDB(query: string) {
    const queryEmbedding = await getEmbeddings(query);
    const collection = await client.getCollection({
        name: "my_collection",
        embeddingFunction: new MyEmbeddingFunction(),
    });

    const results = await collection.query({
        queryEmbeddings: [queryEmbedding],
        nResults: 3,
    });

    return results.documents?.[0]?.[0] || "No relevant answer found.";
}

// Extractive QA using Hugging Face
async function getAnswerFromQAModel(question: string, context: string): Promise<string> {
    const result = await hf.questionAnswering({
        model: "distilbert-base-cased-distilled-squad",
        inputs: { question, context },
    });
    return result.answer;
}

// Query ChromaDB and extract the answer
async function queryChromaDBWithQA(query: string) {
    const bestMatch = await queryChromaDB(query);
    return bestMatch !== "No relevant answer found." ? await getAnswerFromQAModel(query, bestMatch) : bestMatch;
}

// Example: Run a query
async function runQuery() {
    const userQuery = "Who is gaurav?";
    console.log("Answer:", await queryChromaDBWithQA(userQuery));
}

storeInChromaDB(chunkDocument(text)).then(runQuery);

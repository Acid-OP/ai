import { HfInference } from "@huggingface/inference";
import { ChromaClient } from "chromadb";
import fs from "fs";
import path from "path";

// Initialize HF API and ChromaDB client
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

    // Ensure it is always a flat number[] array
    return Array.isArray(embedding[0]) ? (embedding as number[][])[0] : (embedding as number[]);
}

// Store embeddings in ChromaDB
async function storeInChromaDB(documents: string[], embeddings: number[][]) {
    const collection = await client.getOrCreateCollection({ name: "my_collection" });

    // Generate IDs dynamically
    const ids = documents.map((_, index) => `doc_${index}`);

    // Insert embeddings into ChromaDB
    await collection.upsert({
        ids,
        documents,
        embeddings,
    });

    console.log("Embeddings stored in ChromaDB successfully!");
}

// Generate and save embeddings
async function saveEmbeddings() {
    try {
        const text = await readTextFile(filePath);
        console.log("Extracted Text:", text.slice(0, 500)); // Show first 500 chars

        const embeddings = await getEmbeddings(text);
        console.log("Embeddings generated successfully!");

        // Save embeddings and document text
        const data = { documents: [text], embeddings: [embeddings] };
        fs.writeFileSync(embeddingsPath, JSON.stringify(data, null, 2));
        console.log(`Embeddings saved to ${embeddingsPath}`);

        // Store in ChromaDB
        await storeInChromaDB([text], [embeddings]);
    } catch (error) {
        console.error("Error:", error);
    }
}

// Run function
saveEmbeddings();

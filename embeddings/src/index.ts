import { HfInference } from "@huggingface/inference";
import fs from "fs";
import path from "path";

// Initialize HF API
const hf = new HfInference("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");

// Path for storing embeddings
const embeddingsPath = path.join(__dirname, "embeddings.json");

// Text file path
const filePath = path.join(__dirname, "../documents/odf.txt");

// Read the text file
async function readTextFile(filePath: string): Promise<string> {
    return fs.readFileSync(filePath, "utf-8");
}

// Generate embeddings
async function getEmbeddings(text: string) {
    return await hf.featureExtraction({
        model: "sentence-transformers/all-MiniLM-L6-v2",
        inputs: text,
    });
}

// Save embeddings to a JSON file
async function saveEmbeddings() {
    try {
        const text = await readTextFile(filePath);
        console.log("Extracted Text:", text.slice(0, 500)); // Show first 500 chars

        const embeddings = await getEmbeddings(text);
        console.log("Embeddings generated successfully!");

        fs.writeFileSync(embeddingsPath, JSON.stringify(embeddings, null, 2));
        console.log(`Embeddings saved to ${embeddingsPath}`);
    } catch (error) {
        console.error("Error:", error);
    }
}

// Run the function
saveEmbeddings();

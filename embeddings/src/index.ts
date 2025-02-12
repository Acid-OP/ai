import { HfInference } from "@huggingface/inference";
import dotenv from "dotenv";

dotenv.config();

const hf = new HfInference(process.env.HF_TOKEN as string); // ✅ Secure

async function main() {
    const output = await hf.featureExtraction({
        model: "sentence-transformers/all-MiniLM-L6-v2",
        inputs: "That is a happy person",
    });

    console.log(output);
}

main();

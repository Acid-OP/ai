import { HfInference } from "@huggingface/inference";

const hf = new HfInference("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");

async function main() {
    const output = await hf.featureExtraction({
        model: "sentence-transformers/all-MiniLM-L6-v2",
        inputs: "That is a happy person",
    });

    console.log(output);
}

main();

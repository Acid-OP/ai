import { ChromaClient } from "chromadb";

async function run() {
    const client = new ChromaClient();

    // Get or create the collection
    const collection = await client.getOrCreateCollection({
        name: "my_collection",
    });

    // Upsert documents
    await collection.upsert({
        documents: [
            "This is a document about pineapple",
            "This is a document about oranges",
        ],
        ids: ["id1", "id2"],
        
    });

    // Query the collection
    const results = await collection.query({
        queryTexts: "This is a query document about florida", // Chroma will embed this for you
        nResults: 2, // How many results to return
    });

    console.log(results);
}

// Call the async function to execute
run().catch((error) => console.error("Error:", error));

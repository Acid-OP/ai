const express = require("express");
const cors = require("cors"); // Import the CORS package
const bodyParser = require("body-parser");
const { GoogleGenerativeAI } = require("@google/generative-ai");
require("dotenv").config();

const genAI = new GoogleGenerativeAI(process.env.API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

const app = express();

// Enable CORS for all origins
app.use(cors());

app.use(express.json());
app.use(bodyParser.json());

const generate = async (prompt) => {
  try {
    const result = await model.generateContent(prompt);
    return result.response.text();
  } catch (err) {
    console.error(err);
    throw new Error("Error generating content.");
  }
};

app.get("/api/content", async (req, res) => {
  try {
    const data = req.query.query; // Extract query parameter
    const result = await generate(data);
    res.send({
      result: result,
    });
  } catch (err) {
    res.status(500).send(err.message);
  }
});

app.listen(3000, () => {
  console.log("Server running on http://localhost:3000");
});

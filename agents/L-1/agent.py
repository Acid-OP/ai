import os
from dotenv import load_dotenv
import google.generativeai as genai
from tools import TOOLS, TOOL_DESCRIPTIONS

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Choose your Gemini model — 'gemini-2.5-flash' is fast and free
MODEL_NAME = "gemini-2.5-flash"


class Agent:
    def __init__(self):
        self.model = genai.GenerativeModel(MODEL_NAME)
        self.conversation_history = []
        self.max_iterations = 10  # Prevent infinite loops

    def call_llm(self, messages):
        """Call Gemini model with conversation history."""
        # Convert messages into plain text prompt for Gemini
        prompt = "\n".join(
            [f"{msg['role'].upper()}: {msg['content']}" for msg in messages]
        )
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def parse_llm_response(self, response):
        """Parse LLM response to extract tool calls or final answer."""
        response = response.strip()

        if "ANSWER:" in response:
            answer = response.split("ANSWER:")[1].strip()
            return {"type": "answer", "content": answer}

        if "TOOL:" in response and "INPUT:" in response:
            lines = response.split("\n")
            tool_name, tool_input, reason = None, None, None

            for line in lines:
                if line.startswith("TOOL:"):
                    tool_name = line.split("TOOL:")[1].strip()
                elif line.startswith("INPUT:"):
                    tool_input = line.split("INPUT:")[1].strip()
                elif line.startswith("REASON:"):
                    reason = line.split("REASON:")[1].strip()

            if tool_name and tool_input:
                return {
                    "type": "tool_call",
                    "tool": tool_name,
                    "input": tool_input,
                    "reason": reason,
                }

        return {"type": "thought", "content": response}

    def execute_tool(self, tool_name, tool_input):
        """Execute a tool and return the result."""
        if tool_name in TOOLS:
            print(f"  🔧 Using tool: {tool_name}")
            print(f"  📥 Input: {tool_input}")
            result = TOOLS[tool_name](tool_input)
            print(f"  📤 Result: {result}\n")
            return result
        else:
            return f"Error: Tool '{tool_name}' not found"

    def run(self, user_question):
        """Main agent loop."""
        print(f"❓ User Question: {user_question}\n")
        print("=" * 60)

        self.conversation_history = [
            {
                "role": "system",
                "content": f"You are a helpful AI agent that can use tools to answer questions.\n\n{TOOL_DESCRIPTIONS}\n\nThink step by step. Use tools when needed. When you have the final answer, use ANSWER: format.",
            },
            {"role": "user", "content": user_question},
        ]

        for iteration in range(self.max_iterations):
            print(f"🔄 Iteration {iteration + 1}")
            print("-" * 60)

            llm_response = self.call_llm(self.conversation_history)
            print(f"🤖 Agent: {llm_response}\n")

            parsed = self.parse_llm_response(llm_response)

            if parsed["type"] == "answer":
                print("=" * 60)
                print(f"✅ FINAL ANSWER: {parsed['content']}")
                return parsed["content"]

            elif parsed["type"] == "tool_call":
                self.conversation_history.append(
                    {"role": "assistant", "content": llm_response}
                )
                result = self.execute_tool(parsed["tool"], parsed["input"])
                self.conversation_history.append(
                    {"role": "user", "content": f"Tool result: {result}"}
                )

            elif parsed["type"] == "thought":
                self.conversation_history.append(
                    {"role": "assistant", "content": llm_response}
                )
                self.conversation_history.append(
                    {"role": "user", "content": "Continue. What's your next action?"}
                )

        print("⚠️ Max iterations reached!")
        return "I couldn't complete the task within the iteration limit."


if __name__ == "__main__":
    agent = Agent()

    print("\n" + "=" * 60)
    print("TEST 1: Multi-step reasoning")
    print("=" * 60 + "\n")
    agent.run("What's the weather like in the birthplace of Albert Einstein?")

    print("\n\n" + "=" * 60)
    print("TEST 2: Calculation + Search")
    print("=" * 60 + "\n")
    agent = Agent()  # Reset agent
    agent.run("Calculate the square root of 144, then search Wikipedia for that number")

    print("\n\n" + "=" * 60)
    print("TEST 3: Complex reasoning")
    print("=" * 60 + "\n")
    agent = Agent()  # Reset agent
    agent.run("Who invented the telephone? Calculate their birth year plus 100.")

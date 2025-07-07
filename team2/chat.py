import os
import asyncio
import gradio as gr
from dotenv import load_dotenv

from mcp_use import MCPClient, MCPAgent
from langchain_groq import ChatGroq # Changed from langchain_openai import ChatOpenAI

# Load .env
load_dotenv()

# MCP Config
MCP_CONFIG = {
    "mcpServers": {
        "sqlite": {
            "command": "npx",
            "args": [
                "-y",
                "@executeautomation/database-server",
                "D:\\llm\\test.db"
            ]
        }
    }
}

# Load Agent once
agent = None
def setup_agent():
    global agent
    if agent is None:
        client = MCPClient.from_dict(MCP_CONFIG)
        # Changed from ChatOpenAI to ChatGroq
        # Choose a Groq model. 'llama-3.3-70b-versatile' is a strong option for complex tasks,
        # 'llama-3.1-8b-instant' is faster for simpler tasks.
        # Ensure GROQ_API_KEY is set in your .env file or environment variables.
        llm = ChatGroq(
            model_name="llama-3.3-70b-versatile", # Using a powerful Groq model
            # Groq API key is typically loaded from the environment variable GROQ_API_KEY
            # You can explicitly pass it if needed, but using os.getenv is recommended.
            groq_api_key=os.getenv("GROQ_API_KEY") # No need for a placeholder like "sk-..."
        )
        agent = MCPAgent(llm=llm, client=client, max_steps=10)

setup_agent()

# Chat function
def answer_query(user_input):
    try:
        if not user_input.strip():
            return "⛔ தயவுசெய்து ஒரு கேள்வியை உள்ளிடவும்."

        result = asyncio.run(agent.run(user_input))
        return f"✅ பதில்:\n\n{result}"
    except Exception as e:
        import traceback
        return f"❌ பிழை:\n{e}\n\n{traceback.format_exc()}"

# Gradio UI
iface = gr.Interface(
    fn=answer_query,
    inputs=gr.Textbox(label="உங்கள் கேள்வி (தமிழிலும் OK)"),
    outputs="text",
    title="🧠 NL2SQL Chat - Gradio + LangChain + MCP (Groq Powered)",
    description="SQLite-ல் இருந்து SQL பதில்களை MCP மூலம் பெறுங்கள்"
)

iface.launch()
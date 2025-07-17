import json
import sqlite3
from typing import List
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.agents import AgentAction
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import tool

@tool("database")
def database_tool(query: str) -> str:
    """
    Use this tool to execute a SQLite query on the 'course_registrations' table.
    The table schema is (id, name, course, age, qualification, city, timestamp).
    Example Action Input: SELECT name, age FROM course_registrations WHERE city = 'New York';
    """
    # This function's body is a placeholder. The actual execution logic
    # is handled within the MCPAgent's run method.
    pass

class MCPAgent:
    def __init__(self, llm: BaseChatModel, max_steps: int = 5):
        self.llm = llm
        self.max_steps = max_steps
        self.llm_with_tools = self.llm.bind_tools([database_tool])

    async def run(self, chat_history: List[BaseMessage]) -> str:
        """
        Runs the agent to answer a question, now using conversation history.
        """
        intermediate_steps = []
        
        # The prompt is now the entire chat history
        prompt = chat_history
        
        for i in range(self.max_steps):
            try:
                print(f"\n--- Agent Step {i+1} ---")
                print(f"Current History/Prompt: {prompt}")
                ai_message = self.llm_with_tools.invoke(prompt, config={"intermediate_steps": intermediate_steps})
            except Exception as e:
                print(f"Error invoking LLM: {e}")
                return f"Error calling the language model: {e}"

            if not ai_message.tool_calls:
                if ai_message.content:
                    return ai_message.content
                else:
                    return "Agent stopped: It gathered information but could not form a final answer."

            tool_call = ai_message.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call.get("id")

            if tool_name == "database":
                try:
                    conn = sqlite3.connect('va.db')
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    sql_query = tool_args.get('query')
                    print(f"Executing query: {sql_query}")
                    cursor.execute(sql_query)
                    results = cursor.fetchall()
                    conn.close()
                    
                    if not results:
                        observation = "Query executed successfully, but returned no results."
                    else:
                        observation = json.dumps([dict(row) for row in results])
                except Exception as e:
                    observation = f"Error executing query: {e}"

                print(f"Observation: {observation}")
                
                # **CRITICAL FIX**: Append the AI's tool call and the resulting observation
                # as proper message types, not raw strings.
                prompt.append(ai_message)
                prompt.append(ToolMessage(content=observation, tool_call_id=tool_call_id))
                
            else:
                return f"Unknown tool: {tool_name}"

        return "Agent stopped after reaching max steps."
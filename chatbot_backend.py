from langgraph.graph import StateGraph,START, END
import operator
from typing import TypedDict, Any, Optional,Literal,Annotated,List
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import operator
import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage,ToolMessage
from langgraph.graph.message import add_messages
from langchain_tavily import TavilySearch
from langchain_core.tools import Tool
from langgraph.checkpoint.memory import MemorySaver,InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver,sqlite3
from langchain.agents import AgentExecutor, create_react_agent

load_dotenv()
llm=ChatOpenAI(model='gpt-4o-mini')

tavily_tool = TavilySearch(max_results=5)
tools = [tavily_tool]

# Create a prompt for the agent
prompt = PromptTemplate.from_template("""
You are a helpful assistant with access to the following tools:

{tools}

To use a tool, you must follow this format:

Thought: Do I need to use a tool? Yes
Action: the name of the tool to use, should be one of [{tool_names}]
Action Input: the input to the tool
Observation: the result of the tool

When you have the final answer, use this format:

Thought: I have the final answer
Final Answer: the final answer


Begin!
Question: {input}
{agent_scratchpad}
""")

# Create the agent
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools,verbose=False)


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage],add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    
    # Check if the last message is a ToolMessage
    if isinstance(messages[-1], ToolMessage):
        # If it's a tool message, it's a continuation of a tool call
        result = agent_executor.invoke({'input': messages[-2].content})
    else:
        # Otherwise, it's a new conversation
        result = agent_executor.invoke({'input': messages[-1].content})

    return {'messages': [AIMessage(content=result['output'])]}
  
def should_continue(state: ChatState) -> Literal["tool", "__end__"]:
    messages = state['messages']
    last_message = messages[-1]
    
    # If the last message is an AI message with tool calls, it's a tool-using step
    if "function_call" in last_message.additional_kwargs:
        return "tool"
    
    return "__end__"

# Define the new node for tool calling
def tool_node(state: ChatState) -> dict:
    messages = state['messages']
    last_message = messages[-1]
    
    # Get the function call from the message
    function_call = last_message.additional_kwargs["function_call"]
    tool_name = function_call["name"]
    tool_args = json.loads(function_call["arguments"])
    
    # Find the tool and execute it
    tool_to_run = {tool.name: tool for tool in tools}[tool_name]
    observation = tool_to_run.invoke(tool_args)
    
    return {'messages': [ToolMessage(content=str(observation), name=tool_name)]}


def retrive_all_threads():
    all_threads=set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)

conn= sqlite3.connect(database='chatbot.db',check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("agent", chat_node)
graph.add_node("call_tool", tool_node)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tool": "call_tool", "__end__": END})
graph.add_edge("call_tool", "agent")
ChatBot=graph.compile(checkpointer=checkpointer)

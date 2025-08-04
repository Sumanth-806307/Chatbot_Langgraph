from langgraph.graph import StateGraph,START, END
import operator
from typing import TypedDict, Any, Optional,Literal,Annotated,List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import operator
import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver,InMemorySaver

load_dotenv()
llm=ChatOpenAI(model='gpt-4o-mini')
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage],add_messages]
    
def chat_node(state:ChatState):
    messages = state['messages']
    prompt = f"You are a helpful assistant. Answer the user's question based on the provided messages in crisp and short.{messages}"
    response = llm.invoke(prompt)
    return {'messages': [response]}

checkpointer = InMemorySaver()

graph = StateGraph(ChatState)
graph.add_node('chat_node',chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)
ChatBot=graph.compile(checkpointer=checkpointer)

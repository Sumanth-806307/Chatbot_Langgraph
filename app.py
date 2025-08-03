import streamlit as st
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

## Backend
load_dotenv()
llm=ChatOpenAI(model='gpt-4o-mini')
class ChatBot(TypedDict):
    messages:Annotated[List[BaseMessage],add_messages]
    
def chat_node(state:ChatBot):
    messages = state['messages']
    prompt = f"You are a helpful assistant. Answer the user's question based on the provided messages in crisp and short.{messages}"
    response = llm.invoke(prompt)
    return {'messages': [response]}

checkpointer = MemorySaver()

graph = StateGraph(ChatBot)
graph.add_node('chat_node',chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)
ChatBot=graph.compile(checkpointer=checkpointer)

thread_id='1'
config={'configurable':{'thread_id':thread_id}}

if 'message_history' not in st.session_state:
    st.session_state['message_history']=[]

for messages in st.session_state['message_history']:
    with st.chat_message(messages['role']):
        st.text(messages['content'])
        
user_input=st.chat_input("Type Here")

if user_input:
    st.session_state['message_history'].append({'role':'user','content':user_input})
    with st.chat_message("user"):
        st.text(user_input)
    
    response = ChatBot.invoke({'messages':[HumanMessage(content=user_input)]}, config=config)
    st.session_state['message_history'].append({'role':'assistant','content':response['messages'][-1].content})    
    with st.chat_message("assistant"):
        st.text(response['messages'][-1].content)
        



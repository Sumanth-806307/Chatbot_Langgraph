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
from chatbot_backend import ChatBot
import uuid

# Initialize a unique thread ID for the user if it doesn't already exist
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = str(uuid.uuid4())

# Use the unique thread ID for the LangGraph configuration
config = {'configurable': {'thread_id': st.session_state['thread_id']}}

if 'message_history' not in st.session_state:
    st.session_state['message_history']=[]

for messages in st.session_state['message_history']:
    with st.chat_message(messages['role']):
        st.text(messages['content'])
        
user_input= st.chat_input("Type Here")

if user_input:
    st.session_state['message_history'].append({'role':'user','content':user_input})
    with st.chat_message("user"):
        st.text(user_input)
    
    response = ChatBot.invoke({'messages':[HumanMessage(content=user_input)]}, config=config)
    ai_message=response['messages'][-1].content
    st.session_state['message_history'].append({'role':'assistant','content':ai_message})    
    with st.chat_message("assistant"):
        st.text(ai_message)
        



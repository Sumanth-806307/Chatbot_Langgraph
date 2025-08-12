import streamlit as st
from langgraph.graph import StateGraph, START, END
import operator
from typing import TypedDict, Any, Optional, Literal, Annotated, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from chatbot_backend import ChatBot,retrive_all_threads
import uuid

# Load environment variables
load_dotenv()

# ------------ utility Function-----------------

def generate_thread_id():
    """Generates a unique UUID for a new chat thread."""
    return str(uuid.uuid4())

def reset_chat():
    """Resets the current chat session by creating a new thread ID."""
    st.session_state['thread_id'] = generate_thread_id()
    st.session_state['message_history'] = []
    # Add the new thread to the list of conversations
    if st.session_state['thread_id'] not in st.session_state['chat_threads']:
        st.session_state['chat_threads'][st.session_state['thread_id']] = "New Chat"

def load_conversation(thread_id):
    """Loads a conversation from a given thread ID."""
    state=ChatBot.get_state(config={'configurable': {'thread_id': thread_id}})
    if state:
        return state.values['messages']
    return []

def load_last_conversation(thread_id):
    """Loads a conversation from a given thread ID and returns a label for the sidebar."""
    state = ChatBot.get_state(config={'configurable': {'thread_id': thread_id}})
    if state and state.values['messages']:
        messages = state.values['messages']
        # If there are at least two messages, return the second-to-last message (the last user message).
        # Otherwise, return the very first message as the label.
        if len(messages) >= 2:
            return messages[-2].content
        else:
            return messages[0].content
    return []
    #return ChatBot.get_state(config={'configurable': {'thread_id': thread_id}}).values['messages']

# -----------------------------

# Initialize session state variables
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
    
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = {}
    existing_threads = retrive_all_threads()
    
    if existing_threads:
        for thread_id in existing_threads:
            st.session_state['chat_threads'][thread_id] = load_last_conversation(thread_id)
        st.session_state['thread_id'] = existing_threads[-1]
        st.session_state['message_history'] = load_conversation(st.session_state['thread_id'])
    else:
        st.session_state['chat_threads'][st.session_state['thread_id']] = "New Chat"

    
# Ensure the current thread is in the list of threads
if st.session_state['thread_id'] not in st.session_state['chat_threads']:
    st.session_state['chat_threads'][st.session_state['thread_id']] = "New Chat"

# --------UI------------
st.sidebar.title('Langgraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header("My conversations")

# Use a dictionary to store thread IDs and their corresponding button labels
# We'll update the labels as conversations progress
for thread_id, label in reversed(st.session_state['chat_threads'].items()):
    if st.sidebar.button(label, key=thread_id):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)
        
        # Format and display the loaded messages
        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({"role": role, 'content': msg.content})
        st.session_state['message_history'] = temp_messages

# Display the current chat history
try:
    for message in st.session_state['message_history']:
        with st.chat_message(message['role']):
            st.text(message['content'])
except:
    pass
user_input = st.chat_input("Type Here")

        
if user_input:
    config = {'configurable': {'thread_id': st.session_state['thread_id']}}
    
    # Update the button label with the first user input
    if st.session_state['chat_threads'][st.session_state['thread_id']] == "New Chat":
        st.session_state['chat_threads'][st.session_state['thread_id']] = user_input
    
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message("user"):
        st.text(user_input)
    
    with st.chat_message("assistant"):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in 
            ChatBot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=config,
                stream_mode='messages'
            )
        )
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
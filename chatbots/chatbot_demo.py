"""
Streamlit Chatbot Demo Application.

This module provides a web-based chatbot interface using Streamlit,
powered by Amazon Bedrock and the Strands SDK. Users can select from
various text generation models, adjust temperature settings, and have
conversations with AI models through a clean chat interface.

Features:
- Model selection from available Bedrock text models
- Temperature control for response generation
- Persistent chat history within session
- Model information display
- Clear chat functionality
"""

import os
# Add project root to Python path
import sys

import boto3
import streamlit as st
from strands import Agent
from strands.models import BedrockModel

sys.path.append('../')
from util.model_selector import MODELS

# Page config
st.set_page_config(page_title="Strands Chatbot Demo", page_icon="🤖")

# Title
st.title("🤖 Strands SDK Chatbot Demo")
st.markdown("Powered by Amazon Bedrock and Strands SDK")

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # Create model options from our unified system
    text_models = {name: info for name, info in MODELS.items() 
                   if info['type'] == 'text'}
    
    model_options = {}
    for model_id, info in text_models.items():
        display_name = f"{info['name']} - {info['description'][:50]}..."
        model_options[display_name] = model_id
    
    # Model selection using our unified system
    selected_display_name = st.selectbox(
        "Select Model",
        options=list(model_options.keys()),
        help="Choose from available text generation models"
    )
    
    model_id = model_options[selected_display_name]
    
    # Display model info
    selected_model_info = text_models[model_id]
    
    with st.expander("Model Details"):
        st.write(f"**Name:** {selected_model_info['name']}")
        st.write(f"**Family:** {selected_model_info['family']}")
        st.write(f"**Description:** {selected_model_info['description']}")
        if 'max_tokens' in selected_model_info:
            st.write(f"**Max Tokens:** {selected_model_info['max_tokens']:,}")
    
    # Temperature
    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.1)
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.agent = None
        st.rerun()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize agent when model changes
if "agent" not in st.session_state or st.session_state.get("current_model") != model_id:
    try:
        st.session_state.current_model = model_id

        boto3_session = boto3.session.Session()
        region = boto3_session.region_name or "us-east-1"
        
        bedrock_model = BedrockModel(
            model_id=st.session_state.current_model,
            temperature=temperature,
            region=region
        )

        st.session_state.agent = Agent(
            system_prompt="You are a helpful AI assistant. Be conversational and maintain context throughout our chat.",
            model=bedrock_model
        )

        # Show success message
        st.success(f"✅ Initialized with {selected_model_info['name']}")

    except Exception as e:
        st.error(f"Error initializing agent: {str(e)}")
        st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to chat about?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.agent(prompt)
                st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.markdown("---")
st.markdown("💡 **Tip**: The agent maintains conversation context automatically!")

import os
import dotenv
from openai import OpenAI
import streamlit as st
import input_page, chatbot_page

# Load environment variables
dotenv.load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Streamlit app configuration
st.set_page_config(page_title="Gendonk", page_icon="📖")

selected_tab = st.sidebar.selectbox("Select Tab:", ["Input", "Chatbot"])

if selected_tab == "Input":
    input_page.index(client)
    
elif selected_tab == "Chatbot":
    chatbot_page.index(client)
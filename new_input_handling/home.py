import streamlit as st
import requests
import json

st.set_page_config(layout="wide")
st.title("✈️ Flight Booking Assistant")

# Initialize session state variables
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'is_complete' not in st.session_state:
    st.session_state.is_complete = False
if 'flight_info' not in st.session_state:
    st.session_state.flight_info = {}

# Function to start a new chat
def new_chat():
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.is_complete = False
    st.session_state.flight_info = {}
    # Make initial call to get the welcome message
    try:
        response = requests.post(
            "http://127.0.0.1:8000/chat",
            json={"content": "", "session_id": None}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.session_id = data["session_id"]
            st.session_state.messages.append({"role": "assistant", "content": data["response"]})
        else:
            st.error("Failed to start a new chat. Is the backend running?")
            st.error(f"Status: {response.status_code}, Body: {response.text}")

    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the backend. Please make sure it's running.")

# Layout 
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Conversation")
    
    # Start a new chat if it's the first run
    if not st.session_state.messages:
        new_chat()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if not st.session_state.is_complete:
        if prompt := st.chat_input("Your message..."):
            # Add user message to UI
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Send to backend and get response
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/chat",
                    json={"content": prompt, "session_id": st.session_state.session_id}
                )
                if response.status_code == 200:
                    data = response.json()
                    # Add assistant response to UI
                    with st.chat_message("assistant"):
                        st.markdown(data["response"])
                    st.session_state.messages.append({"role": "assistant", "content": data["response"]})
                    
                    # Update session state
                    st.session_state.session_id = data["session_id"]
                    st.session_state.is_complete = data["is_complete"]
                    st.session_state.flight_info = data["flight_info"]
                    
                    # Rerun to update the flight info display and check completion status
                    st.rerun()

                else:
                    st.error("Error communicating with the backend.")
                    st.error(f"Status: {response.status_code}, Body: {response.text}")
            
            except requests.exceptions.ConnectionError:
                st.error("Connection Error: Could not connect to the backend. Please make sure it's running.")
    else:
        st.success("Conversation complete! The booking data has been saved.")
        st.info("Click 'Start New Chat' to begin another booking.")

with col2:
    st.subheader("Collected Information")
    st.button("Start New Chat", on_click=new_chat)
    
    # Display the collected flight info as a JSON object
    st.json(st.session_state.flight_info)
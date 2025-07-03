import streamlit as st
import requests

st.title("flight booking chat")

# Simple chat input
user_input = st.text_input("type your message:")

if st.button("send"):
    if user_input:
        # Send to FastAPI backend
        try:
            response = requests.post(
                "http://localhost:8000/chat",
                json={"role": "user", "content": user_input}
            )
            
            if response.status_code == 200:
                data = response.json()
                st.write("**flight travel agent guy:**", data["response"])
            else:
                st.error("Error connecting to backend")
        except:
            st.error("cannot connect to backend")
    else:
        st.warning("please enter a message") 
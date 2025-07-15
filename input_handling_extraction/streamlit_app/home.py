import streamlit as st
import requests
import pandas as pd

st.title("Flight Booking Chat")

# Add tabs for different sections
tab1, tab2 = st.tabs(["Chat", "User Management"])

with tab1:
    # session state - memory system
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "flight_info" not in st.session_state:
        st.session_state.flight_info = {}
    if "current_user" not in st.session_state:
        st.session_state.current_user = None

    # User login section
    st.sidebar.markdown("### User Login")
    
    # Simple login form
    with st.sidebar.form("login_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("Register"):
                if username and email:
                    response = requests.post(
                        "http://localhost:8000/users/register",
                        json={"username": username, "email": email}
                    )
                    if response.status_code == 200:
                        st.success("User registered!")
                        st.session_state.current_user = username
                    else:
                        st.error("Registration failed")
        
        with col2:
            if st.form_submit_button("Login"):
                if username:
                    response = requests.post(
                        f"http://localhost:8000/users/login",
                        params={"username": username}
                    )
                    if response.status_code == 200:
                        st.success("Login successful!")
                        st.session_state.current_user = username
                    else:
                        st.error("Login failed")
    
    # Show current user
    if st.session_state.current_user:
        st.sidebar.markdown(f"**Logged in as:** {st.session_state.current_user}")
        if st.sidebar.button("Logout"):
            st.session_state.current_user = None
            st.rerun()

    # display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # chat input
    if prompt := st.chat_input("type your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        try:
            request_data = {"role": "user", "content": prompt}
            if st.session_state.session_id:
                request_data["session_id"] = st.session_state.session_id
            if st.session_state.current_user:
                request_data["username"] = st.session_state.current_user
            response = requests.post(
                "http://localhost:8000/chat",
                json=request_data
            )
            if response.status_code == 200:
                data = response.json()
                assistant_response = data["response"]
                st.session_state.session_id = data.get("session_id")
                st.session_state.flight_info = data.get("flight_info", {})
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                with st.chat_message("assistant"):
                    st.markdown(assistant_response)
            else:
                st.error("Error connecting to backend")
        except Exception as e:
            st.error(f"Cannot connect to backend: {e}")

    if st.sidebar.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.session_state.flight_info = {}
        st.rerun()

    st.sidebar.markdown("**Instructions:**")
    st.sidebar.markdown("- Ask about flight booking details")
    st.sidebar.markdown("- The AI will help you through the booking process") 
    st.sidebar.markdown("- The AI will extract flight info automatically") 
    st.sidebar.markdown("---")

    if st.session_state.flight_info:
        st.sidebar.markdown("### 🛫 Extracted Flight Info")
        flight_info = st.session_state.flight_info
        if flight_info.get("departure_city"):
            st.sidebar.markdown(f"**From:** {flight_info['departure_city']}")
        if flight_info.get("arrival_city"):
            st.sidebar.markdown(f"**To:** {flight_info['arrival_city']}")
        if flight_info.get("departure_date"):
            st.sidebar.markdown(f"**Departure:** {flight_info['departure_date']}")
        if flight_info.get("return_date"):
            st.sidebar.markdown(f"**Return:** {flight_info['return_date']}")
        if flight_info.get("passengers"):
            st.sidebar.markdown(f"**Passengers:** {flight_info['passengers']}")
        if flight_info.get("cabin_class"):
            st.sidebar.markdown(f"**Class:** {flight_info['cabin_class']}")
        if flight_info.get("budget"):
            st.sidebar.markdown(f"**Budget:** ${flight_info['budget']}")
        if flight_info.get("round_trip") is not None:
            trip_type = "Round-trip" if flight_info['round_trip'] else "One-way"
            st.sidebar.markdown(f"**Trip:** {trip_type}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Chat Info")
    st.sidebar.markdown(f"**Messages:** {len(st.session_state.messages)}")
    if st.session_state.session_id:
        st.sidebar.markdown(f"**Session:** {st.session_state.session_id}...")

with tab2:
    st.markdown("### User Management")
    try:
        response = requests.get("http://localhost:8000/users/table")
        if response.status_code == 200:
            data = response.json()
            users_df = pd.DataFrame(data["users_table"])
            if not users_df.empty:
                st.markdown(f"**Total Users:** {len(users_df)}")
                st.dataframe(users_df, use_container_width=True)
            else:
                st.info("No users registered yet")
        else:
            st.error("Failed to load users")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

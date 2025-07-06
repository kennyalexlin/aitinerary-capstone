import streamlit as st
import requests

st.title("Flight Booking Chat")

# session state - memory system
# creates a memory that persisits during the session 
# messages is a list that stores all the conversation
# initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "flight_info" not in st.session_state:
    st.session_state.flight_info = {}

# display chat history
# shows all previous messages when the page loads 
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# chat input
if prompt := st.chat_input("type your message here..."):
    # add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # send to FastAPI backend and get response
    try:
        # prepare request with session ID if available
        request_data = {"role": "user", "content": prompt}
        if st.session_state.session_id:
            request_data["session_id"] = st.session_state.session_id
        
        response = requests.post(
            "http://localhost:8000/chat",
            json=request_data
        )
        
        if response.status_code == 200:
            data = response.json()
            assistant_response = data["response"]
            
            # update session state
            st.session_state.session_id = data.get("session_id")
            st.session_state.flight_info = data.get("flight_info", {})
            
            # add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
            # display assistant response
            with st.chat_message("assistant"):
                st.markdown(assistant_response)
        else:
            st.error("Error connecting to backend")
    except Exception as e:
        st.error(f"Cannot connect to backend: {e}")

# add a clear chat button
if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.session_state.session_id = None
    st.session_state.flight_info = {}
    st.rerun()

# instructions
st.sidebar.markdown("**Instructions:**")
st.sidebar.markdown("- Type your message and press Enter")
st.sidebar.markdown("- Ask about flight booking details")
st.sidebar.markdown("- The AI will help you through the booking process") 
st.sidebar.markdown("- The AI will extract flight info automatically") 
st.sidebar.markdown("---")

# extracted flight info
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

# chat info
st.sidebar.markdown("---")
st.sidebar.markdown("### Chat Info")
st.sidebar.markdown(f"**Messages:** {len(st.session_state.messages)}")
if st.session_state.session_id:
    st.sidebar.markdown(f"**Session:** {st.session_state.session_id}...")

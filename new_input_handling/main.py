from fastapi import FastAPI
from datetime import datetime
import json
import os
import uuid
from google import genai
from llm_logic import get_llm_response
from models import ChatSession, ChatRequest, ChatResponse, FlightInfo, UserInfo, ChatMessage

# App Initialization 
app = FastAPI(
    title="Flight Booking Chat API",
    description="A chat-based API for collecting flight booking information",
    version="1.2.0"
)

# In-memory storage (replace with a database in production)
chat_sessions: dict[str, ChatSession] = {}

# Create subdirectory for bookings
BOOKINGS_DIR = "bookings"
os.makedirs(BOOKINGS_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"message": "Flight Booking Chat API is running", "status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    session_id = request.session_id
    user_content = request.content.strip()

    # Find or create the session
    if session_id and session_id in chat_sessions:
        session = chat_sessions[session_id]
    else:
        session_id = str(uuid.uuid4())
        session = ChatSession(session_id=session_id)
        chat_sessions[session_id] = session

    # If this is the very first interaction and the user hasn't typed anything,
    # (e.g., the web app just loaded), send the initial welcome message.
    if not session.messages and not user_content:
        initial_message = """Hello! I'm your flight booking assistant. To get started, could you tell me a bit about your trip? I'm looking for:
- The Airport or City you wish to depart from
- Your destination (Airport or City you will arrive in)
- Whether this is a one-way or round-trip journey
- The dates you are travelling
- The number of passengers

You can provide this all at once, or we can go step-by-step!"""
        session.messages.append(ChatMessage(role="assistant", content=initial_message))
        
        return ChatResponse(
            response=initial_message,
            session_id=session_id,
            is_complete=False,
            flight_info=session.flight_info,
            user_info=session.user_info
        )

    # For any message that has content, add it to the session and process it.
    session.messages.append(ChatMessage(role="user", content=request.content))

    # Pass the whole session object to the LLM logic for a response.
    llm_data = get_llm_response(session) 
    
    assistant_message = llm_data["assistant_message"]
    is_complete = llm_data["is_complete"]
    
    # Update session with the new state from LLM logic
    session = llm_data["updated_session"]
    session.messages.append(ChatMessage(role="assistant", content=assistant_message))

    if is_complete:
        final_data = {
            "session_id": session.session_id,
            "completed_at": datetime.now().isoformat(),
            "flight_info": session.flight_info.dict(exclude_unset=True),
            "user_info": session.user_info.dict(exclude_unset=True),
            "chat_history": [msg.dict() for msg in session.messages]
        }
        
        file_path = os.path.join(BOOKINGS_DIR, f"booking_{session.session_id}.json")
        with open(file_path, 'w') as f:
            json.dump(final_data, f, indent=4, default=str)
            
        del chat_sessions[session_id]

    return ChatResponse(
        response=assistant_message,
        session_id=session_id,
        is_complete=is_complete,
        flight_info=session.flight_info,
        user_info=session.user_info
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# file: main.py

from fastapi import FastAPI
from datetime import datetime
import json
import os
import uuid

# --- LOCAL IMPORTS ---
from llm_logic import get_llm_response
# Import ALL the Pydantic models needed by this file from their single source of truth.
from models import ChatSession, ChatRequest, ChatResponse, FlightInfo, UserInfo, ChatMessage

# --- App Initialization (CORRECTED - NO DUPLICATION) ---
app = FastAPI(
    title="Flight Booking Chat API",
    description="A chat-based API for collecting flight booking information",
    version="1.2.0"
)

# In-memory storage (replace with a database in production)
chat_sessions: dict[str, ChatSession] = {}

# Create subdirectory for bookings if it doesn't exist
BOOKINGS_DIR = "bookings"
os.makedirs(BOOKINGS_DIR, exist_ok=True)


@app.get("/")
def root():
    # Provide a proper JSON response for the root endpoint
    return {"message": "Flight Booking Chat API is running", "status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    session_id = request.session_id
    
    if session_id and session_id in chat_sessions:
        session = chat_sessions[session_id]
    else:
        # This is a new chat session
        session_id = str(uuid.uuid4())
        session = ChatSession(session_id=session_id)
        chat_sessions[session_id] = session
        initial_message = "Hello! I'm your flight booking assistant. Where would you like to fly from?"
        session.messages.append(ChatMessage(role="assistant", content=initial_message))
        
        return ChatResponse(
            response=initial_message,
            session_id=session_id,
            is_complete=False,
            flight_info=session.flight_info,
            user_info=session.user_info
        )

    # Add the user's message to the existing session
    session.messages.append(ChatMessage(role="user", content=request.content))

    # Pass the whole session object to the LLM logic
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
            # Custom JSON encoder for date objects
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
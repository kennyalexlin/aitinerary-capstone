from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

# initialize FastAPI app
app = FastAPI(
    title="Flight Booking Chat API",
    description="A chat-based API for collecting flight booking information",
    version="1.0.0"
)

# # add CORS middleware for frontend communication
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# data models
class FlightInfo(BaseModel):
    departure_city: str
    arrival_city: str
    departure_date: str
    return_date: Optional[str] = None
    passengers: int = 1
    cabin_class: Optional[str] = None
    budget: Optional[float] = None
    round_trip: bool = True
    flexible_dates: Optional[bool] = False

class UserInfo(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None 
    date_of_birth: Optional[str] = None
    home_address: Optional[str] = None
    passport_number: Optional[str] = None

class UserPreferences(BaseModel):
    preferred_airlines: Optional[List[str]] = None
    seat_preference: Optional[str] = None
    meal_preference: Optional[str] = None
    special_assistance: Optional[str] = None
    travel_insurance: Optional[bool] = None

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage] = []
    flight_info: Optional[FlightInfo] = None
    user_info: Optional[UserInfo] = None
    user_preferences: Optional[UserPreferences] = None

# in-memory storage (replace with database in production)
chat_sessions = {}

def generate_session_id() -> str:
    """generate a unique session ID"""
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(chat_sessions)}"

# API Endpoints
@app.get("/")
def root():
    """health check endpoint"""
    return {"message": "Flight Booking Chat API is running", "status": "healthy"}

@app.get("/health")
def health_check():
    """detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(chat_sessions)
    }

@app.post("/chat")
def chat(message: ChatMessage):
    """handle chat messages and return llm response"""
    # for now, just return a simple response
    response = "hello! what are you thinking for your flight?"
    
    return {
        "response": response,
        "session_id": None,  # add session management later
        "flight_info": None,
        "user_info": None,
        "user_preferences": None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
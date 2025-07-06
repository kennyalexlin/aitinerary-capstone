from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import requests
from .extractor import extract_flight_info_from_message, update_flight_info

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

# DeepSeek API configuration
DEEPSEEK_API_KEY = "ADDED_TO_GITIGNORE"  
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"

print("DeepSeek API configured!")

# data models
class FlightInfo(BaseModel):
    departure_city: str
    arrival_city: str
    departure_date: str
    return_date: Optional[str] = None
    adult_passengers: int = 1
    child_passengers: Optional[int] = None
    infant_passengers: Optional[int] = None
    cabin_class: Optional[str] = None
    budget: Optional[float] = None
    round_trip: bool = True
    flexible_dates: Optional[bool] = False
    routing: Optional[str] = None
    points_booking : Optional[bool] = False
    refundable : Optional[bool] = False
    redress_number: Optional[int] = None

class UserInfo(BaseModel):
    first_name: str
    last_name: str
    name_suffix: Optional[str] = None
    email: str
    phone_number: Optional[str] = None 
    date_of_birth: Optional[str] = None
    gender: str
    country: None
    home_address: Optional[str] = None
    passport_number: Optional[str] = None

class UserBillingInfo(BaseModel):
    name_on_card: str
    card_number: int
    expiration_date: int
    cvv: int
    billing_address: str
    city: str
    state_province: str
    zip_code: int
    country_region: str

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

class ChatRequest(BaseModel):
    role: str
    content: str
    session_id: Optional[str] = None

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
def chat(request: ChatRequest):
    """handle chat messages and return llm response with extracted flight info"""
    
    # initialize or get session
    session_id = request.session_id
    if not session_id:
        session_id = generate_session_id()
    
    print(f"Processing chat for session: {session_id}")
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "messages": [],
            "flight_info": {},
            "user_info": {},
            "user_preferences": {}
        }
        print(f"Created new session: {session_id}")
    else:
        print(f"Using existing session: {session_id}")
        print(f"Current flight info: {chat_sessions[session_id]['flight_info']}")
    
    # add user message to session
    chat_sessions[session_id]["messages"].append({
        "role": "user",
        "content": request.content,
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        # prepare the request payload for DeepSeek API
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # add context about being a flight booking assistant
        system_prompt = "You are a helpful flight booking assistant. Help users book flights by collecting their travel preferences in a conversational way. Be friendly and professional."
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.content}
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        # make API request to DeepSeek
        response = requests.post(DEEPSEEK_BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        # extract the response text
        result = response.json()
        ai_response = result['choices'][0]['message']['content']
        
        # Add AI response to session
        chat_sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # extract flight information from the current user message
        extracted_flight_info = extract_flight_info_from_message(request.content)
        print(f"Extracted flight info: {extracted_flight_info}")
        
        # update session flight info
        chat_sessions[session_id]["flight_info"] = update_flight_info(
            chat_sessions[session_id]["flight_info"], 
            extracted_flight_info
        )
        print(f"Updated flight info: {chat_sessions[session_id]['flight_info']}")
        
        # if response is empty, provide a fallback
        if not ai_response.strip():
            ai_response = "response is empty - troubleshooting"
            
    except Exception as e:
        print(f"Error generating response: {e}")
        ai_response = "I'm having trouble processing your request. Please try again."
    
    return {
        "response": ai_response,
        "session_id": session_id,
        "flight_info": chat_sessions[session_id]["flight_info"],
        "user_info": chat_sessions[session_id]["user_info"],
        "user_preferences": chat_sessions[session_id]["user_preferences"]
    }

@app.get("/session/{session_id}")
def get_session_info(session_id: str):
    """get session information including extracted flight data"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    return {
        "session_id": session_id,
        "messages": session["messages"],
        "flight_info": session["flight_info"],
        "user_info": session["user_info"],
        "user_preferences": session["user_preferences"]
    }

@app.get("/sessions")
def list_sessions():
    """list all active sessions"""
    return {
        "sessions": [
            {
                "session_id": session_id,
                "message_count": len(session["messages"]),
                "flight_info": session["flight_info"]
            }
            for session_id, session in chat_sessions.items()
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
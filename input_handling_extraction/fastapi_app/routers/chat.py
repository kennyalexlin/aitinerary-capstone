import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from ..models.chat import ChatRequest
from ..services.chat_service import ChatService
from ..services.user_service import UserService

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY environment variable not set. Please add it to your .env file.")

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
chat_service = ChatService(
    deepseek_api_key=DEEPSEEK_API_KEY,
    deepseek_base_url="https://api.deepseek.com/v1/chat/completions"
)
user_service = UserService()

@router.post("")
def chat(request: ChatRequest):
    """handle chat messages and return LLM response with extracted flight info"""
    
    # process the chat message
    result = chat_service.process_chat_message(
        content=request.content,
        session_id=request.session_id,
        username=request.username
    )
    
    # save session data if username is provided
    if request.username and user_service.authenticate_user(request.username):
        session_data = chat_service.get_session_data(result["session_id"])
        if session_data:
            # optionally save session or message here
            pass
    
    return result 

@router.delete("/clear_sessions")
def clear_sessions():
    """manually clear all in-memory chat sessions (admin/testing only)"""
    chat_service.clear_sessions()
    return {"message": "All chat sessions cleared from memory."} 
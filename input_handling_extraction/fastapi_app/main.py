from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Import routers
from .routers import users, chat

# Initialize FastAPI app
app = FastAPI(
    title="Flight Booking Chat API",
    description="A chat-based API for collecting flight booking information",
    version="1.3.0"
)

# Add CORS middleware for frontend communication
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Include routers
app.include_router(users.router)
app.include_router(chat.router)

# halth check endpoints
@app.get("/")
def root():
    """health check endpoint"""
    return {"message": "Flight Booking Chat API is running", "status": "healthy"}

@app.get("/health")
def health_check():
    """detailed health check"""
    from .services.chat_service import ChatService
    from .services.user_service import UserService
    
    # Initialize services to get session count
    chat_service = ChatService(
        deepseek_api_key="sk-62497041b697410a9df5f50e738e409d",
        deepseek_base_url="https://api.deepseek.com/v1/chat/completions"
    )
    user_service = UserService()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(chat_service.chat_sessions),
        "total_users": len(user_service.get_users_list())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime
from typing import Dict, Optional
from ..extractor import extract_flight_info_from_message, update_flight_info
from data_persistence.chat_saver import save_message_to_user_file

load_dotenv()

class ChatService:
    def __init__(self, deepseek_api_key: str, deepseek_base_url: str):
        self.deepseek_api_key = deepseek_api_key
        self.deepseek_base_url = deepseek_base_url
        self.chat_sessions = {}
    
    def generate_session_id(self) -> str:
        """generate a unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.chat_sessions)}"
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """get existing session or create new one"""
        if not session_id:
            session_id = self.generate_session_id()
        
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = {
                "messages": [],
                "flight_info": {},
                "user_info": {},
                "user_preferences": {}
            }
        
        return session_id
    
    def add_user_message(self, session_id: str, content: str):
        """add user message to session"""
        self.chat_sessions[session_id]["messages"].append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def generate_ai_response(self, content: str, current_flight_info: dict, session_messages: list) -> str:
        """generate AI response using LLM with full conversation context"""
        headers = {
            "Authorization": f"Bearer {self.deepseek_api_key}",
            "Content-Type": "application/json"
        }

        def get_field(info, key, default="Not specified"):
            value = info.get(key)
            return value if value not in [None, "", "null", "None"] else default

        system_prompt = f"""You are a helpful flight booking assistant. Based on the current conversation state, help the user complete their booking by asking for missing information.

Current flight information:
- Departure City: {get_field(current_flight_info, 'departure_city')}
- Arrival City: {get_field(current_flight_info, 'arrival_city')}
- Departure Date: {get_field(current_flight_info, 'departure_date')}
- Return Date: {get_field(current_flight_info, 'return_date')}
- Passengers: {get_field(current_flight_info, 'passengers')}
- Cabin Class: {get_field(current_flight_info, 'cabin_class')}
- Budget: {get_field(current_flight_info, 'budget')}
- Round Trip: {get_field(current_flight_info, 'round_trip')}
- Flexible Dates: {get_field(current_flight_info, 'flexible_dates')}

Your task:
1. Acknowledge any new information the user just provided
2. Identify what information is still missing for a complete booking
3. Ask for the most important missing information in a friendly, conversational way
4. Be specific about what you need (e.g., \"What date would you like to depart?\" instead of \"Tell me more\")

Keep your response concise and focused on collecting the missing information."""

        # Build the full conversation history for the LLM
        messages = [{"role": "system", "content": system_prompt}]
        for msg in session_messages:
            messages.append({"role": msg["role"], "content": msg["content"]})

        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.7
        }

        response = requests.post(self.deepseek_base_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def add_ai_response(self, session_id: str, content: str):
        """add AI response to session"""
        self.chat_sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def process_chat_message(self, content: str, session_id: Optional[str] = None, username: Optional[str] = None) -> Dict:
        """process a chat message and return response"""
        # get or create session
        session_id = self.get_or_create_session(session_id)
        
        # add user message
        self.add_user_message(session_id, content)
        # Save user message to file if username is provided
        if username:
            save_message_to_user_file(
                username=username,
                session_id=session_id,
                timestamp=datetime.now().isoformat(),
                role="user",
                content=content
            )
        try:
            # Stage 1: Extract flight information
            extracted_flight_info = extract_flight_info_from_message(content)
            # Update session flight info
            self.chat_sessions[session_id]["flight_info"] = update_flight_info(
                self.chat_sessions[session_id]["flight_info"], 
                extracted_flight_info
            )
            # DEBUG: Print current session flight_info before generating response
            print(f"[DEBUG] Current session flight_info for session {session_id}: {self.chat_sessions[session_id]['flight_info']}")
            # Stage 2: Generate AI response with full conversation context
            ai_response = self.generate_ai_response(
                content,
                self.chat_sessions[session_id]["flight_info"],
                self.chat_sessions[session_id]["messages"]
            )
            # add AI response
            self.add_ai_response(session_id, ai_response)
            # Save assistant message to file if username is provided
            if username:
                save_message_to_user_file(
                    username=username,
                    session_id=session_id,
                    timestamp=datetime.now().isoformat(),
                    role="assistant",
                    content=ai_response
                )
            # handle empty response
            if not ai_response.strip():
                ai_response = "I understand! Let me help you complete your booking. What other details can you provide?"
        except Exception as e:
            print(f"Error generating response: {e}")
            ai_response = "I'm having trouble processing your request. Please try again."
        return {
            "response": ai_response,
            "session_id": session_id,
            "username": username,
            "flight_info": self.chat_sessions[session_id]["flight_info"],
            "user_info": self.chat_sessions[session_id]["user_info"],
            "user_preferences": self.chat_sessions[session_id]["user_preferences"]
        }
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """get session information"""
        if session_id not in self.chat_sessions:
            return None
        
        session = self.chat_sessions[session_id]
        return {
            "session_id": session_id,
            "messages": session["messages"],
            "flight_info": session["flight_info"],
            "user_info": session["user_info"],
            "user_preferences": session["user_preferences"]
        }
    
    def list_sessions(self) -> Dict:
        """list all active sessions"""
        return {
            "sessions": [
                {
                    "session_id": session_id,
                    "message_count": len(session["messages"]),
                    "flight_info": session["flight_info"]
                }
                for session_id, session in self.chat_sessions.items()
            ]
        }
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """get session data for saving"""
        if session_id not in self.chat_sessions:
            return None
        return self.chat_sessions[session_id] 

    def clear_sessions(self):
        """clear all in-memory chat sessions."""
        self.chat_sessions = {} 
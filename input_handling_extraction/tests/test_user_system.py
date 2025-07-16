#!/usr/bin/env python3
"""
Simple test for the user system
"""

import requests
import json

def test_user_system():
    """Test the user registration and chat functionality"""
    
    base_url = "http://localhost:8000"
    
    # Test 1: Register a user
    print("=== Test 1: Register User ===")
    user_data = {
        "username": "testuser",
        "email": "test@example.com"
    }
    
    response = requests.post(f"{base_url}/register", json=user_data)
    if response.status_code == 200:
        print("✅ User registered successfully")
    else:
        print(f"❌ Registration failed: {response.status_code}")
    
    # Test 2: Login
    print("\n=== Test 2: Login ===")
    response = requests.post(f"{base_url}/login?username=testuser")
    if response.status_code == 200:
        print("✅ Login successful")
    else:
        print(f"❌ Login failed: {response.status_code}")
    
    # Test 3: Send chat message with username
    print("\n=== Test 3: Chat with Username ===")
    chat_data = {
        "role": "user",
        "content": "I want to fly from NYC to Tokyo",
        "username": "testuser"
    }
    
    response = requests.post(f"{base_url}/chat", json=chat_data)
    if response.status_code == 200:
        data = response.json()
        print("✅ Chat successful")
        print(f"Response: {data['response'][:100]}...")
        print(f"Flight info: {data['flight_info']}")
    else:
        print(f"❌ Chat failed: {response.status_code}")
    
    # Test 4: List users
    print("\n=== Test 4: List Users ===")
    response = requests.get(f"{base_url}/users")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Users: {data['users']}")
    else:
        print(f"❌ List users failed: {response.status_code}")

if __name__ == "__main__":
    test_user_system() 
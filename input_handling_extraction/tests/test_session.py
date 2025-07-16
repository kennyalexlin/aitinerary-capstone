#!/usr/bin/env python3
"""
Test script to verify session persistence in FastAPI
"""

import requests
import json

def test_session_persistence():
    """Test that session data persists across multiple requests"""
    
    base_url = "http://localhost:8000"
    
    # Test 1: First message
    print("=== Test 1: First message ===")
    message1 = {
        "role": "user",
        "content": "I want to fly from nyc to tokyo"
    }
    
    response1 = requests.post(f"{base_url}/chat", json=message1)
    if response1.status_code == 200:
        data1 = response1.json()
        session_id = data1["session_id"]
        flight_info1 = data1["flight_info"]
        print(f"Session ID: {session_id}")
        print(f"Flight Info: {flight_info1}")
    else:
        print(f"Error: {response1.status_code}")
        return
    
    # Test 2: Second message with same session
    print("\n=== Test 2: Second message (same session) ===")
    message2 = {
        "role": "user", 
        "content": "actually I want to go to paris",
        "session_id": session_id
    }
    
    response2 = requests.post(f"{base_url}/chat", json=message2)
    if response2.status_code == 200:
        data2 = response2.json()
        flight_info2 = data2["flight_info"]
        print(f"Flight Info: {flight_info2}")
        
        # Check if departure_city is preserved
        if flight_info2.get("departure_city") == "nyc" and flight_info2.get("arrival_city") == "paris":
            print("✅ SUCCESS: departure_city preserved, arrival_city updated")
        else:
            print("❌ FAILED: Expected departure_city='nyc', arrival_city='paris'")
            print(f"Got: departure_city='{flight_info2.get('departure_city')}', arrival_city='{flight_info2.get('arrival_city')}'")
    else:
        print(f"Error: {response2.status_code}")

if __name__ == "__main__":
    test_session_persistence() 
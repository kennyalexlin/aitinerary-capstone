#!/usr/bin/env python3
"""
Test script to simulate Alice's conversation and verify conversation history saving
"""

import requests
import json
import pandas as pd
import time

def test_alice_conversation():
    """Test Alice's complete conversation flow"""
    
    base_url = "http://localhost:8000"
    
    print("=== Testing Alice's Conversation ===\n")
    
    # Step 1: Register Alice
    print("1. Registering Alice...")
    alice_data = {"username": "alice", "email": "alice@example.com"}
    response = requests.post(f"{base_url}/register", json=alice_data)
    if response.status_code == 200:
        print("✅ Alice registered successfully")
    else:
        print(f"❌ Registration failed: {response.status_code}")
        return
    
    # Step 2: Alice's first message
    print("\n2. Alice: 'I want to fly from NYC to Tokyo'")
    chat_data = {
        "role": "user",
        "content": "I want to fly from NYC to Tokyo",
        "username": "alice"
    }
    
    response = requests.post(f"{base_url}/chat", json=chat_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Assistant: '{data['response'][:50]}...'")
        print(f"   Flight info: {data['flight_info']}")
        session_id = data['session_id']
    else:
        print(f"❌ Chat failed: {response.status_code}")
        return
    
    time.sleep(1)  # Small delay to simulate real conversation
    
    # Step 3: Alice's second message
    print("\n3. Alice: 'March 15th'")
    chat_data = {
        "role": "user",
        "content": "March 15th",
        "username": "alice",
        "session_id": session_id
    }
    
    response = requests.post(f"{base_url}/chat", json=chat_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Assistant: '{data['response'][:50]}...'")
        print(f"   Flight info: {data['flight_info']}")
    else:
        print(f"❌ Chat failed: {response.status_code}")
        return
    
    time.sleep(1)
    
    # Step 4: Alice's third message
    print("\n4. Alice: '2 passengers'")
    chat_data = {
        "role": "user",
        "content": "2 passengers",
        "username": "alice",
        "session_id": session_id
    }
    
    response = requests.post(f"{base_url}/chat", json=chat_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Assistant: '{data['response'][:50]}...'")
        print(f"   Flight info: {data['flight_info']}")
    else:
        print(f"❌ Chat failed: {response.status_code}")
        return
    
    # Step 5: Check the saved conversation
    print("\n5. Checking saved conversation...")
    try:
        df = pd.read_csv("alice_sessions.csv")
        print(f"✅ Conversation saved! Found {len(df)} messages")
        
        print("\n📋 Full Conversation History:")
        print("=" * 60)
        for _, row in df.iterrows():
            role_emoji = "👤" if row['role'] == 'user' else "🤖"
            print(f"{role_emoji} {str(row['role']).title()}: {row['content']}")
            print(f"   Message #{row['message_number']} | Total: {row['total_messages']}")
            print()
        
        print("📊 CSV Structure:")
        print(f"Columns: {list(df.columns)}")
        print(f"Total rows: {len(df)}")
        
    except FileNotFoundError:
        print("❌ alice_sessions.csv not found")
    except Exception as e:
        print(f"❌ Error reading conversation: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_alice_conversation() 
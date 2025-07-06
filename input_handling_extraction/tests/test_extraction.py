#!/usr/bin/env python3
"""
Test script to verify flight info extraction behavior
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from fastapi_app.extractor import extract_flight_info_from_message, update_flight_info

def test_extraction_behavior():
    """Test that extraction preserves existing data"""
    
    # Simulate first message: "I want to fly from nyc to tokyo"
    print("=== Test 1: Initial message ===")
    message1 = "I want to fly from nyc to tokyo"
    extracted1 = extract_flight_info_from_message(message1)
    print(f"Message: {message1}")
    print(f"Extracted: {extracted1}")
    
    # Simulate second message: "actually I want to go to paris"
    print("\n=== Test 2: Update message ===")
    message2 = "actually I want to go to paris"
    extracted2 = extract_flight_info_from_message(message2)
    print(f"Message: {message2}")
    print(f"Extracted: {extracted2}")
    
    # Update the flight info
    print("\n=== Test 3: Merged result ===")
    merged = update_flight_info(extracted1, extracted2)
    print(f"Merged result: {merged}")
    
    # Verify that departure_city is preserved
    if merged.get('departure_city') == 'nyc' and merged.get('arrival_city') == 'paris':
        print("✅ SUCCESS: departure_city preserved, arrival_city updated")
    else:
        print("❌ FAILED: Expected departure_city='nyc', arrival_city='paris'")
        print(f"Got: departure_city='{merged.get('departure_city')}', arrival_city='{merged.get('arrival_city')}'")

if __name__ == "__main__":
    test_extraction_behavior() 
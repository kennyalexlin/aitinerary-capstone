import os
from dotenv import load_dotenv
import requests
import json
import re
from typing import List, Dict, Optional
from .airport_resolver import resolve_airport_info

load_dotenv()

# DeepSeek API configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"

def postprocess_flight_info(flight_info: dict) -> dict:
    """resolve city names to IATA codes for departure and arrival cities."""
    for key in ["departure_city", "arrival_city"]:
        value = flight_info.get(key)
        if value:
            resolved = resolve_airport_info(value)
            if resolved["status"] == "resolved":
                flight_info[key + "_iata"] = resolved["iata"]
    return flight_info

def extract_flight_info_from_message(user_message: str) -> dict:
    """use LLM to extract flight information from the most recent user message"""
    try:
        # create extraction prompt
        extraction_prompt = f"""
        Analyze the following user message and extract any flight booking information mentioned. 
        Return ONLY a JSON object with the following structure. Use null for any fields not mentioned:
        {{
            "departure_city": "city name or null",
            "arrival_city": "city name or null", 
            "departure_date": "date in YYYY-MM-DD format or null",
            "return_date": "date in YYYY-MM-DD format or null",
            "passengers": number or null,
            "cabin_class": "economy/business/first or null",
            "budget": number in dollars or null,
            "round_trip": true/false or null,
            "flexible_dates": true/false or null
        }}

        Important: Only extract information that is explicitly mentioned in the user message.
        If a field is not mentioned, use null. Do not make assumptions.

        User message: "{user_message}"

        Extract the flight information as JSON:
        """
        
        # make API request to DeepSeek for extraction
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a flight booking data extractor. Extract flight information and return ONLY valid JSON."},
                {"role": "user", "content": extraction_prompt}
            ],
            "max_tokens": 700,
            "temperature": 0.1  # Low temperature for consistent extraction
        }
        
        response = requests.post(DEEPSEEK_BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        extracted_text = result['choices'][0]['message']['content']
        
        # try to parse the JSON response
        json_match = re.search(r'\{.*\}', extracted_text, re.DOTALL)
        if json_match:
            extracted_json = json.loads(json_match.group())
            # Post-process to resolve IATA codes
            extracted_json = postprocess_flight_info(extracted_json)
            return extracted_json
        else:
            print(f"Could not parse JSON from: {extracted_text}")
            return {}
            
    except Exception as e:
        print(f"Error extracting flight info: {e}")
        return {}

def update_flight_info(current_info: dict, new_info: dict) -> dict:
    """merge new flight information with existing information"""
    if not current_info:
        return new_info
    
    # Update only non-null and non-empty values
    for key, value in new_info.items():
        # Skip if value is None, empty string, "null" string, or other falsy values
        if value is not None and value != "" and value != "null" and value != "None":
            current_info[key] = value
    
    return current_info 
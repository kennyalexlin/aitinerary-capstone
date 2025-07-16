import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any, List
from datetime import datetime
from dateutil.parser import parse
import traceback

from models import ChatSession, FlightInfo, ChatMessage
from airport_resolver import resolve_airport_info

# Load API key from .env file
load_dotenv()

# Configure the generative AI client
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    print(f"Error configuring Google AI client: {e}. Make sure GOOGLE_API_KEY is set.")

def handle_ambiguous_date(date_str: str) -> str:
    try:
        parsed_date = parse(date_str, fuzzy=True).date()
        today = datetime.now().date()
        if parsed_date < today:
            parsed_date = parsed_date.replace(year=parsed_date.year + 1)
        return parsed_date.isoformat()
    except (ValueError, TypeError):
        return date_str

def direct_resolve_airport(city: str) -> dict:
    if not city or not isinstance(city, str): return None
    return resolve_airport_info(city.strip())

def get_system_prompt(context_message: str, flight_info: FlightInfo) -> str:
    return (
        "You are a helpful flight booking assistant. Your ONLY task is to clarify information based on the context below. "
        "Ask a clear, concise question. Do not ask for any other information.\n\n"
        f"CONTEXT FOR YOUR QUESTION:\n{context_message}"
    )

def update_session_from_conversation(session: ChatSession) -> ChatSession:
    """
    Uses an LLM to extract all possible fields from the conversation history with a more robust prompt.
    """
    conversation_history = "\n".join([f"{msg.role}: {msg.content}" for msg in session.messages[-6:]])
    
    extraction_prompt = (
        "You are a highly efficient JSON data extraction assistant. Your task is to analyze the 'Recent Conversation' "
        "and update the 'Current Data' JSON object with any new or corrected information. "
        "Adhere strictly to the `FlightInfo` JSON schema. Fill only relevant fields.\n"
        "1. Extract cities into `departure_city` or `arrival_city`. The system handles IATA resolution.\n"
        "2. Dates must be in YYYY-MM-DD format.\n"
        "3. Passenger counts (`adult_passengers`, `child_passengers`, `infant_passengers`) must be integers.\n"
        "4. `cabin_class` must be one of: 'Economy', 'Premium Economy', 'Business', 'First'. Case-insensitive matching is fine, but output exactly one of these values.\n"
        "5. `budget` must be a floating-point number (e.g., 500.0, 1200.50). Handle 'k' as thousand (e.g., '5k' -> 5000.0). Ignore currency symbols, just extract the number.\n"
        "6. `routing` must be one of: 'direct', 'one_stop', 'any'. 'Non-stop' maps to 'direct'.\n"
        "7. `round_trip` should be boolean (true/false). 'one-way' means false, 'return' or 'round trip' means true.\n"
        "8. `flexible_dates`, `points_booking`, `refundable` should be booleans (true/false) based on user's intent.\n"
        "9. If the user explicitly corrects a field, update it. Otherwise, merge new info with existing. Do not erase data that wasn't specifically mentioned.\n"
        "Return ONLY the raw, updated JSON object. Do not add any commentary or surrounding text.\n\n"
        f"Current Data:\n{session.flight_info.model_dump_json(exclude_unset=True, indent=2)}\n\n"
        f"Recent Conversation:\n{conversation_history}\n\n"
        "Updated JSON:"
    )

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            extraction_prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json", temperature=0.0)
        )
        print(f"DEBUG: LLM Extraction Raw Response: {response.text}") # Debug print
        updates = json.loads(response.text)
        print(f"DEBUG: LLM Extraction Parsed Updates: {updates}") # Debug print

        # Process dates
        for date_field in ['departure_date', 'return_date']:
            if date_field in updates and updates[date_field]:
                updates[date_field] = handle_ambiguous_date(updates[date_field])
        
        # Ensure numerical fields are correctly typed
        numerical_fields = ['adult_passengers', 'child_passengers', 'infant_passengers']
        for field in numerical_fields:
            if field in updates and updates[field] is not None:
                try: updates[field] = int(updates[field])
                except (ValueError, TypeError): updates[field] = None 
        
        if 'budget' in updates and updates['budget'] is not None:
            try: 
                if isinstance(updates['budget'], str):
                    # Remove currency symbols and handle 'k'
                    budget_str = updates['budget'].replace('$', '').replace('€', '').replace('£', '').lower().strip()
                    if 'k' in budget_str:
                        updates['budget'] = float(budget_str.replace('k', '')) * 1000
                    else:
                        updates['budget'] = float(budget_str)
                else:
                    updates['budget'] = float(updates['budget'])
            except (ValueError, TypeError): updates['budget'] = None

        # Handle boolean fields
        boolean_fields = ['round_trip', 'flexible_dates', 'points_booking', 'refundable']
        for field in boolean_fields:
            if field in updates and updates[field] is not None:
                if isinstance(updates[field], str):
                    updates[field] = updates[field].lower() == 'true'
        
        # Handle cabin_class and routing for Literal types
        if 'cabin_class' in updates and updates['cabin_class'] is not None:
            val = str(updates['cabin_class']).lower()
            if 'economy' in val: updates['cabin_class'] = 'Economy'
            elif 'premium economy' in val: updates['cabin_class'] = 'Premium Economy'
            elif 'business' in val: updates['cabin_class'] = 'Business'
            elif 'first' in val: updates['cabin_class'] = 'First'
            else: updates['cabin_class'] = None 

        if 'routing' in updates and updates['routing'] is not None:
            val = str(updates['routing']).lower()
            if 'direct' in val or 'non-stop' in val: updates['routing'] = 'direct'
            elif 'one stop' in val or '1 stop' in val: updates['routing'] = 'one_stop'
            elif 'any' in val: updates['routing'] = 'any'
            else: updates['routing'] = None 

        updated_flight_info_dict = session.flight_info.model_dump(exclude_unset=True)
        updated_flight_info_dict.update(updates)
        session.flight_info = FlightInfo(**updated_flight_info_dict)

    except Exception as e:
        print(f"Error during LLM data extraction: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        
    return session

def get_next_question(flight_info: FlightInfo, optional_fields_declined: bool) -> str:
    """
    Determines the next logical question to ask, prioritizing essential, then optional, then final confirmation.
    Includes a flag to skip optional fields if the user has declined them.
    """
    # Essential fields check
    if not flight_info.departure_iata: return "Where would you like to fly from?"
    if not flight_info.arrival_iata: return "Where would you like to fly to?"
    if not flight_info.departure_date: return "What date would you like to depart?"
    if flight_info.adult_passengers is None: return "How many adults will be traveling?"
    if flight_info.round_trip and not flight_info.return_date: return "And when would you like to return?"
    
    # If essential fields are complete AND user has NOT declined optional fields
    if not optional_fields_declined:
        uncollected_optional_fields_prompts = []
        optional_field_map = {
            "cabin_class": "cabin class (Economy, Business, First, etc.)",
            "budget": "your budget",
            "flexible_dates": "flexible dates",
            "routing": "preferred routing (direct, one stop, any)",
            "points_booking": "booking with points",
            "refundable": "refundable tickets",
        }
        
        for field_name, prompt_text in optional_field_map.items():
            if getattr(flight_info, field_name) is None:
                uncollected_optional_fields_prompts.append(prompt_text)

        if uncollected_optional_fields_prompts:
            if len(uncollected_optional_fields_prompts) == 1:
                return f"I have the essential details. Would you like to specify your {uncollected_optional_fields_prompts[0]}?"
            elif len(uncollected_optional_fields_prompts) == 2:
                return f"I have the essential details. Would you like to specify your {uncollected_optional_fields_prompts[0]} or {uncollected_optional_fields_prompts[1]}?"
            else:
                last_field = uncollected_optional_fields_prompts.pop()
                return f"I have the essential details. Would you like to provide any other details, like your {', '.join(uncollected_optional_fields_prompts)} or {last_field}?"
    
    # If all essential and all known optional fields are collected, or if optional fields were declined
    return "I have all the essential details. Are you ready to search for flights?"


def get_llm_response(session: ChatSession) -> Dict[str, Any]:
    try:
        flight_info_at_start = session.flight_info.copy(deep=True)
        last_user_message_content = session.messages[-1].content.lower().strip()
        
        assistant_message = ""
        is_complete = False

        updated_session = session 

        # State Management based on previous turn and current user input
        if session.awaiting_data_confirmation:
            if last_user_message_content in ["yes", "y", "ok", "correct", "that's right", "confirm"]:
                session.awaiting_data_confirmation = False
                # If data was just confirmed, do not try to extract new data from "yes"
            else:
                session.awaiting_data_confirmation = False 
                updated_session = update_session_from_conversation(session) 
        elif session.awaiting_final_search_confirmation:
            if last_user_message_content in ["yes", "y", "ok", "sure", "proceed", "go", "book", "search"]:
                is_complete = True
                assistant_message = "Great! I'm now finalizing your flight search details. The booking data has been saved. [END_CONVO]"
                session.awaiting_final_search_confirmation = False 
                return {
                    "assistant_message": assistant_message,
                    "is_complete": is_complete,
                    "updated_session": session 
                }
            else:
                session.awaiting_final_search_confirmation = False 
                updated_session = update_session_from_conversation(session)
        else:
            updated_session = update_session_from_conversation(session)
        
        flight_info = updated_session.flight_info
        
        context_for_llm = ""
        
        # Airport Resolution Phase
        if flight_info.departure_city and not flight_info.departure_iata:
            dep_result = direct_resolve_airport(flight_info.departure_city)
            if dep_result['status'] == 'resolved':
                flight_info.departure_iata = dep_result['iata']
                flight_info.departure_city = dep_result['city']
            elif dep_result['status'] == 'ambiguous':
                options = ", ".join([f"{opt['name']} ({opt['iata']})" for opt in dep_result['data']])
                context_for_llm += f"The departure location '{flight_info.departure_city}' has multiple major airports. Please ask the user to choose one: {options}.\n"
            else: # not_found
                context_for_llm += f"I couldn't find any major airports for '{flight_info.departure_city}'. Please ask for a different city.\n"
        
        if flight_info.arrival_city and not flight_info.arrival_iata:
            arr_result = direct_resolve_airport(flight_info.arrival_city)
            if arr_result['status'] == 'resolved':
                flight_info.arrival_iata = arr_result['iata']
                flight_info.arrival_city = arr_result['city']
            elif arr_result['status'] == 'ambiguous':
                options = ", ".join([f"{opt['name']} ({opt['iata']})" for opt in arr_result['data']])
                context_for_llm += f"The arrival location '{flight_info.arrival_city}' has multiple major airports. Please ask the user to choose one: {options}.\n"
            else: # not_found
                context_for_llm += f"I couldn't find any major airports for '{flight_info.arrival_city}'. Please ask for a different city.\n"
        
        #  Response Generation Phase (Clarify > Confirm Data > Ask Next Question)
        
        if context_for_llm:
            # Priority 1: Clarify ambiguity/not_found using LLM
            system_prompt = get_system_prompt(context_for_llm, flight_info)
            model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_prompt)
            chat_history_for_google = [{"role": "model" if msg.role == "assistant" else msg.role, "parts": [{"text": msg.content}]} for msg in updated_session.messages[:-1]]
            chat = model.start_chat(history=chat_history_for_google)
            response = chat.send_message(updated_session.messages[-1].content)
            assistant_message = response.text
            session.awaiting_data_confirmation = False
            session.awaiting_final_search_confirmation = False
            session.optional_fields_offered_and_declined = False # Reset if clarification leads to new data flow
        else:
            # Check if user explicitly declined optional fields
            decline_phrases = ["no", "skip", "don't care", "not interested", "just book", "proceed", "go", "search"]
            # Detect if current response explicitly declines, AND we are in the optional question phase
            current_question = get_next_question(flight_info, False) # Temporarily check what question *would* be asked if not for decline flag
            if any(phrase in last_user_message_content for phrase in decline_phrases) and \
               "Would you like to provide any other details" in current_question:
                session.optional_fields_offered_and_declined = True
                print("DEBUG: User declined optional fields. Setting optional_fields_offered_and_declined to True.") # Debug print
            elif updated_session.flight_info != flight_info_at_start:
                # If there were any actual updates extracted by the LLM, reset the decline flag.
                # This means the user provided new data, even if it wasn't a direct answer to an optional field question.
                session.optional_fields_offered_and_declined = False 

            # Priority 2: Confirm newly resolved/extracted info (if not already confirmed and no ambiguities)
            confirmation_parts = []
            if flight_info.departure_iata and flight_info.departure_iata != flight_info_at_start.departure_iata:
                confirmation_parts.append(f"departing from {flight_info.departure_city} ({flight_info.departure_iata})")
            if flight_info.arrival_iata and flight_info.arrival_iata != flight_info_at_start.arrival_iata:
                confirmation_parts.append(f"arriving in {flight_info.arrival_city} ({flight_info.arrival_iata})")
            
            if not session.awaiting_data_confirmation: 
                if flight_info.departure_date and str(flight_info.departure_date) != str(flight_info_at_start.departure_date):
                    confirmation_parts.append(f"on {flight_info.departure_date}")
                if flight_info.adult_passengers is not None and flight_info.adult_passengers != flight_info_at_start.adult_passengers:
                    confirmation_parts.append(f"for {flight_info.adult_passengers} adult{'s' if flight_info.adult_passengers > 1 else ''}")
                if flight_info.round_trip is not None and flight_info.round_trip != flight_info_at_start.round_trip:
                    confirmation_parts.append("for a one-way trip" if not flight_info.round_trip else "for a round trip")
                if flight_info.round_trip and flight_info.return_date and str(flight_info.return_date) != str(flight_info_at_start.return_date):
                    confirmation_parts.append(f"returning on {flight_info.return_date}")
                
                # Check newly added or changed optional fields for confirmation
                if flight_info.cabin_class and flight_info.cabin_class != flight_info_at_start.cabin_class:
                    confirmation_parts.append(f"in {flight_info.cabin_class} class")
                if flight_info.budget is not None and flight_info.budget != flight_info_at_start.budget:
                    confirmation_parts.append(f"with a budget of ${flight_info.budget:,.2f}")
                if flight_info.flexible_dates is not None and flight_info.flexible_dates != flight_info_at_start.flexible_dates:
                    confirmation_parts.append("with flexible dates" if flight_info.flexible_dates else "without flexible dates")
                if flight_info.routing and flight_info.routing != flight_info_at_start.routing:
                    confirmation_parts.append(f"with {flight_info.routing} routing")
                if flight_info.points_booking is not None and flight_info.points_booking != flight_info_at_start.points_booking:
                    confirmation_parts.append("booking with points" if flight_info.points_booking else "not booking with points")
                if flight_info.refundable is not None and flight_info.refundable != flight_info_at_start.refundable:
                    confirmation_parts.append("for refundable tickets" if flight_info.refundable else "for non-refundable tickets")


            if confirmation_parts and not session.awaiting_data_confirmation: 
                confirmation_string = " and ".join(confirmation_parts)
                assistant_message = f"OK, I've got you down for a trip {confirmation_string}. Is that correct?"
                session.awaiting_data_confirmation = True 
                session.awaiting_final_search_confirmation = False
            else:
                session.awaiting_data_confirmation = False
                session.awaiting_final_search_confirmation = False

                # Pass the new flag to get_next_question
                assistant_message = get_next_question(flight_info, session.optional_fields_offered_and_declined)
                
                if "I have all the essential details. Are you ready to search for flights?" in assistant_message:
                    session.awaiting_final_search_confirmation = True 
            
        return {
            "assistant_message": assistant_message.strip(),
            "is_complete": is_complete,
            "updated_session": updated_session
        }
    except Exception as e:
        print(f"Error in get_llm_response: {e}\nFull traceback: {traceback.format_exc()}")
        return {"assistant_message": "I'm sorry, an internal error occurred. Please try again.", "is_complete": False, "updated_session": session}
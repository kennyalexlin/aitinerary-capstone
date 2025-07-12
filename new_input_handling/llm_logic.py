import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any
from datetime import datetime, timedelta, date
from dateutil.parser import parse

# Import from the new, safe location
from models import ChatSession, FlightInfo

# Import from config as before
from config import APP_MODE, TIER_1_ESSENTIAL_FIELDS, COLLECTION_STAGES
# Load API key from .env file
load_dotenv()

# Configure the OpenAI client to use OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Pre-processing function for dates
def preprocess_user_input(text: str) -> str:
    """Replaces relative date terms in user input with absolute dates."""
    today = datetime.now().date()

    # Simple, direct replacements for "today" and "tomorrow"
    # Using word boundaries (\b) to avoid replacing the substring in other words.
    text = re.sub(r'\btoday\b', today.strftime('%Y-%m-%d'), text, flags=re.IGNORECASE)
    text = re.sub(r'\btomorrow\b', (today + timedelta(days=1)).strftime('%Y-%m-%d'), text, flags=re.IGNORECASE)
    
    # More complex replacement for phrases like "in X days" using a replacer function
    def date_replacer(match):
        days = int(match.group(1))
        future_date = today + timedelta(days=days)
        return future_date.strftime('%Y-%m-%d')

    # This single, robust pattern handles phrases like:
    # "in 6 days", "6 days later", "6 days from now"
    pattern = re.compile(r'\b(?:in\s+)?(\d+)\s+days(?:\s+(?:later|from\s+now))?\b', re.IGNORECASE)
    text = pattern.sub(date_replacer, text)
    
    return text


def handle_ambiguous_date(date_str: str) -> str:
    """Parses a date string and ensures it's a future date."""
    try:
        # The parser is very flexible
        parsed_date = parse(date_str).date()
        today = datetime.now().date()

        # If the parsed date is in the past, assume it's for the next year
        if parsed_date < today:
            parsed_date = parsed_date.replace(year=parsed_date.year + 1)

        return parsed_date.isoformat()
    except (ValueError, TypeError):
        return date_str


def get_system_prompt(session: ChatSession) -> str:
    """Generates the system prompt based on the current collection stage and config."""
    
    # Determine the current stage based on config
    current_stage_models = COLLECTION_STAGES[APP_MODE]
    current_model_name = current_stage_models[0]
    
    flight_info = session.flight_info

    # --- 1. Determine required fields for THIS turn ---
    required_fields_for_stage = set(TIER_1_ESSENTIAL_FIELDS)
    if flight_info.round_trip is True:
        required_fields_for_stage.add("return_date")

    missing_essential_fields = [
        field for field in required_fields_for_stage if getattr(flight_info, field) is None
    ]
    is_ready_to_book = not missing_essential_fields

    # --- 2. Analyze last messages for intent ---
    last_user_message = ""
    if session.messages and session.messages[-1].role == 'user':
        last_user_message = session.messages[-1].content.lower()

    last_bot_message = ""
    if len(session.messages) > 1 and session.messages[-2].role == 'assistant':
        last_bot_message = session.messages[-2].content.lower()
        
    user_is_confirming = bool(re.search(r'\b(yes|correct|confirm|yep|that is right)\b', last_user_message))
    user_wants_to_finalize = bool(re.search(r'\b(book|search|find|go|done|that\'s it|that\'s all|looks good|proceed)\b', last_user_message))
    bot_just_asked_for_confirmation = "correct?" in last_bot_message or "confirm?" in last_bot_message

    # --- 3. Build the Prompt ---
    prompt = (
        "You are a helpful and conversational flight booking assistant. Your goal is to fill a JSON object with flight details by having a natural conversation. "
        "Your responses MUST be clean, concise, single paragraphs. Do NOT use markdown, code blocks, or repeat yourself.\n\n"
        f"You are currently collecting information for: **{current_model_name}**.\n"
        "Here is the data you have collected so far:\n"
        f"{flight_info.model_dump_json(exclude_unset=True, indent=2)}\n\n"
    )

    # --- 4. State Machine Logic ---

    # Case 1: User gives final confirmation. End the conversation.
    if bot_just_asked_for_confirmation and user_is_confirming:
        prompt += "**Your Current Task:** The user has confirmed all details. Thank them, state that the booking is complete, and end the conversation using the `[END_CONVO]` tag."

    # Case 2: User wants to book/finalize, but essential info is missing.
    elif user_wants_to_finalize and not is_ready_to_book:
        prompt += (
            f"**Your Current Task:** The user wants to proceed with booking, but you are missing essential information: "
            f"**{', '.join(missing_essential_fields)}**. Politely explain this, and then ask a clear question to get the next required piece of information (which is **{missing_essential_fields[0]}**)."
        )
    
    # Case 3: User wants to book/finalize, and all essential info is present. Time to summarize.
    elif user_wants_to_finalize and is_ready_to_book:
        prompt += (
            "**Your Current Task:** All essential information is collected and the user wants to proceed. "
            "Summarize ALL the details you have collected so far and ask the user for final confirmation (e.g., 'Does this look correct?'). "
            "**DO NOT** use the `[END_CONVO]` tag yet."
        )

    # Case 4: Default conversation flow.
    else:
        # Sub-case 4a: Still need essential info.
        if not is_ready_to_book:
            prompt += (
                f"**Your Current Task:** Continue the conversation to get the next piece of essential information. "
                f"Your highest priority is to fill one of these fields: **{', '.join(missing_essential_fields)}**. Ask one clear question for the next field, which is **{missing_essential_fields[0]}**."
            )
        # Sub-case 4b: Essentials are done. Ask for optional info.
        else:
            all_possible_fields = set(FlightInfo.model_fields.keys())
            filled_fields = {k for k, v in flight_info.model_dump().items() if v is not None}
            missing_optional_fields = list(all_possible_fields - filled_fields)
            
            # Crucial fix: Don't ask for a return date on a one-way trip
            if flight_info.round_trip is False and 'return_date' in missing_optional_fields:
                missing_optional_fields.remove('return_date')
            
            if missing_optional_fields:
                prompt += (
                    f"**Your Current Task:** You have the essential flight details. Continue the conversation by asking for optional details to refine the search. "
                    f"For example, you could ask about: **{', '.join(missing_optional_fields)}**. Pick one and ask a natural question (e.g., 'Are there any children or infants traveling?', 'What cabin class would you prefer?')."
                    " Do not ask for confirmation yet."
                )
            else: # All fields are filled, which is unlikely but possible.
                 prompt += (
                    "**Your Current Task:** You have all possible information. Summarize ALL the details you have collected so far and ask the user for final confirmation (e.g., 'Does this look correct?'). "
                    "**DO NOT** use the `[END_CONVO]` tag yet."
                )
    return prompt

def update_session_from_conversation(session: ChatSession) -> ChatSession:
    """Uses LLM to extract data and updates the session object."""
    messages = [msg.dict() for msg in session.messages]
    
    if messages and messages[-1]['role'] == 'user':
        messages[-1]['content'] = preprocess_user_input(messages[-1]['content'])

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages[-6:]])

    # --- REVISED, MORE ROBUST EXTRACTION PROMPT ---
    extraction_prompt = (
        "You are a meticulous data extraction system. Your task is to comprehensively fill a JSON object based on a conversation history. "
        "Carefully review the entire 'Recent Conversation' provided. The user may provide multiple pieces of information in a single message or across several messages. "
        "Your goal is to extract ALL available details (departure/arrival cities, dates, passenger counts, cabin class, budget, booleans for round_trip/refundable etc.) and use them to update the 'Current Data' JSON object. "
        "Do not overwrite existing data unless the user explicitly corrects it. "
        "Ensure dates are in YYYY-MM-DD format. "
        "Return ONLY the updated JSON object for the `FlightInfo` model. Do not add any commentary or explanations. Fill every field for which you can find information in the conversation.\n\n"
        f"Current Data:\n{session.flight_info.model_dump_json(exclude_unset=True, indent=2)}\n\n"
        f"Recent Conversation:\n{conversation_history}\n\n"
        "Return ONLY the updated JSON object for the `FlightInfo` model."
    )
    
    try:
        response = client.chat.completions.create(
            model="google/gemini-flash-1.5-8b",
            messages=[{"role": "system", "content": extraction_prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        updates = json.loads(response.choices[0].message.content)
        
        # Handle date fields specifically
        for date_field in ['departure_date', 'return_date']:
            if date_field in updates and updates[date_field]:
                # Apply the ambiguous date handler
                updates[date_field] = handle_ambiguous_date(updates[date_field])
        
        # Create a new FlightInfo object with the updates, letting Pydantic validate
        # This is safer than updating the dictionary directly
        updated_flight_info_dict = session.flight_info.dict()
        updated_flight_info_dict.update(updates)
        
        session.flight_info = FlightInfo(**updated_flight_info_dict)

    except Exception as e:
        print(f"Error extracting or processing JSON: {e}")
        # Log the actual error for debugging
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
    return session


def get_llm_response(session: ChatSession) -> Dict[str, Any]:
    """Manages the chat turn, updates state, and gets the bot's response."""
    
    try:
        # 1. Update the session state based on the last user message
        updated_session = update_session_from_conversation(session)

        # 2. Generate the system prompt for the CHATBOT using the NEWLY updated session
        system_prompt = get_system_prompt(updated_session)
        
        llm_messages = [{"role": "system", "content": system_prompt}] + [msg.dict() for msg in updated_session.messages]

        response = client.chat.completions.create(
            model="google/gemini-flash-1.5-8b",
            messages=llm_messages,
            temperature=0.5,
        )
        
        assistant_response = response.choices[0].message.content
        
        is_complete = "[END_CONVO]" in assistant_response
        if is_complete:
            assistant_response = assistant_response.replace("[END_CONVO]", "").strip()
        
        return {
            "assistant_message": assistant_response,
            "is_complete": is_complete,
            "updated_session": updated_session
        }
    except Exception as e:
        print(f"Error in get_llm_response: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise
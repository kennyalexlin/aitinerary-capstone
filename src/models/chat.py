from pydantic import BaseModel
from typing import List, Optional

class FlightInfo(BaseModel):
    departure_city: str
    arrival_city: str
    departure_date: str
    return_date: Optional[str] = None
    adult_passengers: int = 1
    child_passengers: Optional[int] = None
    infant_passengers: Optional[int] = None
    cabin_class: Optional[str] = None
    budget: Optional[float] = None
    round_trip: bool = True
    flexible_dates: Optional[bool] = False
    routing: Optional[str] = None
    points_booking: Optional[bool] = False
    refundable: Optional[bool] = False
    redress_number: Optional[int] = None

class UserInfo(BaseModel):
    first_name: str
    last_name: str
    name_suffix: Optional[str] = None
    email: str
    phone_number: Optional[str] = None 
    date_of_birth: Optional[str] = None
    gender: str
    country: Optional[str] = None
    home_address: Optional[str] = None
    passport_number: Optional[str] = None

class UserBillingInfo(BaseModel):
    name_on_card: str
    card_number: int
    expiration_date: int
    cvv: int
    billing_address: str
    city: str
    state_province: str
    zip_code: int
    country_region: str

class UserPreferences(BaseModel):
    preferred_airlines: Optional[List[str]] = None
    seat_preference: Optional[str] = None
    meal_preference: Optional[str] = None
    special_assistance: Optional[str] = None
    travel_insurance: Optional[bool] = None

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage] = []
    flight_info: Optional[FlightInfo] = None
    user_info: Optional[UserInfo] = None
    user_preferences: Optional[UserPreferences] = None

class ChatRequest(BaseModel):
    role: str
    content: str
    session_id: Optional[str] = None
    username: Optional[str] = None 
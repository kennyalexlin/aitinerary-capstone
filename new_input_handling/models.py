from pydantic import BaseModel, EmailStr, constr, ConfigDict, field_validator
from typing import List, Optional, Literal, Union
from datetime import date, datetime

class FlightInfo(BaseModel):
    model_config = ConfigDict(
        json_encoders={date: lambda v: v.isoformat()},
        extra="ignore"
    )

    departure_city: Optional[str] = None
    departure_iata: Optional[str] = None
    arrival_city: Optional[str] = None
    arrival_iata: Optional[str] = None
    departure_date: Optional[Union[date, str]] = None
    return_date: Optional[Union[date, str]] = None
    adult_passengers: Optional[int] = None
    round_trip: Optional[bool] = None
    child_passengers: int = 0
    infant_passengers: int = 0
    cabin_class: Optional[Literal["Economy", "Premium Economy", "Business", "First"]] = None
    budget: Optional[float] = None
    flexible_dates: Optional[bool] = False
    routing: Optional[Literal["direct", "one_stop", "any"]] = None
    points_booking: Optional[bool] = False
    refundable: Optional[bool] = False

    @field_validator('departure_date', 'return_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if v is None: return None
        if isinstance(v, date): return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v).date()
            except:
                try:
                    return datetime.strptime(v, '%Y-%m-%d').date()
                except:
                    return v # Return as-is if parsing fails
        return v

class UserInfo(BaseModel):
    model_config = ConfigDict(
        json_encoders={date: lambda v: v.isoformat()},
        extra="ignore"
    )
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[Literal["Male", "Female", "Unspecified"]] = None
    date_of_birth: Optional[Union[date, str]] = None
    name_suffix: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    home_address: Optional[str] = None
    passport_number: Optional[str] = None

    @field_validator('date_of_birth', mode='before')
    @classmethod
    def parse_dob(cls, v):
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v).date()
            except:
                try:
                    return datetime.strptime(v, '%Y-%m-%d').date()
                except:
                    return v
        return v

class UserBillingInfo(BaseModel):
    name_on_card: Optional[str] = None
    card_number: Optional[constr(min_length=15, max_length=19)] = None
    expiration_date: Optional[str] = None
    cvv: Optional[constr(min_length=3, max_length=4)] = None
    billing_address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    zip_code: Optional[str] = None
    country_region: Optional[str] = None

class UserPreferences(BaseModel):
    preferred_airlines: Optional[List[str]] = None
    seat_preference: Optional[str] = None
    meal_preference: Optional[str] = None
    special_assistance: Optional[str] = None
    travel_insurance: Optional[bool] = None
    
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage] = []
    flight_info: FlightInfo = FlightInfo()
    user_info: UserInfo = UserInfo()
    awaiting_data_confirmation: bool = False
    awaiting_final_search_confirmation: bool = False
    optional_fields_offered_and_declined: bool = False 

class ChatRequest(BaseModel):
    content: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    is_complete: bool
    flight_info: FlightInfo
    user_info: UserInfo
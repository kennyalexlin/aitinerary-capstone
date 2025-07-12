
# Application Mode - we can expand this later
APP_MODE = "flight_search_only"

# Tier 1: Essential for SEARCHING for a flight
# These fields are the absolute minimum needed to query an airline API.
TIER_1_ESSENTIAL_FIELDS = {
    "departure_city",
    "arrival_city",
    "departure_date",
    "adult_passengers",
}
# This dictionary maps the app mode to the Pydantic models to be collected in order.
COLLECTION_STAGES = {
    "flight_search_only": ["FlightInfo"],
    "full_booking": ["FlightInfo", "UserInfo", "UserPreferences"], # For future implementation
}
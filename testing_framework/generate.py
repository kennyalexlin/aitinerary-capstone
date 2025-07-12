import json
import random
from datetime import datetime, timedelta

# Configuration for Data Generation

NUM_RECORDS = 100
OUTPUT_FILE = "flight_test_data.json"
START_DATE = datetime(2025, 7, 7).date() # Start generating dates from here

# Lists for random selection to create varied and realistic data
CITIES = [
    "New York", "Los Angeles", "London", "Paris", "Tokyo", "Sydney", 
    "Dubai", "Singapore", "Hong Kong", "San Francisco", "Chicago", "Toronto",
    "Berlin", "Madrid", "Rome", "Amsterdam", "Seoul", "Bangkok"
]
CABIN_CLASSES = ["Economy", "Premium Economy", "Business", "First"]
ROUTING_PREFERENCES = ["direct", "one_stop", "any"]

def generate_flight_data(num_records: int) -> list:
    """Generates a list of sensible flight booking test cases."""
    
    test_cases = []
    
    for _ in range(num_records):
        # 1. Select distinct cities
        departure_city, arrival_city = random.sample(CITIES, 2)
        
        # 2. Generate departure and return dates
        # Departure date is a random day within a year from the start date
        departure_offset = random.randint(0, 365)
        departure_date = START_DATE + timedelta(days=departure_offset)
        
        # Determine if the trip is round-trip (80% chance)
        is_round_trip = random.choices([True, False], weights=[0.8, 0.2], k=1)[0]
        
        if is_round_trip:
            # Return date is 3 to 21 days after departure
            return_offset = random.randint(3, 21)
            return_date = departure_date + timedelta(days=return_offset)
        else:
            return_date = None
            
        # 3. Generate passenger counts
        adult_passengers = random.choices([1, 2, 3, 4, 5, 6], weights=[0.4, 0.4, 0.05, 0.05, 0.05, 0.05], k=1)[0]
        child_passengers = random.choices([0, 1, 2], weights=[0.7, 0.2, 0.1], k=1)[0]
        # Ensure infants are not more than adults
        infant_passengers = random.choices([0, 1], weights=[0.9, 0.1], k=1)[0] if adult_passengers > 0 else 0

        # 4. Determine cabin class and budget
        # Higher cabins are less likely
        cabin_class = random.choices(CABIN_CLASSES, weights=[0.75, 0.15, 0.08, 0.02], k=1)[0]
        
        # Budget correlates with cabin class
        base_budget = random.randint(300, 1500)
        if cabin_class == "Premium Economy":
            base_budget *= 1.8
        elif cabin_class == "Business":
            base_budget *= 3.5
        elif cabin_class == "First":
            base_budget *= 6.0
        budget = round(base_budget * (1 if not is_round_trip else 1.5))

        # 5. Generate other boolean preferences (most are typically false)
        flexible_dates = random.choices([False, True], weights=[0.9, 0.1], k=1)[0]
        points_booking = random.choices([False, True], weights=[0.95, 0.05], k=1)[0]
        refundable = random.choices([False, True], weights=[0.8, 0.2], k=1)[0]

        # 6. Assemble the final JSON object
        flight_record = {
            "departure_city": departure_city,
            "arrival_city": arrival_city,
            "departure_date": departure_date.isoformat() if departure_date else None,
            "return_date": return_date.isoformat() if return_date else None,
            "adult_passengers": adult_passengers,
            "round_trip": is_round_trip,
            "child_passengers": child_passengers,
            "infant_passengers": infant_passengers,
            "cabin_class": cabin_class,
            "budget": budget,
            "flexible_dates": flexible_dates,
            "routing": random.choice(ROUTING_PREFERENCES),
            "points_booking": points_booking,
            "refundable": refundable
        }
        test_cases.append(flight_record)
        
    return test_cases

def main():
    """Main function to generate data and save it to a file."""
    print(f"Generating {NUM_RECORDS} test records...")
    
    flight_data = generate_flight_data(NUM_RECORDS)
    
    try:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(flight_data, f, indent=4)
        print(f"Successfully created '{OUTPUT_FILE}' with {len(flight_data)} records.")
    except IOError as e:
        print(f"Error: Could not write to file '{OUTPUT_FILE}'. Reason: {e}")

if __name__ == "__main__":
    main()

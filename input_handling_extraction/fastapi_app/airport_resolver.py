import csv
import os

# Load the airport database from the local CSV file
AIRPORTS_DB = []
AIRPORTS_DB_LOADED = False

def load_airport_data_from_csv():
    """
    Loads airport data from 'airports.csv' from OurAirports.com.
    """
    global AIRPORTS_DB, AIRPORTS_DB_LOADED
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        csv_file_path = os.path.join(project_root, 'airports.csv')
        
        with open(csv_file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                AIRPORTS_DB.append(row)
        AIRPORTS_DB_LOADED = True
    except FileNotFoundError:
        print(f"'airports.csv' not found")
    except Exception as e:
        print(f"Failed to load 'airports.csv': {e}")

# Load the data when the module is first imported
load_airport_data_from_csv()

def resolve_airport_info(identifier: str) -> dict:
    """
    Resolves a city or airport code using a hierarchical search (large > medium).
    """
    if not AIRPORTS_DB_LOADED or not identifier:
        return {"status": "not_found"}

    identifier_lower = identifier.strip().lower()

    # Step 1: Find all potential airports matching the identifier
    matching_airports = []
    for airport in AIRPORTS_DB:
        # We only care about airports with IATA codes and scheduled service
        if not airport.get('iata_code') or airport.get('scheduled_service') != 'yes':
            continue

        city_lower = airport.get('municipality', '').lower()
        name_lower = airport.get('name', '').lower()
        
        if identifier_lower in city_lower or identifier_lower in name_lower:
            matching_airports.append(airport)

    if not matching_airports:
        print(f"DEBUG: No airports with scheduled service found for identifier '{identifier_lower}'.")
        return {"status": "not_found"}

    # Step 2: Apply the hierarchical filter (Large > Medium)
    large_airports = [ap for ap in matching_airports if ap.get('type') == 'large_airport']
    
    final_candidates = []
    if large_airports:
        print(f"DEBUG: Prioritizing {len(large_airports)} large airport(s) for '{identifier_lower}'.")
        final_candidates = large_airports
    else:
        medium_airports = [ap for ap in matching_airports if ap.get('type') == 'medium_airport']
        if medium_airports:
            print(f"DEBUG: No large airports found. Using {len(medium_airports)} medium airport(s) for '{identifier_lower}'.")
            final_candidates = medium_airports

    if not final_candidates:
        print(f"DEBUG: Found matches for '{identifier_lower}', but none were large or medium airports.")
        return {"status": "not_found"}

    # Step 3: Return the result based on how many candidates we have
    if len(final_candidates) == 1:
        airport = final_candidates[0]
        print(f"DEBUG: Resolved to single candidate: {airport['name']} ({airport['iata_code']})")
        return {
            "status": "resolved",
            "iata": airport['iata_code'],
            "city": airport.get('municipality', airport.get('name'))
        }
    else:
        # If ambiguous, return the list of options
        sorted_candidates = sorted(final_candidates, key=lambda x: x.get('name'))
        options = [{
            "iata": ap['iata_code'], 
            "name": f"{ap['name']} ({ap.get('municipality', '')})"
        } for ap in sorted_candidates]
        
        print(f"DEBUG: Found ambiguous options for '{identifier_lower}': {options}")
        return {"status": "ambiguous", "data": options[:5]} # Return up to 5 options 
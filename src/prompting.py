def get_initial_actions(site="delta"):
    """Returns a list of initial actions for the agent to take"""
    actions = []
    if site == "delta":
        actions.append(
            {"go_to_url": {"url": "https://www.delta.com", "new_tab": False}}
        )
    if site == "united":
        actions.append(
            {"go_to_url": {"url": "https://www.united.com", "new_tab": False}}
        )
    return actions


# TODO: implement
def get_tasks(intent: dict) -> str:
    """
    Generates a user task based on a prompt template
    and task parameters

    Returns
        A string representing the formatted user task to be passed to the agent
    """
    if intent["flight_type"] == "round-trip":
        task1 = f"""
Search for {intent["flight_type"]} flights from {intent["from"]} to {intent["to"]}.
- Departure Date: {intent["departure_date"]}
- Return Date: {intent["return_date"]}
- Number of Passengers: {intent["num_passengers"]}

Some input fields may be pre-populated. Make sure to clear them before you type into them.
Make sure to double check that the departure and return dates are selected correctly before proceeding.

Once you are presented with a list of flights, you are done.
"""
    else:
        task1 = f"""
Search for {intent["flight_type"]} flights from {intent["from"]} to {intent["to"]}.
- Departure Date: {intent["departure_date"]}
- Number of Passengers: {intent["num_passengers"]}

Some input fields may be pre-populated. Make sure to clear them before you type into them.
Make sure to double check that the departure and return dates are selected correctly before proceeding.

Once you are presented with a list of flights, you are done.
"""

    if intent["flight_type"] == "round-trip":
        task2 = f"""
You are booking a round-trip flight from {intent["from"]} to {intent["to"]}.
Select the cheapest departing flight and returning flight, regardless of restrictions.
Continue with the airline booking process until you are prompted to provide any traveler info.
Once this occurs, you are done.
"""
    else:
        task2 = f"""
You are booking a one-way flight from {intent["from"]} to {intent["to"]}.
Select the cheapest departing flight, regardless of restrictions.
Continue with the airline booking process until you are prompted to provide any traveler info.
Once this occurs, you are done.
"""

    task3 = f"""
You are booking a one-way flight from {intent["from"]} to {intent["to"]}.
Populate any passenger information using the information provided below. If there is more than one passenger, treat Passenger #1 as the primary contact for any booking or confirmation details.

Continue with the airline booking process until you are prompted to provide any payment info.
Once this occurs, you are done.

Passenger #1:
- FIRST NAME: {intent["passengers"][0]["first_name"]}
- LAST NAME: {intent["passengers"][0]["last_name"]}
- DATE OF BIRTH: {intent["passengers"][0]["dob"]}
- GENDER: {intent["passengers"][0]["gender"]}
- EMAIL: {intent["passengers"][0]["email"]}
- PHONE NUMBER: {intent["passengers"][0]["phone_number"]}
- EMERGENCY CONTACT: {intent["passengers"][0]["emergency_contact"]}
"""

    # """
    # ### STEP 2
    # Review the list of available flights and select the cheapest flight, regardless of seating, baggage, or other restrictions.

    # ### STEP 3
    # Populate any passenger information using the information provided below. If there is more than one passenger, treat Passenger #1 as the primary contact for any booking or confirmation details.
    # Once you are done populating passenger information, your task is complete. Do not provide any payment or billing information.

    # Passenger #1:
    # - FIRST NAME: Kenneth
    # - LAST NAME: Lin
    # - DATE OF BIRTH: September 15, 1999
    # - GENDER: Male
    # - EMAIL: kenneth.alex.lin@gmail.com
    # - PHONE NUMBER: +1 626 375 6087
    # - EMERGENCY CONTACT: Do not add an emergency contact
    # """

    return task1, task2, task3


# Book a {intent["flight_type"]} flight from {intent["from"]} to {intent["to"]} for {intent["num_passengers"]} passenger(s).
# The flight must depart on {intent["departure_date"]} and return on {intent["return_date"]}.
# Search for available flights and select the cheapest flight that meets that criteria, regardless of seating or baggage restrictions.
# Populate any passenger information using the information provided below. If there is more than one passenger, treat Passenger #1 as the primary contact for any booking or confirmation details.
# Once your next task is to provide payment or billing information, your task is complete.

#     task = """
# ### Step 1
# - Open [Delta Airlines](https://www.delta.com).
# - Close any popups that appear before proceeding.
# - Complete Step 1 fully before moving on.

# ---

# ### Step 2

# 1. In the "From" field:
#    - Click the field.
#    - Make sure the search says "Origin"
#    - Type ATL and wait until dropdown suggestions appear.
#    - Click the suggestion exactly matching "ATL Atlanta, GA".
#    - The drop down should now disapear, if not click the Atlanda airport from the drop down.
#    - Do not proceed until confirmed.

# 2. In the To field:
#    - Click the field.
#    - Make sure the search says "Destination"
#    - Type JFK and wait until dropdown suggestions appear.
#    - Click the suggestion exactly matching "JFK New York-Kennedy, NY".
#    - The drop down should now disapear, if not click the JFK airport from the drop down.
#    - Do not proceed until confirmed.

# 3. Change to one-way trip:
#    - Click the trip type button (currently shows "Round Trip")
#    - There will be 3 options, "Round Trip", "One Way", and "Multi-City", select the middle option "One Way"
#    - Click "One Way" from the dropdown menu
#    - The drop down should now disapear.
#    - Make sure the trip type clearly shows "One Way" is selected.
#    - Only proceed to step 4 if "One Way" is confirmed

# 4. Set departure date:
#    - Click the departure date field
#    - Navigate to August 2025 in the calendar
#    - Click on selectable day that has the number "11"
#    - Now click the "Done" button in the bottom right corner of the calendar
#    - VERIFY: Check that the date field shows "Aug 11" or "August 11, 2025" (do not click the field again)
#    - Only proceed to step 5 if August 11, 2025 is confirmed

# 5. Confirm 1 adult passenger (should be default)
#    - VERIFY: Check that passenger count shows "1 Adult" (do not change unless it shows something different)

# 6. Click "Search" or "Find Flights" button

# **Important: Complete each step fully before moving to the next step. If any step fails, retry that step before continuing.**

# """

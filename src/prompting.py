import sys

# TODO: no longer need to add this to path once we re-organize project
# replace this with the absolute path to the pydantic data models file
sys.path.append(
    "/Users/kennyalexlin/Desktop/MIDS/W210/aitinerary-capstone/input_handling_extraction/fastapi_app/models"
)
from chat import FlightInfo, UserBillingInfo, UserInfo, UserPreferences


def get_initial_actions(site: str) -> list[dict]:
    """Returns a list of initial actions for the agent to take"""
    actions = []
    if site == "delta":
        actions.append(
            {"go_to_url": {"url": "https://www.delta.com", "new_tab": False}}
        )
    elif site == "united":
        actions.append(
            {"go_to_url": {"url": "https://www.united.com", "new_tab": False}}
        )
    elif site == "southwest":
        actions.append(
            {"go_to_url": {"url": "https://www.southwest.com", "new_tab": False}}
        )
    else:
        actions.append({"go_to_url": {"url": site, "new_tab": False}})

    return actions


def get_tasks(
    flight_info: FlightInfo,
    user_info_ls: list[UserInfo],
    user_billing_info: UserBillingInfo,
    user_preferences: UserPreferences = None,
) -> tuple[str]:
    """
    Injects user context into a series of prompt templates for tasks 1 - 4

    Returns
        a tuple of form (task1, task2, task3, task4)
    """

    assert flight_info["adult_passengers"] == len(user_info_ls), (
        f"flight_info['adult_passengers'] is {flight_info['adult_passengers']} but user_info only contains {len(user_info_ls)} users."
    )

    # map routing to natural language description
    routing_mapping = {
        "direct": "Nonstop Flights Only",
        "one_stop": "Nonstop or One-Stop Flights Only",
        "any": "Nonstop or Multi-Stop Flights Allowed",
    }
    flight_type = "round-trip" if flight_info["round_trip"] else "one-way"

    def fmt_user_info(user_info: UserInfo) -> str:
        """formats a UserInfo object for use by the agent"""

        ret = ""
        for key, value in user_info.items():
            if value is None:
                continue
            ret += f"- {key.replace('_', ' ').title()}: {value}\n"
        return ret

    def fmt_user_billing_info(user_billing_info: UserBillingInfo) -> str:
        """formats billing info for use by the agent"""

        ret = ""
        for key, value in user_billing_info.items():
            if value is None:
                continue
            ret += f"- {key.replace('_', ' ').title()}: {value}\n"
        return ret

    task1 = f"""
Your goal is to search for **{flight_type}** flights from {flight_info["departure_code"]} to {flight_info["arrival_code"]}.

You should only search for flights that match the following criteria:
- Departure Airport Code: {flight_info["departure_code"]}
- Arrival Airport Code: {flight_info["arrival_code"]}
- Trip Type: {flight_type}
- Departure Date: {flight_info["departure_date"]}"""
    if flight_info["round_trip"]:
        task1 += f"\n- Return Date {flight_info['return_date']}"
    task1 += f"""
- Return Date: {flight_info["return_date"]}
- Number of Passengers: {flight_info["adult_passengers"]}
- Routing Type: {routing_mapping[flight_info["routing"]]}
- Cabin Class: {flight_info["cabin_class"]} Only

Some input fields may be pre-populated. Make sure to clear them before you type into them.
Make sure to double check that the departure and return dates are selected correctly before proceeding.

Once you are presented with a list of flights, you are done.
"""
    task2 = f"""
You are booking a {flight_type} flight from {flight_info["departure_code"]} to {flight_info["arrival_code"]}. You are currently on the page to select a flight.
Your goal is to select the cheapest departing flight, regardless of restrictions and continue with the flight booking process until you reach a page requesting traveler personal info (e.g. First Name, Last Name, Birthday).
Make sure to review all available flights in order to determine which is the cheapest. You may need to scroll the page up or down in order to see all of the options.

Once you reached this page, you are done.
"""

    task3 = f"""
You are booking a {flight_type} flight from {flight_info["departure_code"]} to {flight_info["arrival_code"]}. You are currently on the page to provide traveler information to the airline.
Your goal is to accurately populate and submit the form using the passenger information provided below. Note that not all fields will be required to submit the form. Only populate fields that are required.

You may need to expand some page elements in order to access all form elements.
If there are form elements that are not visible in the viewport, use the scroll action.

Continue with the airline booking process until you are prompted to provide any payment info. Make sure that you have successfully navigated to a page that is requesting your billing information.
Once this occurs, you are done.

"""

    for idx, user_info in enumerate(user_info_ls):
        task3 += f"**Passenger #{idx + 1}**\n"
        task3 += fmt_user_info(user_info)

    task4 = f"""
You are booking a {flight_type} flight from {flight_info["departure_code"]} to {flight_info["arrival_code"]}. You are currently on the page to provide payment information and complete your booking.
Your goal is to populate all requested billing information using the billing details provided below. DO NOT SUBMIT OR CONFIRM PURCHASE IN ANY WAY.

Once you have filled in all required fields and request assistance from the user with the request_msg: "I have populated your payment information. Please review it, correct any errors, and complete the booking process."

**Billing Info**
{fmt_user_billing_info(user_billing_info)}
"""
    return task1, task2, task3, task4


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

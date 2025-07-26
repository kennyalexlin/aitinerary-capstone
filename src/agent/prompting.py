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
        "one_stop": "Nonstop or One-Stop Flights Allowed",
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

    ### TASK 1
    task1 = f"""
# CONTEXT
You are booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
You are currently on the home page of an airline. There should be a form to search for flights.
If you do not see a form to search for flights, immediately exit by using the "done" action with success=False. 
    
# GOAL
Your goal is to search for **{flight_type}** flights from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}.

# FLIGHT SEARCH CRITERIA
- **Trip Type**: {flight_type}
- **Departure Airport Code**: {flight_info["departure_airport"]}
- **Arrival Airport Code**: {flight_info["arrival_airport"]}
- **Departure Date**: {flight_info["departure_date"]}"""
    if flight_info["round_trip"]:
        task1 += f"\n- **Return Date** {flight_info['return_date']}"
    task1 += f"""
- **Number of Passengers**: {flight_info["adult_passengers"]}
- **Routing Type**: {routing_mapping[flight_info["routing"]]}
- **Cabin Class**: {flight_info["cabin_class"]}

# COMMON ISSUES
- Some input fields may be pre-populated - clear them before typing.
- Depending on the airline, not every field will be applicable when searching for flights. If the search form doesn't accept one or more of the FLIGHT SEARCH CRITERIA, ignore it and proceed. For example, Southwest does not require Cabin Class or Routing Type to search for flights. 
- Date pickers may default to today's date. Always verify that the correct departure and return dates (if applicable) are selected before proceeding.
- You will need to click a button to actually submit your search query. Common labels for this button are "Search Flights" or "Find Flights". Make sure that you are using the correct button, as some promotional buttons (e.g. "Book Now") will navigate you away from the search page.

# VALIDATION STRATEGY
Before clicking the button to submit your search query, use your screenshot of the page to verify that:
1. The trip type shows that you are searching for "{flight_type}" flights
2. The departure airport shows as "{flight_info["departure_airport"]}" 
3. The arrival airport shows as "{flight_info["arrival_airport"]}"
4. The departure date shows as "{flight_info["departure_date"]}"
"""
    if flight_info["round_trip"]:
        task1 += f'4. The return date shows as "{flight_info["return_date"]}"'
    task1 += """

# SUCCESS CRITERIA
You have successfully completed this task when you are presented with a list of departing flights, times, and prices.
"""

    ### TASK 2
    if flight_info["round_trip"]:
        task2 = f"""
# CONTEXT
You are booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
You are currently on the page to select a departing flight from a list of available options.
If you do not see a list of flight options, immediately exit by using the "done" action with success=False. 

# GOAL
Your goal is to review flight options and select the **cheapest** departing and returning flights that meet the following criteria:
- Routing Type: {routing_mapping[flight_info["routing"]]}
- Cabin Class: {flight_info["cabin_class"]}

# SELECTION STRATEGY
1. Sort flights by price (lowest to highest) if the option is available
2. Look for the cheapest option that meets cabin and routing requirements
3. If multiple flights have the same price, choose the one with better timing or fewer stops

# COMMON ISSUES
- Some airlines have the departing and returning flight selections on different pages. Verify that each flight matches the requirements before proceeding.
- Some sites require clicking a button to confirm each selected flight, such as a "Select Next Flight" or "Continue" button.

# SUCCESS CRITERIA
You have successfully completed this task when you reach a page asking for passenger information (e.g. First Name, Last Name, Date of Birth)
"""

    else:
        task2 = f"""
# CONTEXT
You are booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
You are currently on the page to select a departing flight from a list of available options.
If you do not see a list of flight options, immediately exit by using the "done" action with success=False. 

# GOAL
Your goal is to review flight options and select the **cheapest** departing flight that meets the following criteria:
- Routing Type: {routing_mapping[flight_info["routing"]]}
- Cabin Class: {flight_info["cabin_class"]}

# SELECTION STRATEGY
1. Sort flights by price (lowest to highest) if the option is available
2. Look for the cheapest option that meets cabin and routing requirements
3. If multiple flights have the same price, choose the one with better timing or fewer stops

# COMMON ISSUES
- Some sites require clicking a button to confirm your selected flight, such as a "Continue" or "Confirm Selection" button.

# SUCCESS CRITERIA
You have successfully completed this task when you reach a page asking for passenger information (e.g. First Name, Last Name, Date of Birth)
"""

    task3 = f"""
# CONTEXT
You are booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
You are currently on the page to provide traveler information to the airline.
If you do not see a form requesting traveler information, immediately exit by using the "done" action with success=False. 


# GOAL
Your goal is to accurately populate and submit the form using the passenger information provided below. Note that not all fields will be required to submit the form. Only populate fields that are required.

# COMMON ISSUES
- Depending on which airline you are booking with, not every piece of passenger info will be required to submit the form. Only populate fields the form requires. For example, Southwest may not require each passenger's address.
- You may need to expand some page elements in order to access all form elements.
- If there are form elements that are not visible in the viewport, use the scroll action.

# VERIFICATION STRATEGY
Before proceeding, use your screenshot of the page to verify that all required passenger information has been entered correctly.

# SUCCESS CRITERIA
You have successfully completed this task when you have submitted passenger information and reach a page that requests payment information.

# PASSENGER INFO
"""

    for idx, user_info in enumerate(user_info_ls):
        task3 += f"## Passenger #{idx + 1}**\n"
        task3 += fmt_user_info(user_info)

    task4 = f"""
# CONTEXT
You are booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
You are currently on the page to provide payment information and complete your booking.
If you do not see a form requesting payment information, immediately exit by using the "done" action with success=False. 

# GOAL
Your goal is to populate all requested billing information using the billing details provided below. 

# CRITICAL
DO NOT CLICK ANY BUTTONS THAT COMPLETE THE PURCHASE. 
Examples include:
- "Complete Purchase"
- "Buy Now" 
- "Confirm Booking"
- "Submit Payment"
- "Book Flight"

# SUCCESS CONDITION
You have successfully completed this task once you have filled in all required fields accurately. 

Verify all required billing information and request assistance from the user with the request_msg: "I have populated your payment information. Please review it, correct any errors, and complete the booking process."

# BILLING INFO
{fmt_user_billing_info(user_billing_info)}
"""
    return task1, task2, task3, task4

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
    flight_info: dict,
    user_info_ls: list[dict],
    user_billing_info: dict,
) -> tuple[str, str, str, str]:
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

    def fmt_user_info(user_info: dict) -> str:
        """formats a UserInfo object for use by the agent"""

        ret = ""
        for key, value in user_info.items():
            if value is None:
                continue
            ret += f"- {key.replace('_', ' ').title()}: {value}\n"
        return ret

    def fmt_user_billing_info(user_billing_info: dict) -> str:
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
Your goal is to search for **{flight_type}** flights from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]} using the form.
If done correctly, submitting the form will take you to a page that lists different possible departing flights by time, price, and other characteristics.
The button to submit your search query will be labeled "Search Flights" or something similar.
After clicking the button to submit your search query, wait for the page to load and verify you have reached this page using the DOM and your screenshot of the page.
Do NOT indicate success until you have reached the page that lists possible departing flights.

## FLIGHT SEARCH CRITERIA
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

## VALIDATION STRATEGY
Before clicking the button to submit your search query, use your screenshot of the page to verify that:
1. The trip type shows that you are searching for "{flight_type}" flights
2. The departure airport shows as "{flight_info["departure_airport"]}" 
3. The arrival airport shows as "{flight_info["arrival_airport"]}"
4. The departure date shows as "{flight_info["departure_date"]}"
"""
    if flight_info["round_trip"]:
        task1 += f'5. The return date shows as "{flight_info["return_date"]}"'
    task1 += """

# COMMON ISSUES
- Date pickers can be finnicky. When populating the departure and return date, use the input_text action first. Provide the date in the form "MMDD". Then, select the desired date in the picker.
- Some input fields may be pre-populated - ALWAYS use clear_text before using input_text to avoid issues.
- Depending on the airline, not every field will be applicable when searching for flights. If the search form doesn't accept one or more of the FLIGHT SEARCH CRITERIA, ignore it and proceed. For example, Southwest does not require Cabin Class or Routing Type to search for flights. 
- Date pickers may default to today's date. Always verify that the correct departure and return dates (if applicable) are selected before proceeding.
- You will need to click a button to actually submit your search query. Common labels for this button are "Search Flights" or "Find Flights". Make sure that you are using the correct button, as some promotional buttons (e.g. "Book Now", "Learn More") will navigate you away from the search page.
"""

    ### TASK 2
    if flight_info["round_trip"]:
        task2 = f"""
# CONTEXT
You are in the process of booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
You should currently be on the page to select a departing flight from a list of available options.
If you do not see a list of different options for flight times, prices, and cabin classes, immediately exit by using the "done" action with success=False. 

# GOAL
Your overall goal is to continue with the booking process until you reach a page that requests Passenger or Traveler Information such as First Name, Last Name, and Date of Birth.
There are 3 general steps for this:
1. Review available flight options and select the **cheapest** departing flight that meets the following criteria:
    - Routing Type: {routing_mapping[flight_info["routing"]]}
    - Cabin Class: {flight_info["cabin_class"]}
2. Review available flight options and select the **cheapest** returning flight that meets the same criteria.
3. Confirm your selections and navigate through any additional confirmation pages until you reach the Passenger or Traveler Information page.

For each step, you will need to click some kind of button to confirm your selection or proceed to the next page. Typical button labels include "Select Next Flight" and "Continue". 
You may need to scroll to find this button.
For example, after selecting your departing flight, you will need to scroll down and select "Select Next Flight" in order to proceed to the page for selecting your returning flight.

Do NOT indicate success until you have reached the page requesting Passenger or Traveler information. 
Confirm that you have reached this page using the DOM and your screenshot of the page.

## SELECTION STRATEGY
When selecting a departing and returning flight, use the following strategy:
1. Sort flights by price (lowest to highest) if the option is available
2. Look for the cheapest option that meets cabin and routing requirements
3. If multiple flights have the same price, you may pick any of them.

# COMMON ISSUES
- Some airlines have the departing and returning flight selections on different pages. If so, the first page will be for the departing flight and the second page will be for the returning flight.
- Some sites require clicking a button to confirm your selections, such as a "Select Next Flight" or "Continue" button. This button may also not be visible without scrolling on the page.
"""

    else:
        task2 = f"""
# CONTEXT
You are in the process of booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
You should currently be on the page to select a departing flight from a list of available options.
If you do not see a list of different options for flight times, prices, and cabin classes, immediately exit by using the "done" action with success=False. 

# GOAL
Your overall goal is to continue with the booking process until you reach a page that requests Passenger or Traveler Information such as First Name, Last Name, and Date of Birth.
There are 2 general steps for this:
1. Review available flight options and select the **cheapest** departing flight that meets the following criteria:
    - Routing Type: {routing_mapping[flight_info["routing"]]}
    - Cabin Class: {flight_info["cabin_class"]}
2. Confirm your selection and navigate through any additional confirmation pages until you reach the Passenger or Traveler Information page.

Do NOT indicate success until you have reached the page requesting Passenger or Traveler information. 
Confirm that you have reached this page using the DOM and your screenshot of the page.

## SELECTION STRATEGY
When selecting a departing flight, use the following strategy:
1. Sort flights by price (lowest to highest) if the option is available
2. Look for the cheapest option that meets cabin and routing requirements
3. If multiple flights have the same price, you may pick any of them.

# COMMON ISSUES
- Some sites require clicking a button to confirm your selections, such as a "Select Next Flight" or "Continue" button. This button may also not be visible without scrolling on the page.
"""

    task3 = f"""
# CONTEXT
You are in the process of booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
You are currently on the page to provide traveler information to the airline.
If you do not see a form requesting traveler information, immediately exit by using the "done" action with success=False. 


# GOAL
Your goal is to accurately populate and submit the form using the passenger information provided below. 
Once you have done so, continue the booking process until you reach a page that requests Billing or Payment Information.

Do NOT indicate success until you have reached the page requesting Billing or Payment information. Confirm that you have reached this page using the DOM and your screenshot of the page.

# COMMON ISSUES
- Depending on which airline you are booking with, not every piece of passenger info will be required to submit the form. Only populate fields the form requires. For example, Southwest may not require each passenger's address.
- You may need to expand some page elements in order to access all form elements
- If there are form elements that are not visible in the viewport, use the scroll action.

# PASSENGER INFO
"""

    for idx, user_info in enumerate(user_info_ls):
        task3 += f"## Passenger #{idx + 1}**\n"
        task3 += fmt_user_info(user_info)

    task4 = f"""
# CONTEXT
You are in the process of booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
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

# SUCCESS CRITERIA
You have successfully completed this task once you have filled in all required fields accurately. 

# BILLING INFO
{fmt_user_billing_info(user_billing_info)}
"""
    return task1, task2, task3, task4

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
                value = "Not Applicable"
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
Before taking any action, always:
1. Use your screenshot to verify that the current state matches your intended action
2. If selecting from a dropdown, confirm the selected value is visible in the screenshot
3. State explicitly what you see vs what you intended.

## POPOVER STRATEGY
When interacting with dropdowns or date pickers, always follow the following steps:
1. Review your screenshot of the current state
2. Click to open the dropdown/picker
3. Review your screenshot again to see available options
4. Select the correct option
5. Review your screensot again to confirm the selection
6. Only then proceed to the next field

# GOAL COMPLETION VERIFICATION
Before indicating that the goal is complete, you must:
1. Take a final screenshot
2. Identify 3 specific visual indicators that prove you've reached the target state
3. List what you expected to see vs what you actually see
4. Only mark complete if ALL indicators match expectations
"""

    task1 += """

# COMMON ISSUES
- Date pickers can be finnicky. When populating the departure and return date, use the input_text action first. Provide the date in the form "MMDD". Then, select the desired date in the picker.
- Some input fields may be pre-populated - ALWAYS use clear_text before using input_text to avoid issues.
- Depending on the airline, not every field will be applicable when searching for flights. If the search form doesn't accept one or more of the FLIGHT SEARCH CRITERIA, ignore it and proceed. For example, Southwest does not require Cabin Class or Routing Type to search for flights. 
- Date pickers may default to today's date. Always verify that the correct departure and return dates (if applicable) are selected before proceeding.
- You will need to click a button to actually submit your search query. Common labels for this button are "Search Flights" or "Find Flights". Make sure that you are using the correct button, as some promotional buttons (e.g. "Book Now", "Learn More") will navigate you away from the search page.

# RECOVERY STRATEGY
If you find yourself stuck or unable to locate expected elements, try these options in order:
1. Scroll on the page to find missing elements
2. Refresh the page once
3. If you are still stuck, use the "done" action with success=False. 
"""

    ### TASK 2
    if flight_info["round_trip"]:
        task2 = f"""
# CONTEXT
You are in the process of booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
You should currently be on the page to select a departing flight from a list of available options.
If you do not see a list of different options for flight times, prices, and cabin classes, immediately exit by using the "done" action with success=False. 

# GOAL
Your overall goal is to continue with the booking process until you reach a page that explicitly requests Passenger or Traveler Information such as First Name, Last Name, and Date of Birth.
There are 3 general steps for this:
1. Review available flight options and select the **cheapest** departing flight. Continue to the returning flight selection page.
    - The flight must meet the following criteria:
        - Routing Type: {routing_mapping[flight_info["routing"]]}
        - Cabin Class: {flight_info["cabin_class"]}
    - Indicators of success:
        1. Page title or page URL changes from the departure selection page. Typically they will contain the word "Return".
        2. There is a "departing flight" summary visible showing your previously selected departing flight.
2. Review available flight options and select the **cheapest** returning flight. Continue to the next page.
    - The flight must meet the same criteria as above.
    - Indicators of success:
        1. The page title or page URL changes from the return selection page. Typically you will be on some kind of confirmation or add-ons page.
2. Navigate from the confirmation or add-ons page to the page that explicitly requests Passenger or Traveler information. You may need to scroll to find a "Continue" button.

## FLIGHT SELECTION STRATEGY
When selecting a departing and returning flight, use the following strategy:
1. Sort flights by price (lowest to highest) if the option is available
2. Look for the cheapest option that meets cabin and routing requirements
3. If multiple flights have the same price, you may pick any of them.

# GOAL COMPLETION VERIFICATION
Before indicating that the goal is complete, you must:
1. Take a final screenshot
2. Identify 3 specific visual indicators that prove you've reached the target state
3. List what you expected to see vs what you actually see
4. Only mark complete if ALL indicators match expectations

# RECOVERY STRATEGY
If you find yourself stuck or unable to locate expected elements, try these options in order:
1. Scroll on the page to find missing elements
2. Refresh the page once
3. If you are still stuck, use the "done" action with success=False. 
"""

    else:
        task2 = f"""
# CONTEXT
You are in the process of booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
You should currently be on the page to select a departing flight from a list of available options.
If you do not see a list of different options for flight times, prices, and cabin classes, immediately exit by using the "done" action with success=False. 

# GOAL
Your overall goal is to continue with the booking process until you reach a page that explicitly requests Passenger or Traveler Information such as First Name, Last Name, and Date of Birth.
There are 2 general steps for this:
1. Review available flight options and select the **cheapest** departing flight. Continue to the next page.
    - The flight must meet the following criteria:
        - Routing Type: {routing_mapping[flight_info["routing"]]}
        - Cabin Class: {flight_info["cabin_class"]}
    - Indicators of success:
        1. Page title or page URL changes from the departure selection page. Typically you will be on some kind of confirmation or add-ons page.
2. Navigate from the confirmation or add-ons page to the page that explicitly requests Passenger or Traveler information. You may need to scroll to find a "Continue" button.

## FLIGHT SELECTION STRATEGY
When selecting a departing flight, use the following strategy:
1. Sort flights by price (lowest to highest) if the option is available
2. Look for the cheapest option that meets cabin and routing requirements
3. If multiple flights have the same price, you may pick any of them.

# GOAL COMPLETION VERIFICATION
Before indicating that the goal is complete, you must:
1. Take a final screenshot
2. Identify 3 specific visual indicators that prove you've reached the target state
3. List what you expected to see vs what you actually see
4. Only mark complete if ALL indicators match expectations

# RECOVERY STRATEGY
If you find yourself stuck or unable to locate expected elements, try these options in order:
1. Scroll on the page to find missing elements
2. Refresh the page once
3. If you are still stuck, use the "done" action with success=False. 
"""

    task3 = f"""
# CONTEXT
You are in the process of booking a {flight_type} flight from {flight_info["departure_airport"]} to {flight_info["arrival_airport"]}. 
You are currently on the page to provide traveler information to the airline.
If you do not see a form requesting traveler information, immediately exit by using the "done" action with success=False. 

# GOAL
Your goal is to accurately populate and submit the form using the passenger information provided below. 
ONLY fill fields that actually exist - ignore any passenger information that doesn't have a corresponding field.
Once you have done so, continue the booking process until you reach a page that explicitly requests Billing or Payment Information.

# GOAL COMPLETION VERIFICATION
Before indicating that the goal is complete, you must:
1. Take a final screenshot
2. Identify 3 specific visual indicators that prove you've reached the target state
3. List what you expected to see vs what you actually see
4. Only mark complete if ALL indicators match expectations

# COMMON ISSUES
- You may need to expand some page elements in order to access all form elements
- If there are form elements that are not visible in the viewport, use the scroll action.

# RECOVERY STRATEGY
If you find yourself stuck or unable to locate expected elements, try these options in order:
1. Scroll on the page to find missing elements
2. Refresh the page once
3. If you are still stuck, use the "done" action with success=False

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

# GOAL COMPLETION VERIFICATION
Before indicating that the goal is complete, you must:
1. Take a final screenshot
2. Identify 3 specific visual indicators that prove you've reached the target state
3. List what you expected to see vs what you actually see
4. Only mark complete if ALL indicators match expectations

# RECOVERY STRATEGY
If you find yourself stuck or unable to locate expected elements, try these options in order:
1. Scroll on the page to find missing elements
2. Refresh the page once
3. If you are still stuck, use the "done" action with success=False. 

# BILLING INFO
{fmt_user_billing_info(user_billing_info)}
"""
    return task1, task2, task3, task4

import sys

# TODO: no longer need to add this to path once we re-organize project
# replace this with the absolute path to the pydantic data models file
sys.path.append(
    "/Users/jimxu/Desktop/aitinerary/aitinerary-capstone-main/input_handling_extraction/fastapi_app/models"
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

In particular, search for flights that match the following criteria:
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
- Cabin Class: {flight_info["cabin_class"]}

You will receive a list of DOM controls with fields: index, tag, text.
Select the correct input fields for the above criteria and sequentially:
1. click the input (by index),
2. use the above criteria to search for flights,

NOTE: Depending on which airline you are booking with, not every field will be applicable when searching for flights. If one or more criteria isn't requested, you may proceed without filtering on it.
For example, you do not need to select Cabin Class or Routing Type for Southwest to search for flights. 

Some input fields may be pre-populated. Make sure to clear them before you type into them.
Make sure to double check that the departure and return dates (if applicable) are selected correctly before proceeding.

3. click the “Search flights” button (by index).

Once you are presented with a list of flights, you are done.
"""
    task2 = f"""
You are booking a {flight_type} flight from {flight_info["departure_code"]} to {flight_info["arrival_code"]}. You are currently on the page to select a flight from a list of available options.

Your goal is to review the options and select the **cheapest** departing flight that meets the following criteria
- Routing Type: {routing_mapping[flight_info["routing"]]}
- Cabin Class: {flight_info["cabin_class"]}

Continue with the flight booking process until you reach a page requesting traveler personal info (e.g. First Name, Last Name, Birthday). Once you reach this page, you are done.
"""

    task3 = f"""
You are booking a {flight_type} flight from {flight_info["departure_code"]} to {flight_info["arrival_code"]}. You are currently on the page to provide traveler information to the airline.
Your goal is to accurately populate and submit the form using the passenger information provided below. Note that not all fields will be required to submit the form. Only populate fields that are required.

NOTE: Depending on which airline you are booking with, not every piece of passenger info will be required to submit the form. Only populate fields the form requires.
For example, Southwest may not require each passenger's address.

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

import asyncio
import logging
import os
import sys
from datetime import datetime

from browser_use import Agent
from browser_use.llm import ChatGoogle
from dotenv import load_dotenv

from controller import custom_controller
from prompting import get_initial_actions, get_tasks
from session import create_fresh_browser_session

# TODO: no longer need to add this to path once we re-organize project
# replace this with the absolute path to the pydantic data models file
sys.path.append(
    "/Users/kennyalexlin/Desktop/MIDS/W210/aitinerary-capstone/input_handling_extraction/fastapi_app/models"
)
from chat import FlightInfo, UserBillingInfo, UserInfo, UserPreferences


async def do_flight_booking(
    flight_info: FlightInfo,
    user_info_ls: list[UserInfo],
    user_billing_info: UserBillingInfo,
    user_preferences: UserPreferences = None,
    logs_path: str = "logs",
):
    """Kick off agentic flight booking process.

    There are 4 "tasks" currently defined:
        1. Search for a flight on the home page
        2. Select a flight
            TODO: implement use of the budget parameter instead of just searching for the cheapest flight
        3. Populate traveler information
        4. Populate billing information - currently requests confirmation from the user once for review once info has been populated

    Args
        flight_info: a FlightInfo object representing the parameters to use when searching
            and selecting a flight to book
        user_info_ls: a list of UserInfo objects representing the traveler information for all passengers
            NOTE: for MVP, this will always be of length 1
        user_billing_info: a UserBillingInfo object representing the billing information to use for the flight booking
        user_preferences (optional): a UserPreferences object representing booking-specific preferences to apply, e.g. seat preference
        logs_path (optional): filepath to save all of the logs associated with this run. Runs are tagged by the
            timestamp this function was called

    """
    # load environment variables
    load_dotenv()

    # define paths for logs
    # browser-use already creates its own uid for logs but we need a way to organize
    # multiple sets of logs in the same run
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")

    run_logs_path = os.path.join(logs_path, run_id)
    task1_logs_path = os.path.join(run_logs_path, "task1")
    task2_logs_path = os.path.join(run_logs_path, "task2")
    task3_logs_path = os.path.join(run_logs_path, "task3")
    task4_logs_path = os.path.join(run_logs_path, "task4")
    logging.info(f"Logs will be saved to {run_logs_path}")

    # define model to use
    model = "gemini-2.0-flash"
    # model = 'gpt-4.1-mini'
    llm = ChatGoogle(model=model, temperature=0.0)
    # llm = ChatOpenAI(model=model, temperature=0)
    logging.info(f"Initialized LLM with model {model}")

    # generate user tasks for agent
    task1, task2, task3, task4 = get_tasks(
        flight_info=flight_info,
        user_info_ls=user_info_ls,
        user_billing_info=user_billing_info,
    )
    logging.info("Tasks generated successfully:")
    logging.info(f"TASK #1: SEARCH FOR FLIGHTS\n{task1}")
    logging.info(f"TASK #2: SELECT A FLIGHT\n{task2}")
    logging.info(f"TASK #3: FILL IN PASSENGER INFO\n{task3}")
    logging.info(f"TASK #4: FILL IN PAYMENT INFO\n{task4}")

    # initialize and kick off chromium browser session
    browser_session = create_fresh_browser_session()
    logging.info("Created fresh browser session")
    await browser_session.start()
    logging.info("Browser session initialized")

    # do agentic booking!
    extended_system_message = """
    <critical_rules>
    You will be interacting with very dense, dynamic pages. Be conservative when using any actions that will alter your view of the page.
    Below is a list of CRITICAL rules that must always be followed. Failure to adhere to them will lead to unstable page interactions that may make accomplishing your goal impossible.
    1. Never click or input text into an element on the page that is obscured or partly obscured. Use the provided screenshot of the page in order to confirm that the target element is fully visible before taking action. If it's obscured, take action to reveal it such as scrolling the page or expanding accordion widgets.
    2. Whenever you use the scroll action, prefer to scroll in half-page increments (num_pages = 0.5). Scrolling a full page or more can accidentally obscure content. 
    3. If you are prompted to accept cookies, you must do this before taking any other task. This pop-up may obscure other critical page elements.
    </critical_rules>
    """

    # step 1 - Search for flights
    agent = Agent(
        controller=custom_controller,
        task=task1,
        llm=llm,
        initial_actions=get_initial_actions(site="southwest"),
        browser_session=browser_session,
        save_conversation_path=task1_logs_path,
        use_vision=True,
        extended_system_message=extended_system_message,
    )
    result = await agent.run()

    # step 2
    agent = Agent(
        controller=custom_controller,
        task=task2,
        llm=llm,
        browser_session=browser_session,
        save_conversation_path=task2_logs_path,
        use_vision=True,
        extend_system_message=extended_system_message,
    )
    result = await agent.run()

    # step 3
    agent = Agent(
        controller=custom_controller,
        task=task3,
        llm=llm,
        browser_session=browser_session,
        save_conversation_path=task3_logs_path,
        use_vision=True,
        extend_system_message=extended_system_message,
    )
    result = await agent.run()

    # step 4
    agent = Agent(
        controller=custom_controller,
        task=task4,
        llm=llm,
        browser_session=browser_session,
        save_conversation_path=task4_logs_path,
        use_vision=True,
        extend_system_message=extended_system_message,
    )
    result = await agent.run()


# define demo flight info
flight_info = {
    "departure_code": "LAX",
    "arrival_code": "SFO",
    "departure_date": "2025-09-01",
    "return_date": None,
    "adult_passengers": 1,
    "round_trip": False,
    "cabin_class": "Basic",
    "routing": "direct",
}

# define demo UserInfo
user_info_ls = [
    {
        "first_name": "Kenneth",
        "last_name": "Lin",
        "gender": "Male",
        "date_of_birth": "1999-09-15",
        "name_suffix": None,
        "email": "kenneth.alex.lin@gmail.com",
        "phone_number": "+1 626 375 6087",
        "country": "USA",
        "home_address": "2850 Kelvin Ave Apt 123, Irvine, CA 92614",
        "passport_number": None,
        "rewards_account_number": None,
    }
]

# define demo UserBillingInfo
user_billing_info = {
    "type": "Credit Card",
    "card_number": "4147 5678 9100",
    "expiration_date": "09-2026",
    "cvv": "808",
    "billing_address": "1234 Green Valley Rd, Salt Lake City, UT 71854",
    "phone_number": "+1 881 849 9102",
    "email_address": "kenneth.alex.lin@gmail.com",
}


async def main():
    await do_flight_booking(
        flight_info=flight_info,
        user_info_ls=user_info_ls,
        user_billing_info=user_billing_info,
    )


if __name__ == "__main__":
    asyncio.run(main())

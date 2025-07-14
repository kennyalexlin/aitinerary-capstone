import asyncio
import os
import sys
from datetime import datetime

from browser_use import ActionResult, Agent, BrowserSession, Controller
from browser_use.llm import ChatGoogle
from dotenv import load_dotenv

from prompting import get_initial_actions, get_tasks
from session import create_fresh_browser_session

load_dotenv()


LOGS_PATH = "logs"

# browser-use already creates its own uid for logs but we need a way to organize
# multiple sets of logs in the same run
run_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
task1_logs_path = os.path.join(LOGS_PATH, run_id, "task1")
task2_logs_path = os.path.join(LOGS_PATH, run_id, "task2")
task3_logs_path = os.path.join(LOGS_PATH, run_id, "task3")
task4_logs_path = os.path.join(LOGS_PATH, run_id, "task4")

flight_info = {
    "departure_code": "SNA",
    "arrival_code": "SFO",
    "departure_date": "2025-09-01",
    "return_date": None,
    "adult_passengers": 1,
    "round_trip": False,
    "cabin_class": "Economy",
    "routing": "direct",
}

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
billing_info = {
    "type": "Credit Card",
    "card_number": "1234 5678 9100",
    "expiration_date": "09-2026",
    "cvv": "808",
    "billing_address": "1234 Green Valley Rd, Salt Lake City, UT 71854",
    "phone_number": "+1 881 849 9102",
    "email_address": "kenneth.alex.lin@gmail.com",
}

llm = ChatGoogle(model="gemini-2.0-flash", temperature=0.0)
browser_session = create_fresh_browser_session(window_orientation="top-right")
task1, task2, task3, task4 = get_tasks(
    flight_info=flight_info, user_info_ls=user_info_ls, billing_info=billing_info
)

print(task1)
print(task2)
print(task3)
print(task4)

controller = Controller()


@controller.action("Click and clear text in a text input element")
async def clear_text(index: int, browser_session: BrowserSession) -> ActionResult:
    element_node = await browser_session.get_dom_element_by_index(index)
    element_handle = await browser_session.get_locate_element(element_node)

    await element_handle.evaluate('el => {el.textContent = ""; el.value = "";}')
    await element_handle.click()

    page = await browser_session.get_current_page()
    await page.keyboard.press("Meta+A" if sys.platform == "darwin" else "Control+A")
    await page.keyboard.press("Backspace")
    return ActionResult(extracted_content=f"Cleared text in text input element {index}")


@controller.action(
    "Request user assistance completing the current task. Use the request_msg parameter to describe what you need assistance with. The user will take over control of the browser and return control to you it when your request has been completed."
)
async def request_assistance(request_msg: str) -> ActionResult:
    val = await input(
        f"""
        🫵 User assistance has been requested. 
           Here's the agent's request: {request_msg} 
           Type DONE when you would like to return control to the Agent: """
    )
    if val != "DONE":
        raise ValueError(f"Expected value 'DONE' but received {val} instead.")
    return ActionResult(
        extracted_content=f'The user has provided assistance. The page may have changed from the last time it has been seen. Here is what the user was asked to do: "{request_msg}"'
    )


extended_system_message = """
<critical_rules>
You will be interacting with very dense, dynamic pages. Be conservative when using any actions that will alter your view of the page.

Below is a list of CRITICAL rules that must always be followed. Failure to adhere to them will lead to unstable page interactions that may make accomplishing your goal impossible.
1. Whenever you use the scroll action, you must only scroll in half-page increments (num_pages = 0.5). Scrolling a full page or more can accidentally obscure content.
2. NEVER use the input_text action when the text input element is not visible or is only partly visible in the browser window. Always use the provided screenshot of the page in order to confirm that the target element is fully visible before using input_text. If it is obscured, take necessary actions to reveal it such as scrolling the page or expanding accordion widgets.
3. If you are prompted to accept cookies, you must do this before taking any other task. This pop-up may obscure other critical page elements.
</critical_rules>
"""


async def main():
    # initialize browser
    await browser_session.start()

    # step 1
    agent = Agent(
        controller=controller,
        task=task1,
        llm=llm,
        initial_actions=get_initial_actions(site="southwest"),
        browser_session=browser_session,
        save_conversation_path=task1_logs_path,
        use_vision=True,
    )
    result = await agent.run()

    # testing_url = "https://www.southwest.com/air/booking/select-depart.html?adultsCount=1&adultPassengersCount=1&destinationAirportCode=SFO&departureDate=2025-09-01&departureTimeOfDay=ALL_DAY&fareType=USD&int=HOMEQBOMAIR&originationAirportCode=SNA&passengerType=ADULT&promoCode=&returnDate=&returnTimeOfDay=ALL_DAY&tripType=oneway"
    # step 2
    agent = Agent(
        controller=controller,
        task=task2,
        llm=llm,
        browser_session=browser_session,
        save_conversation_path=task2_logs_path,
        use_vision=True,
        extend_system_message=extended_system_message,
        # initial_actions=get_initial_actions(site=testing_url),
    )
    result = await agent.run()

    # step 3
    agent = Agent(
        controller=controller,
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
        controller=controller,
        task=task4,
        llm=llm,
        browser_session=browser_session,
        save_conversation_path=task4_logs_path,
        use_vision=True,
        extend_system_message=extended_system_message,
    )
    result = await agent.run()


if __name__ == "__main__":
    asyncio.run(main())

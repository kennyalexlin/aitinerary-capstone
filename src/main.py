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

intent = {
    "from": "SNA",
    "to": "SFO",
    "departure_date": "August 12th, 2025",
    "return_date": "August 19th, 2025",
    # "flight_type": "round-trip",
    "flight_type": "one-way",
    "passengers": [
        {
            "first_name": "Kenneth",
            "middle_name": None,
            "last_name": "Lin",
            "dob": "September 15, 1999",
            "gender": "male",
            "email": "kenneth.alex.lin@gmail.com",
            "phone_number": "+1 626 375 6087",
            "emergency_contact": "do not add an emergency contact",
        }
    ],
    "num_passengers": 1,
}

primary_llm = ChatGoogle(model="gemini-2.0-flash", temperature=0.0)
planner_llm = ChatGoogle(model="gemini-2.0-flash", temperature=0.0)
browser_session = create_fresh_browser_session(window_orientation="top-right")
task1, task2, task3 = get_tasks(intent=intent)
initial_actions = get_initial_actions(site="united")

controller = Controller()


@controller.action("Click and clear text in a selected text input element")
async def clear_text(index: int, browser_session: BrowserSession) -> ActionResult:
    """Defines a new action for the Agent that enables it to clear an input element
    without needing to hit backspace multiple times

    This additionally solves the problem of the agent clicking into the middle of a text element,
    which was happening frequently on the United site.
    """
    element_node = await browser_session.get_dom_element_by_index(index)
    element_handle = await browser_session.get_locate_element(element_node)

    await element_handle.evaluate('el => {el.textContent = ""; el.value = "";}')
    await element_handle.click()

    page = await browser_session.get_current_page()
    await page.keyboard.press("Meta+A" if sys.platform == "darwin" else "Control+A")
    await page.keyboard.press("Backspace")
    return ActionResult(extracted_content=f"Cleared text in text input element {index}")


# extended_planner_system_message = """
# If any of your next steps involve populating a text input interactive element, you must include a step before it to delete any pre-populated text by selecting the input element, sending the keys Meta+A, and then sending the Backspace key.

# In addition, if any of your next steps involve submitting a form, you must include a step before it to double-check that all fields have been populated correctly. Do not assume that all prior steps have accomplished their tasks successfully.
# """


async def main():
    # initialize browser
    await browser_session.start()

    # step 1
    agent = Agent(
        controller=controller,
        task=task1,
        llm=primary_llm,
        planner_llm=planner_llm,
        max_actions_per_step=30,
        initial_actions=initial_actions,
        # message_context isn't being used at all so no point in passing that arg in
        # message_context=,
        browser_session=browser_session,
        save_conversation_path=task1_logs_path,
        use_vision=True,
    )
    result = await agent.run()

    # step 2
    agent = Agent(
        controller=controller,
        task=task2,
        llm=primary_llm,
        planner_llm=planner_llm,
        browser_session=browser_session,
        save_conversation_path=task2_logs_path,
        use_vision=True,
    )
    result = await agent.run()

    # step 3
    agent = Agent(
        controller=controller,
        task=task3,
        llm=primary_llm,
        planner_llm=planner_llm,
        browser_session=browser_session,
        save_conversation_path=task3_logs_path,
        use_vision=True,
    )
    result = await agent.run()


if __name__ == "__main__":
    asyncio.run(main())

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

controller = Controller()


@controller.action("Click and clear text in a selected text input element")
async def clear_text(index: int, browser_session: BrowserSession) -> ActionResult:
    element_node = await browser_session.get_dom_element_by_index(index)
    element_handle = await browser_session.get_locate_element(element_node)

    await element_handle.evaluate('el => {el.textContent = ""; el.value = "";}')
    await element_handle.click()

    page = await browser_session.get_current_page()
    await page.keyboard.press("Meta+A" if sys.platform == "darwin" else "Control+A")
    await page.keyboard.press("Backspace")
    return ActionResult(extracted_content=f"Cleared text in text input element {index}")


# failed attempt at getting the browser to zoom out to show more elements.
# Chromium disables zooming out via hot-key :(
# @controller.action("Zoom the page out")
# async def zoom_out(browser_session: BrowserSession) -> ActionResult:
#     page = await browser_session.get_current_page()
#     session = await browser_session.browser_context.new_cdp_session(page)
#     await session.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 0.5})
#     await page.reload()
#     return ActionResult(extracted_content="Zoomed out to 75% scale.")


# testing_url = "https://www.united.com/en/us/fsr/choose-flights?f=SNA&t=SFO&d=2025-08-12&tt=1&sc=7&px=1&taxng=1&newHP=True&clm=7&st=bestmatches&tqp=R"

extended_system_message = """
<critical_rules>
You will be interacting with very dense, dynamic pages. Be conservative when using any actions that will alter your view of the page.

The following are CRITICAL rules that must always be followed:
1. Whenever you use the "scroll" action, you must only scroll in half-page increments (num_pages = 0.25). Scrolling a full page or more will lead to unstable results.
2. If you are prompted to accept cookies, you must do this before taking any other task. This pop-up may obscure other critical page elements.
</critical_rules>
"""


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
        initial_actions=get_initial_actions(site="united"),
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
        extend_system_message=extended_system_message,
        # initial_actions=get_initial_actions(site=testing_url),
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
        extend_system_message=extended_system_message,
        initial_actions=get_initial_actions(),
    )
    result = await agent.run()


if __name__ == "__main__":
    asyncio.run(main())

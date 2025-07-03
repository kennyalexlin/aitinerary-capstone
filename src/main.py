import asyncio

from browser_use import Agent, BrowserSession
from browser_use.llm import ChatGoogle
from dotenv import load_dotenv

from prompting import get_user_task

load_dotenv()

LOGS_PATH = "logs/conversation"

primary_llm = ChatGoogle(model="gemini-2.0-flash", temperature=0.0)
planner_llm = ChatGoogle(model="gemini-2.0-flash", temperature=0.0)
browser_session = BrowserSession(headless=False, keep_alive=True)

task = get_user_task()


async def main():
    await browser_session.start()
    agent = Agent(
        task=task,
        llm=primary_llm,
        # using a planner LLM significantly improved performance of the model.
        # it made fewer mistakes and solved the problem in fewer steps (16 instead of 24)
        planner_llm=planner_llm,
        browser_session=browser_session,
        save_conversation_path=LOGS_PATH,
    )
    result = await agent.run()
    print(result)


if __name__ == "__main__":
    asyncio.run(main())

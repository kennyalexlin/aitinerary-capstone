import asyncio
import os
from datetime import datetime

from browser_use import Agent
from browser_use.llm import ChatGoogle
from tqdm import tqdm

from agent.session import create_fresh_browser_session

run_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
logs_path = "logs_test"
run_logs_path = os.path.join(logs_path, run_id)
task1_logs_path = os.path.join(run_logs_path, "task1")
task1_gif_path = os.path.join(run_logs_path, "task1.gif")

model = "gemini-2.0-flash"
# model = "gpt-4.1-mini"
llm = ChatGoogle(model=model, temperature=0.0)


async def run_agent():
    browser_session = create_fresh_browser_session(keep_alive=False)
    await browser_session.start()

    agent = Agent(
        llm=llm,
        browser_session=browser_session,
        save_conversation_path=task1_logs_path,
        use_vision=True,
        max_actions_per_step=2,
        generate_gif=task1_gif_path,
        task="Go to Google. Look up images of dogs. Once you've searched for dogs, you're done.",
    )
    await agent.run()


async def run_sequentially(num_runs: 3):
    for i in tqdm(range(num_runs)):
        await run_agent()


async def main():
    await run_sequentially(num_runs=3)


if __name__ == "__main__":
    asyncio.run(main())

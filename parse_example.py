import asyncio
import json
from datetime import datetime
import sys
import os
import platform

# Set up browser-use config directory before importing
config_dir = os.path.expanduser('~/Desktop/aitinerary/browser_config')
os.makedirs(config_dir, exist_ok=True)
os.environ['BROWSER_USE_CONFIG_DIR'] = config_dir

# Now safely import browser-use
try:
    from browser_use import Agent, BrowserSession
    print("Successfully imported browser-use")
except Exception as e:
    print(f"Still having import issues: {e}")
    sys.exit(1)

from dotenv import load_dotenv
from browser_use.llm import ChatAnthropic
from pydantic import BaseModel


load_dotenv()


llm = ChatAnthropic(model="claude-3-5-sonnet-20240620",)


async def main():
    website = 'https://www.delta.com/completepurchase/review-pay?cacheKeySuffix=adb13fc9-83eb-46ef-b3ed-a89724d1d221&cartId=38ee8275-a4c5-44ab-98b1-e65eb32a44d2'
    agent = Agent(
        task = f"Scan this site and give me a list of all the field names in the forms a user needs to fill out: {website}",
        llm = llm 
    )
    result = await agent.run()
    print(result.extracted_content())

asyncio.run(main())
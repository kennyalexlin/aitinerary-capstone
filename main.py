import asyncio

from browser_use import Agent, BrowserSession
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()

llm = ChatAnthropic(
    model_name="claude-3-5-sonnet-20240620", temperature=0.0, timeout=30
)
print("Created LLM client")
browser_session = BrowserSession(headless=False, keep_alive=True)

task = """
Navigate to this link: {link}
Select the first flight that you see with the lowest price and go through the booking process as a Guest.
Agree or consent to any terms and conditions that you see.
Once you've filled in my basic information below, stop. Do not click any buttons to submit my information or finalize the booking.

Basic Personal Information:
- First Name: Kenneth
- Last Name: Lin
- Middle Name: Alexander
- Gender: Male
- Phone Number: (626) 375 - 6087
- Address: 2850 Kelvin Ave Apt 123, Irvine, CA 92614
- Email: kenneth.alex.lin@gmail.com
"""

task = task.format(link='https://flyasiana.com/I/US/EN/RevenueInternationalFareDrivenFlightsSelect.do?is_mobile=N&site_code=US&lang_code=EN&domIntType=I&tripType=OW&departureAirport=LAX&arrivalAirport=NRT&departureDate=20250628&cabinClass=R&adultCount=1&childCount=0&infantCount=0&sessionUniqueKey=kpey7vHwhJMpS8_ODFwbbA&ServiceType=REV&deeplink_id=Kayak&trcode=0000027&kayakclickid=kpey7vHwhJMpS8_ODFwbbA')

async def main():
    await browser_session.start()
    agent = Agent(
        task=task,
        llm=llm,
        browser_session=browser_session,
    )
    result = await agent.run()
    print(result)


if __name__ == "__main__":
    print("Start!!!")
    asyncio.run(main())

import asyncio
import json
from datetime import datetime
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import platform
import re

# Set up browser-use config directory before importing
config_dir = os.path.expanduser('~/Desktop/aitinerary/browser_config')
os.makedirs(config_dir, exist_ok=True)
os.environ['BROWSER_USE_CONFIG_DIR'] = config_dir

# Now safely import browser-use
try:
    from browser_use import Agent, BrowserSession, Controller, ActionResult
    print("Successfully imported browser-use")
except Exception as e:
    print(f"Still having import issues: {e}")
    sys.exit(1)

from dotenv import load_dotenv
from browser_use.llm import ChatAnthropic
from pydantic import BaseModel
BrowserSession.capture_element_screenshots = False
from browser_use.llm import ChatGoogle

load_dotenv()
BrowserSession.clear_context_on_start = True

llm = ChatGoogle(model="gemini-2.5-flash-lite-preview-06-17")

message_context = """
When URL contains '/traveler/choose-travelers' (or any of the specified segments), do NOT click, go back, or perform any further actions. Immediately output:
{"action":"done","text": "<current_url>","success": true}

# Step 1: Filter interactive DOM
In the traveler info page / traveler booking page, invoke filter_interactive_fields() to extract all typable/selectable fields.
- Call the action `filter_interactive_fields()`. This action returns `interactive_fields`, each with tag, type, name/id, xpath, position, and visibility.
- Include visible inputs (textual types), textareas, selects, and contenteditable areas
- Exclude hidden/disabled fields
- For each element, capture tag, type, name/id, xpath, bounding box, and visibility
- For elements that can be expanded (e.g. a list of choices), expand the elements and include the items within those elements
- Return this list named "interactive_fields" before doing any further task-specific actions

# Step 2: Final output
Once you have the list, format it and call done.
"""

message_pre_agent = """
1. Invoke filter_booking_controls().
2. From the returned list, look for "One-way" or "Round-trip" and click that selector.
3. Then fill origin/destination/date.
4. Click on "Find flights" or "Book now" (something similar).
5. Wait for flight results.
6. Invoke filter_booking_controls() again, locate the first flight's "Select" button, click it.
7. Wait for the traveler info form to appear (check by waiting selector).
8. Once on traveler info, return the URL via done.
"""

task_setup = """
You are booking a one-way flight from JFK to LAX on www.southwest.com. You are currently on flight company homepage.
-- First, clear all existing texts in From and To (or Depart and Arrive) boxes.
-- Type the airport code "JFK" into the origin input field exactly once.
-- After typing, click the autocomplete option, then pause and wait for the field to show JFK.
-- Do NOT add extra key presses or repeat characters.
-- Repeat the same for LAX.
Book a one-way flight on August 1.
Yo will be navigated to a list of flights. Select the first flight and continue with the booking process until you are prompted to provide any traveler info.
Once this occurs, stop proceeding or performing any actions. Return the exact URL of this page; it should contain: southwest.com and one of these path segments (or something similar):
- /booking/passenger
- /checkout/traveler
- /purchase/details
- /book/passenger-info
Once on a URL containing '/traveler/choose-travelers' or '/booking/passenger':
- Immediately stop all browser actions.
- Output the URL and call done with success=true.
- Do not click previous pages or rethink flight selection.
"""

# customer functions for DOM filtering

controller = Controller()

@controller.action("Return flight booking controls")
async def filter_booking_controls() -> ActionResult:
    js = r"""
    const needed = ["one-way", "round-trip", "depart", "return", "find flights", "select", "continue", "next"];
    return Array.from(document.querySelectorAll('button, select, input[type="text"], input[type="date"]'))
      .filter(el => {
        const text = (el.innerText || el.value || el.getAttribute('aria-label') || "").toLowerCase();
        return needed.some(k => text.includes(k));
      })
      .map(el => ({
        tag: el.tagName,
        selector: el.tagName.toLowerCase()
                  + (el.id ? `#${el.id}` : el.name ? `[name="${el.name}"]` : ""),
        text: (el.innerText || el.value || el.getAttribute('aria-label') || "").trim()
      }));
    """
    return ActionResult(js=js)


@controller.action("Return named, focused, and relevant DOM fields")
async def filter_interactive_fields() -> ActionResult:
    js = r"""
    function getName(el) {
      if (el.ariaLabel) return el.ariaLabel;
      const abz = el.getAttribute('aria-labelledby');
      if (abz) return abz.split(' ').map(id => document.getElementById(id)?.innerText).join(' ');
      if (el.labels?.length) return Array.from(el.labels).map(l => l.innerText).join(' ');
      if (el.placeholder) return el.placeholder;
      if (el.title) return el.title;
      return el.innerText?.trim() || null;
    }
    return Array.from(document.querySelectorAll(
      'input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])'
    )).filter(el => {
      const name = getName(el);
      return name && /First name|Last name|Middle|Birth|Gender|Suffix|Frequent flyer/i.test(name);
    }).map(el => {
      const rect = el.getBoundingClientRect();
      return {
        tag: el.tagName,
        type: el.type || null,
        selector: el.tagName.toLowerCase() +
          (el.name ? `[name="${el.name}"]` : el.id ? `#${el.id}` : ''),
        name: getName(el),
        value: el.value || null,
        required: el.required || el.getAttribute('aria-required') === 'true',
        visible: rect.width > 0 && rect.height > 0
      };
    });
    """
    return ActionResult(js=js)



async def main():
    # pre-agent: setup a valid session (e.g., login/search) to get to booking page
    setup_agent = Agent(
        task=task_setup,
        llm=llm,
        initial_actions=[
    {"go_to_url": {"url": "https://www.southwest.com","new_tab": False}}
  ],
        message_context = message_pre_agent,
        use_vision=True
    )
    try:
        setup_result = await setup_agent.run()
    except Exception:
        BrowserSession.capture_element_screenshots = False
        setup_result = await setup_agent.run()

    content = setup_result.extracted_content()
    # if it's a list, pull out the single URL string
    extract = content[0] if isinstance(content, list) else content
    match = re.search(r'https?://\S+', extract)
    if match:
        website = match.group(0)
    else:
        raise ValueError(f"Could not parse URL from setup_agent result: {extract}")
    print("✅ Setup complete, navigating to:", website)

    # main DOM parsing agent: operate on the established page
    main_agent = Agent(
        task="Filter traveler info page DOM and list interactive fields.",
        initial_actions=[
            {"go_to_url": {"url": website, "new_tab": False}}], # page should already be traveler info
        llm=llm,
        controller=controller,
        message_context=message_context,
        use_vision=True
    )
    try:
        main_result = await main_agent.run()
        fields = main_result.extracted_content()
    except UnicodeEncodeError:
        fields = main_result.extracted_content().encode('ascii','ignore').decode('ascii')

    print("🧩 Interactive fields found:", fields)

asyncio.run(main())

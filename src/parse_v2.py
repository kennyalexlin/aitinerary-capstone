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

task_setup = """
You are booking a one-way flight from JFK to LAX on www.united.com. You are currently on flight company homepage.
-- First, clear all existing texts in From and To boxes.
-- Type the airport code "JFK" into the origin input field exactly once.
-- After typing, click the autocomplete option, then pause and wait for the field to show JFK.
-- Do NOT add extra key presses or repeat characters.
-- Repeat the same for LAX.
Book a one-way flight on August 1.
Yo will be navigated to a list of flights. Select the first flight and continue with the booking process until you are prompted to provide any traveler info.
Once this occurs, stop proceeding or performing any actions. Return the exact URL of this page; it should contain: united.com and one of these path segments (or something similar):
- /booking/passenger
- /checkout/traveler
- /purchase/details
- /book/passenger-info
Once on a URL containing '/traveler/choose-travelers' or '/booking/passenger':
- Immediately stop all browser actions.
- Output the URL and call done with success=true.
- Do not click previous pages or rethink flight selection.
"""

# customer function for DOM filtering

controller = Controller()

@controller.action("Return named typable/selectable/focusable DOM fields")
async def filter_interactive_fields() -> ActionResult:
    js = r"""
    function getAccessibleName(el) {
      // Use ariaLabel, aria-labelledby or inner text/placeholder
      if (el.ariaLabel) return el.ariaLabel;
      if (el.getAttribute('aria-labelledby')) {
        const ids = el.getAttribute('aria-labelledby').split(' ');
        return ids.map(id => document.getElementById(id)?.innerText).filter(Boolean).join(' ');
      }
      // Labels associated by <label for>
      if (el.labels?.length) {
        return Array.from(el.labels).map(l => l.innerText).join(' ');
      }
      // Fallback to visible text or placeholder
      if (el.innerText && el.innerText.trim()) return el.innerText.trim();
      if (el.placeholder) return el.placeholder;
      return null;
    }

    return Array.from(document.querySelectorAll(
      'input:not([type=hidden]):not([disabled]), textarea:not([disabled]), select:not([disabled]), [contenteditable="true"]'
    )).filter(el => {
      if (el.tagName === 'INPUT') {
        return ['text','email','search','url','tel','password','number','date',
                'datetime-local','month','time','week']
          .includes(el.type.toLowerCase());
      }
      return true;
    }).map(el => {
      const name = getAccessibleName(el);
      const rect = el.getBoundingClientRect();
      return {
        tag: el.tagName,
        type: el.type || null,
        id: el.id || null,
        name: name,
        xpath: (() => {
          let path = '', node = el;
          while (node && node.nodeType === Node.ELEMENT_NODE) {
            let idx = 1, sib = node.previousElementSibling;
            while (sib) {
              if (sib.tagName === node.tagName) idx++;
              sib = sib.previousElementSibling;
            }
            path = `/${node.tagName}[${idx}]` + path;
            node = node.parentNode;
          }
          return path;
        })(),
        visible: rect.width > 0 && rect.height > 0
      };
    });
    """
    return ActionResult(js=js)


async def main():
    # pre-agent: setup a valid session (e.g., login/search) to get to booking page
    setup_agent = Agent(
        task="Book one-way flight JFK→LAX on Aug 1. Once traveler info form loads, stop and return the URL.",
        llm=llm,
        initial_actions=[
    {"go_to_url": {"url": "https://www.united.com","new_tab": False}}
  ],
        message_context = task_setup,
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

    # 2️⃣ Main agent: operate on the established page
    main_agent = Agent(
        task="Filter traveler info page DOM and list interactive fields.",
        initial_actions=[
            {"go_to_url": {"url": website, "new_tab": False}}],
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

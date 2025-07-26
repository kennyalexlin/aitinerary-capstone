import asyncio
import shutil
from pathlib import Path

from browser_use import Agent, BrowserSession
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def clear_browseruse_cache():
    """Clear browser-use default cache directory"""
    try:
        # Browser-use default profile path
        browseruse_profile = Path.home() / ".config" / "browseruse" / "profiles" / "default"
        
        if browseruse_profile.exists():
            print(f"Clearing browser-use cache at: {browseruse_profile}")
            shutil.rmtree(browseruse_profile)
            print("✓ Browser-use cache cleared successfully")
        else:
            print("✓ No existing browser-use cache found")
            
    except Exception as e:
        print(f"Warning: Could not clear browser-use cache: {e}")

# Create LLM with optimized settings 
# NOTE: I was getting inconsistent results with gpt-4o-mini, so I switched to gpt-4o that was significantly better, we need to optimize this further in the coming weeks
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.1,
    max_tokens=2000,
    timeout=60,
)
print("Created optimized LLM client with GPT-4o-mini")

async def create_fresh_browser_session():
    """Create a completely fresh browser session with aggressive cache clearing"""
    # Clear browser-use's own cache first
    clear_browseruse_cache()
    
    # Configure browser session with maximum freshness
    browser_session = BrowserSession(
        headless=False, 
        keep_alive=False,  # Don't persist between runs
        storage_state=None,  # No stored cookies/localStorage
        browser_config={
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-restore-session-state',
                '--disable-background-networking',
                '--incognito',  # Force private browsing
                '--disable-extensions',
                '--disable-plugins',
                '--disable-sync',
                '--disable-session-crashed-bubble',
                '--disable-infobars',
                '--disable-translate',
                '--disk-cache-size=0',  # No disk cache
                '--media-cache-size=0',  # No media cache
                '--aggressive-cache-discard',
            ]
        }
    )
    
    return browser_session

# Enhanced task with detailed instructions built into the task itself
task = """
### Step 1
- Open [Delta Airlines](https://www.delta.com).
- Close any popups that appear before proceeding.
- Complete Step 1 fully before moving on.

---

### Step 2

1. In the "From" field:  
   - Click the field.
   - Make sure the search says "Origin" 
   - Type ATL and wait until dropdown suggestions appear.  
   - Click the suggestion exactly matching "ATL Atlanta, GA".  
   - The drop down should now disapear, if not click the Atlanda airport from the drop down.
   - Do not proceed until confirmed.

2. In the To field:  
   - Click the field.
   - Make sure the search says "Destination" 
   - Type JFK and wait until dropdown suggestions appear.  
   - Click the suggestion exactly matching "JFK New York-Kennedy, NY".  
   - The drop down should now disapear, if not click the JFK airport from the drop down.
   - Do not proceed until confirmed.

3. Change to one-way trip:
   - Click the trip type button (currently shows "Round Trip")
   - There will be 3 options, "Round Trip", "One Way", and "Multi-City", select the middle option "One Way"
   - Click "One Way" from the dropdown menu
   - The drop down should now disapear.
   - Make sure the trip type clearly shows "One Way" is selected.
   - Only proceed to step 4 if "One Way" is confirmed

4. Set departure date:
   - Click the departure date field
   - Navigate to August 2025 in the calendar
   - Click on selectable day that has the number "11"
   - Now click the "Done" button in the bottom right corner of the calendar
   - VERIFY: Check that the date field shows "Aug 11" or "August 11, 2025" (do not click the field again)
   - Only proceed to step 5 if August 11, 2025 is confirmed

5. Confirm 1 adult passenger (should be default)
   - VERIFY: Check that passenger count shows "1 Adult" (do not change unless it shows something different)

6. Click "Search" or "Find Flights" button

**Important: Complete each step fully before moving to the next step. If any step fails, retry that step before continuing.**

"""

async def main():
    print("Creating completely fresh browser session...")
    browser_session = await create_fresh_browser_session()
    
    try:
        await browser_session.start()
        
        # Create agent with fresh session
        agent = Agent(
            task=task,
            llm=llm,
            browser_session=browser_session,
            use_vision=True,
            max_failures=3,
        )
        
        print("Starting Delta Airlines automation with fresh session...")
        print("- Completely new browser instance")
        print("- Browser-use cache cleared")
        print("- No cached data or cookies")
        print("- Aggressive form clearing instructions")
        
        result = await agent.run()
        print("\n" + "="*50)
        print("AUTOMATION COMPLETE")
        print("="*50)
        print(result)
        
    except Exception as e:
        print(f"Error during automation: {e}")
    finally:
        # Clean up browser session
        try:
            await browser_session.stop()
            print("Browser session stopped")
        except:
            pass

if __name__ == "__main__":
    print("Fresh Delta Airlines Automation")
    print("="*50)
    asyncio.run(main())

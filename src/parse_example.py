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

task_setup = """
ULTRA-SPECIFIC DELTA BOOKING INSTRUCTIONS:

1. NAVIGATE TO HOMEPAGE:
   - Go to https://www.delta.com
   - Wait for page to fully load

2. HANDLE POPUPS (if any appear):
   - Look for modal overlays with close buttons (X, "Close", "No Thanks")
   - Click ONLY buttons with these exact attributes:
     * aria-label="Close" 
     * class containing "close" or "dismiss"
     * text="✕" or "×" or "x" or "X"
   - IGNORE all other buttons like "Accept Cookies", "Sign Up", promotional banners

3. FLIGHT SEARCH - EXACT STEPS: 
   - Find the flight search widget (usually prominent on homepage)
   - Click on "FROM" field, type "JFK" (John F. Kennedy, New York)
   - Click on "TO" field, type "LAX" (Los Angeles International)
   - Click on departure date field, select any date 7-14 days from today
   - For trip type: Keep "Round Trip" selected (default)
   - Click on return date field, select date 2-3 days after departure
   - Click the main search button with text "FIND FLIGHTS" or "SEARCH FLIGHTS"
   - IGNORE: "Advanced Search", "Multi-city", "Flexible Dates" options

4. OUTBOUND FLIGHT SELECTION:
   - At the flight results page, you will see flight cards/rows with "Select" or "Choose" buttons
   - Click "Select" on the FIRST available flight (ignore price comparisons)
   - IGNORE: "Details", "Baggage Info", "Seat Selection" links
   - You should see "Outbound Selected" or similar confirmation

5. RETURN FLIGHT SELECTION:
   - Page will show return flight options
   - Click "Select" on the FIRST available return flight
   - IGNORE: Upgrade offers, seat selection prompts
   - Look for "Continue" or "Proceed to Checkout" button and click it

6. FLIGHT SUMMARY/REVIEW PAGE:
   - You'll see a summary with selected flights
   - Look for button with text "CONTINUE" or "PROCEED TO PASSENGER DETAILS" or "Continue to Payment", etc.
   - IGNORE: "Add Hotel", "Add Car", "Seat Selection", "Upgrade" options
   - Click ONLY the main continue button

7. PASSENGER DETAILS PAGE - STOP HERE:
   - You should now see forms for passenger information
   - Page title should contain "Passenger" or "Traveler Details"
   - URL should contain "passenger", "traveler", or "booking", etc.
   - DO NOT fill any forms - just confirm you can see input fields
   - Return the exact current URL

CRITICAL DOM FILTERING RULES:
- ONLY click buttons that advance the booking process
- IGNORE all promotional content, ads, cross-sells
- IGNORE social media buttons, newsletter signups
- IGNORE "Save trip", "Price alerts", "Fare calendar" features
- IGNORE any popup asking for personal info, app downloads
- Focus ONLY on primary booking flow buttons with these patterns:
  * "Select Flight", "Continue", "Proceed", "Next"
  * Main CTA buttons (usually blue/prominent)
  * Buttons inside the booking widget/flow area

EXPECTED FINAL URL PATTERN:
Should contain: delta.com and one of these path segments (or something similar):
- /booking/passenger
- /checkout/traveler
- /purchase/details
- /book/passenger-info
"""

async def setup_valid_session():
    # this is the pre-agent to establish a session first
    setup_agent = Agent(
    task = task_setup,
    llm = llm
    )
    valid_url = await setup_agent.run()
    return valid_url.extracted_content()

async def main():
    website = await setup_valid_session()
    agent = Agent(
        task = f"""
Navigate to {website}

### Step 1: DOM FILTERING - INCLUDE ONLY THESE FORM ELEMENTS

**PASSENGER INFO SECTION:**
- Input fields with these exact patterns:
  * name="firstName" or contains "first-name", "given-name"
  * name="lastName" or contains "last-name", "surname", "family-name"
  * name="middleName" or contains "middle-name", "middle-initial"
  * name="dateOfBirth" or contains "birth-date", "dob"
  * name="gender" or contains "gender", "sex"
  * name="phone" or contains "phone", "mobile", "telephone"
  * name="email" or contains "email", "e-mail"
  * name="knownTravelerNumber" or contains "ktn", "precheck", "tsa"
  * name="redressNumber" or contains "redress"

**BAGGAGE SECTION:**
- Elements with these patterns:
  * Buttons/dropdowns containing "baggage", "bag", "carry-on", "checked"
  * Text like "Add Bags", "Bag Selection", "Baggage Allowance"
  * Price displays for baggage options

**TRIP PROTECTION SECTION:**
- Elements containing:
  * "Trip Protection", "Travel Insurance", "Cancel for Any Reason"
  * Checkboxes or radio buttons for insurance options
  * Price displays for protection plans

**PAYMENT SECTION:**
- Input fields with these patterns:
  * name="cardNumber" or contains "card-number", "credit-card"
  * name="expiryDate" or contains "expiry", "exp-date", "mm-yy"
  * name="cvv" or contains "cvv", "cvc", "security-code"
  * name="cardholderName" or contains "cardholder", "name-on-card"
  * name="billingAddress" or contains "billing", "address"
  * name="zipCode" or contains "zip", "postal-code"

**TERMS AND PURCHASE:**
- Checkbox elements containing "terms", "conditions", "agree"
- Button elements with text "Complete Purchase", "Book Now", "Pay Now"

**FLIGHT SUMMARY (Reference Only):**
- Elements showing selected flights (for context, not interaction)
- Price breakdowns and totals

### Step 2: IGNORE THESE ELEMENTS
- Navigation menus, headers, footers
- Promotional banners, ads, cross-sells
- Social media buttons, newsletter signups
- "Save trip", "Share", "Print" buttons
- App download prompts
- Customer service chat widgets
- Any popup overlays not related to booking

### Step 3: RETURN STRUCTURED DATA
Return a dictionary with this json structure:
  "passenger_info_fields": 
    "first_name": "DOM_INDEX_or_SELECTOR",
    "last_name": "DOM_INDEX_or_SELECTOR",
    "date_of_birth": "DOM_INDEX_or_SELECTOR",
    "email": "DOM_INDEX_or_SELECTOR",
    "phone": "DOM_INDEX_or_SELECTOR"
  ,
  "baggage_options": 
    "carry_on_selection": "DOM_INDEX_or_SELECTOR",
    "checked_bag_selection": "DOM_INDEX_or_SELECTOR"
  ,
  "trip_protection": 
    "insurance_checkbox": "DOM_INDEX_or_SELECTOR",
    "protection_options": "DOM_INDEX_or_SELECTOR"
  ,
  "payment_fields": 
    "card_number": "DOM_INDEX_or_SELECTOR",
    "expiry_date": "DOM_INDEX_or_SELECTOR",
    "cvv": "DOM_INDEX_or_SELECTOR",
    "billing_address": "DOM_INDEX_or_SELECTOR"
  ,
  "terms_and_purchase": 
    "terms_checkbox": "DOM_INDEX_or_SELECTOR",
    "purchase_button": "DOM_INDEX_or_SELECTOR"
    
  CRITICAL: Only index elements that users must interact with to complete the booking. Ignore all decorative, promotional, or non-essential elements.
"""
    ,
    llm = llm 
    )
    result = await agent.run()
    print(result.extracted_content())

asyncio.run(main())
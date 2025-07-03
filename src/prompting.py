def get_user_task() -> str:
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
    return task

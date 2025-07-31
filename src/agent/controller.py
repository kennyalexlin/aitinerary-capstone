import sys

from browser_use import ActionResult, BrowserSession, Controller

custom_controller = Controller(exclude_actions=['filter_booking_controls, filter_interactive_fields','filter_booking_indices', 'filter_flight_selector_indices','filter_interactive_indices'])

@custom_controller.action("Click and clear text in a text input element")
async def clear_text(index: int, browser_session: BrowserSession) -> ActionResult:
    element_node = await browser_session.get_dom_element_by_index(index)
    element_handle = await browser_session.get_locate_element(element_node)

    await element_handle.evaluate('el => {el.textContent = ""; el.value = "";}')
    await element_handle.click()

    page = await browser_session.get_current_page()
    await page.keyboard.press("Meta+A" if sys.platform == "darwin" else "Control+A")
    await page.keyboard.press("Backspace")
    return ActionResult(extracted_content=f"Cleared text in text input element {index}")


@custom_controller.action(
    "Request user assistance completing the current task. Use the request_msg parameter to describe what you need assistance with. The user will take over control of the browser and return control to you it when your request has been completed."
)
async def request_assistance(request_msg: str) -> ActionResult:
    val = await input(
        f"""
        🫵 User assistance has been requested. 
           Here's the agent's request: {request_msg} 
           Type DONE when you would like to return control to the Agent: """
    )
    if val != "DONE":
        raise ValueError(f"Expected value 'DONE' but received {val} instead.")
    return ActionResult(
        extracted_content=f'The user has provided assistance. The page may have changed from the last time it has been seen. Here is what the user was asked to do: "{request_msg}"'
    )

# DOM parsing functions

@custom_controller.action("Filter for DOM elements that are only about booking the trip, such as filling in dates, airport codes, roundtrip/one-way, etc, as well as action buttons to proceed to subsequent pages.")
async def filter_booking_controls() -> ActionResult:
    js = r"""
    const keywords = [
      "round-trip", "one-way", "depart", "return", "from", "to", 
      "search flights", "find flights", "continue", "next", 
      "passenger", "date", "airport", "select", "book"
    ];

    const elements = Array.from(
      document.querySelectorAll('form, [role="form"], div')
    ).filter(el => {
      const text = el.innerText?.toLowerCase() || "";
      return keywords.some(k => text.includes(k));
    });

    const bookingRoot = elements[0] || document.body;

    const controls = Array.from(
      bookingRoot.querySelectorAll('button, select, input:not([type="hidden"])')
    ).filter(el => {
      const label = (el.innerText || el.value || el.placeholder || el.getAttribute("aria-label") || "").toLowerCase();
      return keywords.some(k => label.includes(k));
    });

    return controls.map(el => {
      const rect = el.getBoundingClientRect();
      return {
        tag: el.tagName,
        type: el.type || null,
        selector: el.tagName.toLowerCase()
          + (el.id ? `#${el.id}` : el.name ? `[name="${el.name}"]` : ""),
        text: (el.innerText || el.value || el.placeholder || el.getAttribute("aria-label") || "").trim(),
        visible: rect.width > 0 && rect.height > 0,
        boundingBox: { top: rect.top, left: rect.left, width: rect.width, height: rect.height }
      };
    });
    """
    return ActionResult(js=js)

@custom_controller.action("Filter for DOM elements that are only user-interaction fields, such as typable, focusable, selectable/dropdowns.")
async def filter_interactive_fields() -> ActionResult:
    js = r"""
    const needed = ["one-way","round-trip","depart","return","find flights","select","continue","next"];
    const els = Array.from(document.querySelectorAll("button, a, div, span"));
    const controls = [];
    els.forEach(el => {
      const text = (el.innerText||el.getAttribute("aria-label")||"").trim();
      const lower = text.toLowerCase();
      if (needed.some(k => lower.includes(k)) || /\$\s*\d+/.test(text)) {
        controls.push({
          tag: el.tagName,
          text: text,
          price: (/\$\s*\d+/.exec(text) || [null])[0],
          selector: el.id
            ? `#${el.id}`
            : el.getAttribute("data-testid")
              ? `${el.tagName.toLowerCase()}[data-testid="${el.getAttribute("data-testid")}"]`
              : el.className
                ? `${el.tagName.toLowerCase()}.${el.className.split(" ").join(".")}`
                : el.tagName.toLowerCase()
        });
      }
    });
    // popup controls
    const popups = Array.from(document.querySelectorAll("button, a")).filter(el => {
      const t = (el.innerText||"").toLowerCase();
      return ["continue","confirm","close","cancel","done"].some(w => t.includes(w));
    }).map(el => ({
      tag: el.tagName,
      text: el.innerText?.trim() || el.getAttribute("aria-label"),
      selector: el.id ? `#${el.id}` : null
    }));
    return {controls, popup_controls: popups};
    """
    return ActionResult(js=js)

@custom_controller.action("Filter for stored indexes in the DOM tree that are only about booking the trip, such as filling in dates, airport codes, roundtrip/one-way, etc, as well as action buttons to proceed to subsequent pages.")
async def filter_booking_indices() -> ActionResult:
    js = r"""
    const keywords = [
      "round‑trip","one‑way","depart","return","from","to","search flights",
      "find flights","continue","next","passenger","date","airport","select","book"
    ];

    const tree = await buildDomTree();
    const nodes = tree.nodes || [];

    // narrow to visible and in booking form
    const matches = nodes.filter(n => {
      const text = (n.innerText || n.value || n.ariaLabel || "").toLowerCase();
      return n.visible && keywords.some(k => text.includes(k));
    });

    return matches.map(n => ({
      index: n.index,
      tag: n.tag,
      type: n.type || null,
      text: (n.innerText || n.value || n.ariaLabel || "").trim(),
      visible: true
    }));
    """
    return ActionResult(js=js)

@custom_controller.action("Filter for stored indexes in the DOM tree that are only about selecting the appropriate flight, with the appropriate priced selection and navigating through any potential popups.")
async def filter_flight_selector_indices() -> ActionResult:
    js = r"""
    const tree = await buildDomTree();
    const nodes = tree.nodes || [];

    const matches = nodes.filter(n => {
      if (!n.visible) return false;
      const txt = (n.innerText || n.value || n.ariaLabel || "").toLowerCase();
      return (/\$\d+/.test(txt) && txt.length < 20) // price buttons
        || /(confirm|continue|agree|close|x)/.test(txt) // pop-up controls
        || /(basic|anytime|business|plus)/.test(txt); // fare type selectors
    });

    return matches.map(n => ({
      index: n.index,
      tag: n.tag,
      type: n.type || null,
      text: (n.innerText || n.value || n.ariaLabel || "").trim(),
      visible: n.visible
    }));
    """
    return ActionResult(js=js)

@custom_controller.action("Filter for stored indexes in the DOM tree that are only user-interaction fields, such as typable, focusable, selectable/dropdowns.")
async def filter_interactive_indices() -> ActionResult:
    js = r"""
    const isInput = el => ["INPUT","SELECT","TEXTAREA"].includes(el.tag);
    const tree = await buildDomTree();
    function getName(n) {
      if (n.ariaLabel) return n.ariaLabel;
      if (n.labels?.length) return n.labels.join(" ");
      if (n.placeholder) return n.placeholder;
      if (n.title) return n.title;
      return n.innerText?.trim()||"";
    }
    return tree.nodes
      .filter(n => isInput(n) && !n.disabled)
      .filter(n => {
        const name=getName(n);
        return /First name|Last name|Middle|Birth|Gender|Suffix|Frequent flyer/i.test(name);
      })
      .map(n=>({
        index: n.index,
        tag: n.tag,
        type: n.type||null,
        name: getName(n),
        value: n.value||null,
        required: n.required,
        visible: n.visible,
      }));
    """
    return ActionResult(js=js)
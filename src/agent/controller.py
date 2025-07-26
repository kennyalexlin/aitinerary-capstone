import sys

from browser_use import ActionResult, BrowserSession, Controller


def create_custom_controller(allow_request_assistance: bool = False) -> Controller:
    custom_controller = Controller()

    @custom_controller.action("Click and clear text in a text input element")
    async def clear_text(index: int, browser_session: BrowserSession) -> ActionResult:
        element_node = await browser_session.get_dom_element_by_index(index)
        element_handle = await browser_session.get_locate_element(element_node)

        await element_handle.evaluate('el => {el.textContent = ""; el.value = "";}')
        await element_handle.click()

        page = await browser_session.get_current_page()
        await page.keyboard.press("Meta+A" if sys.platform == "darwin" else "Control+A")
        await page.keyboard.press("Backspace")
        return ActionResult(
            extracted_content=f"Cleared text in text input element {index}"
        )

    if allow_request_assistance:

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

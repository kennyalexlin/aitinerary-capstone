from browser_use import ActionResult, Controller

controller = Controller()


# @controller.action(
#     "Ask human for help with a question"
# )  # pass allowed_domains= or page_filter= to limit actions to certain pages
# def ask_human(question: str) -> ActionResult:
#     answer = input(f"{question} > ")
#     return ActionResult(
#         extracted_content=f"The human responded with: {answer}", include_in_memory=True
#     )


@self.registry.action(
    'Click and input text into a input interactive element',
    param_model=InputTextAction,
)
async def input_text(params: InputTextAction, browser_session: BrowserSession, has_sensitive_data: bool = False):
    if params.index not in await browser_session.get_selector_map():
        raise Exception(f'Element index {params.index} does not exist - retry or use alternative actions')

    element_node = await browser_session.get_dom_element_by_index(params.index)
    assert element_node is not None, f'Element with index {params.index} does not exist'
    try:
        await browser_session._input_text_element_node(element_node, params.text)
    except Exception:
        msg = f'Failed to input text into element {params.index}.'
        return ActionResult(error=msg)

    if not has_sensitive_data:
        msg = f'⌨️  Input {params.text} into index {params.index}'
    else:
        msg = f'⌨️  Input sensitive data into index {params.index}'
    logger.info(msg)
    logger.debug(f'Element xpath: {element_node.xpath}')
    return ActionResult(
        extracted_content=msg,
        include_in_memory=True,
        long_term_memory=f"Input '{params.text}' into element {params.index}.",
    )
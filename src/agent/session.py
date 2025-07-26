import logging
import shutil
from pathlib import Path

import screeninfo
from browser_use import BrowserSession

DEFAULT_WINDOW_WIDTH = 1440
DEFAULT_WINDOW_HEIGHT = 900


def clear_browseruse_cache():
    """Clear browser-use default cache directory"""
    try:
        # Browser-use default profile path
        browseruse_profile = (
            Path.home() / ".config" / "browseruse" / "profiles" / "default"
        )

        if browseruse_profile.exists():
            print(f"Clearing browser-use cache at: {browseruse_profile}")
            shutil.rmtree(browseruse_profile)
            print("✓ Browser-use cache cleared successfully")
        else:
            print("✓ No existing browser-use cache found")

    except Exception as e:
        print(f"Warning: Could not clear browser-use cache: {e}")


def get_screen_dimensions():
    """Gets your monitor's dimensions"""
    monitors = screeninfo.get_monitors()
    primary_monitor = monitors[0]
    return primary_monitor.width, primary_monitor.height


def create_fresh_browser_session(keep_alive=True):
    """Create a completely fresh browser session with aggressive cache clearing"""
    # Clear browser-use's own cache first
    clear_browseruse_cache()

    window_size = {"width": DEFAULT_WINDOW_WIDTH, "height": DEFAULT_WINDOW_HEIGHT}
    screen_width, screen_height = get_screen_dimensions()
    if screen_width < window_size["width"] or screen_height < window_size["height"]:
        logging.warning(
            f"Screen dimensions of {screen_width}px by {screen_height}px are insufficient to support the default window size of {window_size['width']}px by {window_size['heigth']}px. So, window_size will be set to fill your screen instead."
        )
        window_size = None

    # Configure browser session with maximum freshness
    browser_session = BrowserSession(
        headless=False,
        viewport_expansion=0,  # websites have anti-automation blockers
        keep_alive=keep_alive,  # Don't persist between runs
        minimum_wait_page_load_time=0.5,
        storage_state=None,  # No stored cookies/localStorage
        window_size=window_size,
    )

    return browser_session

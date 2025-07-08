import shutil
from pathlib import Path

import screeninfo
from browser_use import BrowserSession
import logging


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


def create_fresh_browser_session(
    window_width: int = 1920,
    window_height: int = 1080,
    window_orientation: str = "top-right",
):
    """Create a completely fresh browser session with aggressive cache clearing"""
    # Clear browser-use's own cache first
    clear_browseruse_cache()

    # by default, browser-use opens the playwright window in the top left-hand corner
    position_width = 0
    position_height = 0

    if window_orientation == 'top-left':
        pass
    elif window_orientation == "top-right":
        screen_width, screen_height = get_screen_dimensions()
        position_width = screen_width - window_width
        position_height = 0
    else:
        logging.warning(f"window_orientation {window_orientation} is not supported. Valid values are 'top-left' or 'top-right'")

    # Configure browser session with maximum freshness
    browser_session = BrowserSession(
        headless=False,
        keep_alive=True,  # Don't persist between runs
        window_size={"width": 1920, "height": 1080},
        window_position={"width": position_width, "height": position_height},
        minimum_wait_page_load_time=0.5,
        storage_state=None,  # No stored cookies/localStorage
        browser_config={
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-restore-session-state",
                "--disable-background-networking",
                "--incognito",  # Force private browsing
                "--disable-extensions",
                "--disable-plugins",
                "--disable-sync",
                "--disable-session-crashed-bubble",
                "--disable-infobars",
                "--disable-translate",
                "--disk-cache-size=0",  # No disk cache
                "--media-cache-size=0",  # No media cache
                "--aggressive-cache-discard",
            ]
        },
    )

    return browser_session

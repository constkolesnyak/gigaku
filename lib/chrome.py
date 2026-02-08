"""Chrome bookmarks reading, window open/close/fullscreen."""

import json

from lib import applescript
from lib.applescript import AppleScriptError
from lib.config import CHROME_BOOKMARKS_PATH, CI_FOLDER_NAME
from lib.display import DisplayInfo


class BookmarkError(Exception):
    """Raised when CI bookmarks are missing or misconfigured."""


def get_ci_bookmark_url() -> str:
    """Read the single CI bookmark URL from Chrome bookmarks.

    Raises BookmarkError if the CI folder is missing, empty, or has != 1 bookmark.
    """
    with open(CHROME_BOOKMARKS_PATH, encoding="utf-8") as f:
        bookmarks = json.load(f)

    def find_ci_folder(node: dict) -> list[str] | None:
        if node.get("type") == "folder" and node.get("name") == CI_FOLDER_NAME:
            return [
                child["url"]
                for child in node.get("children", [])
                if child.get("type") == "url"
            ]
        for child in node.get("children", []):
            result = find_ci_folder(child)
            if result is not None:
                return result
        return None

    for root_node in bookmarks.get("roots", {}).values():
        if isinstance(root_node, dict):
            result = find_ci_folder(root_node)
            if result is not None:
                if len(result) != 1:
                    raise BookmarkError(
                        f"Expected exactly 1 bookmark in CI folder, found {len(result)}"
                    )
                return result[0]

    raise BookmarkError(f"Bookmark folder '{CI_FOLDER_NAME}' not found")


def close_windows_on_display(samsung: DisplayInfo) -> None:
    """Close Chrome windows whose left edge is on the Samsung display."""
    source = f'''\
tell application "Google Chrome"
    set windowsToClose to {{}}
    repeat with w in windows
        set b to bounds of w
        if item 1 of b >= {samsung.x} then
            set end of windowsToClose to w
        end if
    end repeat
    repeat with w in windowsToClose
        close w
    end repeat
end tell'''
    try:
        applescript.run(source)
    except AppleScriptError as e:
        # -600 = Chrome not running — silently ignore
        if e.error_number == -600:
            return
        raise


def open_url_in_new_window(url: str, samsung: DisplayInfo) -> int:
    """Open a URL in a new Chrome window on the Samsung display. Returns window ID."""
    x1 = samsung.x + 100
    y1 = samsung.y + 100
    x2 = samsung.x + samsung.width - 100
    y2 = samsung.y + samsung.height - 100
    source = f'''\
tell application "Google Chrome"
    activate
    delay 0.5
    set newWindow to make new window
    set bounds of newWindow to {{{x1}, {y1}, {x2}, {y2}}}
    delay 0.5
    set URL of active tab of newWindow to "{url}"
    delay 1
    return id of newWindow
end tell'''
    return applescript.run_int(source)


def make_window_fullscreen(window_id: int) -> bool:
    """Make a specific Chrome window fullscreen by ID.

    Returns True if fullscreen was toggled, False if already fullscreen.
    """
    source = f'''\
set windowTitle to ""
tell application "Google Chrome"
    repeat with w in windows
        if (id of w as text) = "{window_id}" then
            set windowTitle to name of w
            exit repeat
        end if
    end repeat
    activate
end tell

delay 0.5

tell application "System Events"
    tell process "Google Chrome"
        click menu item windowTitle of menu "Window" of menu bar 1
        delay 0.5
        if value of attribute "AXFullScreen" of front window then
            return "already"
        end if
        keystroke "f" using {{control down, command down}}
    end tell
end tell
return "toggled"'''
    result = applescript.run(source)
    return result == "toggled"

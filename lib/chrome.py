"""Chrome bookmarks reading, window open/close/fullscreen."""

import json
import time

from lib import applescript
from lib.applescript import AppleScriptError
from lib.config import CHROME_BOOKMARKS_PATH, CI_FOLDER_NAME
from lib.display import DisplayInfo


class BookmarkError(Exception):
    """Raised when CI bookmarks are missing or misconfigured."""


def dismiss_chrome_dialogs() -> None:
    """Dismiss Chrome dialogs: profile errors (OK), proxy auth (Cancel on sheets)."""
    source = '''\
tell application "System Events"
    if not (exists process "Google Chrome") then return "0"
    set dismissed to 0
    tell process "Google Chrome"
        -- Dismiss profile error dialogs (windows with OK button)
        repeat
            set found to false
            repeat with w in windows
                try
                    click button "OK" of w
                    set found to true
                    set dismissed to dismissed + 1
                    exit repeat
                end try
            end repeat
            if not found then exit repeat
            delay 0.3
        end repeat
    end tell
    return dismissed as text
end tell'''
    try:
        result = applescript.run(source)
        if result is not None and result != "0":
            print(f"  Dismissed {result} Chrome dialog(s)")
    except AppleScriptError:
        pass


def exec_js_on_extension(extension_id: str, js: str) -> str | None:
    """Execute JavaScript on a Chrome tab whose URL contains the given extension ID."""
    escaped = js.replace("\\", "\\\\").replace('"', '\\"')
    return applescript.run(f'''
tell application "Google Chrome"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "{extension_id}" then
                return execute t javascript "{escaped}"
            end if
        end repeat
    end repeat
    error "Extension tab {extension_id} not found in Chrome"
end tell
''')


def exec_js_on_window(window_id: int, js: str) -> str | None:
    """Execute JavaScript on the active tab of a Chrome window by ID."""
    escaped = js.replace("\\", "\\\\").replace('"', '\\"')
    return applescript.run(f'''
tell application "Google Chrome"
    repeat with w in windows
        if (id of w as text) = "{window_id}" then
            return execute active tab of w javascript "{escaped}"
        end if
    end repeat
    error "Chrome window {window_id} not found"
end tell
''')


def get_ci_bookmark_url(subfolder: str) -> str:
    """Read the single CI bookmark URL from Chrome bookmarks.

    Looks for CI_FOLDER_NAME -> subfolder -> exactly 1 bookmark.
    Raises BookmarkError if any level is missing, empty, or has != 1 bookmark.
    """
    with open(CHROME_BOOKMARKS_PATH, encoding="utf-8") as f:
        bookmarks = json.load(f)

    def find_folder(node: dict, name: str) -> dict | None:
        if node.get("type") == "folder" and node.get("name") == name:
            return node
        for child in node.get("children", []):
            result = find_folder(child, name)
            if result is not None:
                return result
        return None

    for root_node in bookmarks.get("roots", {}).values():
        if isinstance(root_node, dict):
            ci_folder = find_folder(root_node, CI_FOLDER_NAME)
            if ci_folder is not None:
                sub = find_folder(ci_folder, subfolder)
                if sub is None:
                    raise BookmarkError(
                        f"Subfolder '{subfolder}' not found in '{CI_FOLDER_NAME}'"
                    )
                urls = [
                    child["url"]
                    for child in sub.get("children", [])
                    if child.get("type") == "url"
                ]
                if len(urls) != 1:
                    raise BookmarkError(
                        f"Expected exactly 1 bookmark in {CI_FOLDER_NAME}/{subfolder}, found {len(urls)}"
                    )
                return urls[0]

    raise BookmarkError(f"Bookmark folder '{CI_FOLDER_NAME}' not found")


def close_windows_on_display(samsung: DisplayInfo) -> None:
    """Close Chrome windows whose left edge is on the Samsung display.

    Two-pass: collect window IDs, then for each exit fullscreen and close.
    """
    source = f'''\
tell application "Google Chrome"
    set wIDs to {{}}
    set wCount to count of windows
    repeat with i from wCount to 1 by -1
        set w to window i
        set b to bounds of w
        set leftEdge to item 1 of b
        if leftEdge >= {samsung.x} and leftEdge < {samsung.x + samsung.width} then
            set end of wIDs to id of w
        end if
    end repeat
end tell

repeat with i from 1 to count of wIDs
    set theID to (item i of wIDs) as text

    -- Bring window to front
    tell application "Google Chrome"
        repeat with w in windows
            if (id of w as text) = theID then
                set index of w to 1
                exit repeat
            end if
        end repeat
    end tell

    -- Exit fullscreen if active
    tell application "System Events"
        tell process "Google Chrome"
            repeat with w in windows
                if subrole of w is "AXStandardWindow" then
                    if value of attribute "AXFullScreen" of w then
                        set value of attribute "AXFullScreen" of w to false
                        delay 1
                    end if
                    exit repeat
                end if
            end repeat
        end tell
    end tell

    -- Close window
    tell application "Google Chrome"
        repeat with w in windows
            if (id of w as text) = theID then
                close w
                exit repeat
            end if
        end repeat
    end tell
    delay 0.3
end repeat'''
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

    # Create window and load URL
    window_id = applescript.run_int(f'''\
tell application "Google Chrome"
    activate
    delay 0.5
    set newWindow to make new window
    delay 0.5
    set URL of active tab of newWindow to "{url}"
    delay 1
    return id of newWindow
end tell''')

    # macOS Sequoia auto-tiles new windows (AXFullScreen=true in tile mode),
    # which blocks Chrome set bounds from working cross-display.
    # Fix: exit tile-fullscreen via System Events, then set bounds.
    applescript.run(f'''\
tell application "Google Chrome" to activate
delay 0.3
tell application "System Events"
    tell process "Google Chrome"
        repeat with w in windows
            if subrole of w is "AXStandardWindow" then
                if value of attribute "AXFullScreen" of w then
                    set value of attribute "AXFullScreen" of w to false
                end if
                exit repeat
            end if
        end repeat
    end tell
end tell
delay 1
tell application "Google Chrome"
    repeat with w in windows
        if (id of w as text) = "{window_id}" then
            set bounds of w to {{{x1}, {y1}, {x2}, {y2}}}
            exit repeat
        end if
    end repeat
end tell'''
    )
    return window_id


def _check_fullscreen(window_id: int) -> bool:
    """Check if the Chrome window with the given ID is fullscreen.

    Brings the window to front via set index, then checks the frontmost
    AXStandardWindow — avoids title matching entirely.
    """
    source = f'''\
tell application "Google Chrome"
    repeat with w in windows
        if (id of w as text) = "{window_id}" then
            set index of w to 1
            exit repeat
        end if
    end repeat
end tell
tell application "System Events"
    tell process "Google Chrome"
        repeat with w in windows
            if subrole of w is "AXStandardWindow" then
                return value of attribute "AXFullScreen" of w
            end if
        end repeat
    end tell
end tell
return false'''
    return applescript.run(source) == "true"


def _bring_to_front_and_toggle(window_id: int) -> None:
    """Bring a Chrome window to front and send Ctrl+Cmd+F to toggle fullscreen."""
    send_keystroke_to_window(window_id, "f", modifiers=["control down", "command down"])


def send_keystroke_to_window(window_id: int, key: str, modifiers: list[str] | None = None) -> None:
    """Send a keystroke to a specific Chrome window by bringing it to front first."""
    if modifiers:
        ks = f'keystroke "{key}" using {{{", ".join(modifiers)}}}'
    else:
        ks = f'keystroke "{key}"'
    source = f'''\
tell application "Google Chrome"
    repeat with w in windows
        if (id of w as text) = "{window_id}" then
            set index of w to 1
            exit repeat
        end if
    end repeat
    activate
end tell
delay 0.5
tell application "System Events"
    tell process "Google Chrome"
        {ks}
    end tell
end tell'''
    applescript.run(source)


def focus_window(window_id: int) -> None:
    """Bring a Chrome window to front by ID."""
    source = f'''\
tell application "Google Chrome"
    repeat with w in windows
        if (id of w as text) = "{window_id}" then
            set index of w to 1
            exit repeat
        end if
    end repeat
    activate
end tell'''
    applescript.run(source)


def make_window_fullscreen(window_id: int) -> bool:
    """Make a specific Chrome window fullscreen by ID.

    Verifies via AXFullScreen after toggling, retries up to 3 times.
    Each check uses fresh System Events window references to avoid stale refs
    after macOS moves the window to its own Space.
    Returns True if fullscreen was toggled, False if already fullscreen.
    """
    if _check_fullscreen(window_id):
        return False

    for _ in range(3):
        _bring_to_front_and_toggle(window_id)
        time.sleep(2)  # wait for macOS fullscreen animation
        if _check_fullscreen(window_id):
            return True

    raise RuntimeError(f"Failed to fullscreen window {window_id} after 3 retries")

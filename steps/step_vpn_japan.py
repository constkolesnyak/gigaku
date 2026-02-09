#!/usr/bin/env python3
"""Step: Connect to a Japan VPN server via the NordVPN Chrome extension."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.applescript import AppleScriptError, run as applescript
from lib.chrome import make_window_fullscreen, open_url_in_new_window
from lib.config import NORDVPN_EXTENSION_ID, NORDVPN_POPUP_URL
from lib.display import DisplayInfo, find_samsung_display


class VPNError(Exception):
    """Raised when the VPN connection fails."""


def _exec_js(js: str) -> str | None:
    """Execute JavaScript on the NordVPN extension tab in Chrome."""
    escaped = js.replace("\\", "\\\\").replace('"', '\\"')
    try:
        return applescript(f'''
tell application "Google Chrome"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "{NORDVPN_EXTENSION_ID}" then
                return execute t javascript "{escaped}"
            end if
        end repeat
    end repeat
    error "NordVPN extension tab not found in Chrome"
end tell
''')
    except AppleScriptError as e:
        if "JavaScript through AppleScript is turned off" in str(e):
            raise VPNError(
                "In Chrome, enable View > Developer > 'Allow JavaScript from Apple Events'."
            ) from e
        raise


def _close_vpn_window(window_id: int) -> None:
    """Close the NordVPN Chrome window."""
    try:
        applescript(f'''
tell application "Google Chrome"
    repeat with w in windows
        if (id of w as text) = "{window_id}" then
            close w
            return
        end if
    end repeat
end tell
''')
        print(f"Closed NordVPN window {window_id}")
    except AppleScriptError:
        pass


def _wait_for_ui(timeout: int = 15) -> None:
    """Wait for the NordVPN React UI to render."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = _exec_js(
            "var el = document.querySelector('[data-testid=\"location-card-search-input\"]')"
            " || document.querySelector('[data-testid=\"connection-card-quick-connect-button\"]')"
            " || document.querySelector('[data-testid=\"connection-card-disconnect-button\"]');"
            " el ? 'ready' : 'loading'"
        )
        if result == "ready":
            return
        time.sleep(1)
    raise VPNError("NordVPN UI did not render within timeout")


def _get_connection_state() -> str | None:
    """Check current VPN connection state. Returns country name or None if disconnected."""
    result = _exec_js(
        "var title = document.querySelector('[data-testid=\"connection-card-title\"]');"
        " title ? title.textContent : 'unknown'"
    )
    if not result or result == "unknown" or result == "Connect to VPN":
        return None
    return result


def _disconnect(timeout: int = 15) -> None:
    """Disconnect from current VPN server."""
    _exec_js(
        "var btn = document.querySelector('[data-testid=\"connection-card-disconnect-button\"]');"
        " if (btn) { btn.click(); 'clicked' } else { 'no button' }"
    )
    print("Disconnecting...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = _exec_js(
            "document.querySelector('[data-testid=\"connection-card-disconnect-button\"]')"
            " ? 'connected' : 'disconnected'"
        )
        if result == "disconnected":
            print("Disconnected")
            time.sleep(1)
            return
        time.sleep(1)
    raise VPNError("Failed to disconnect within timeout")


def _connect_japan(timeout: int = 30) -> None:
    """Search for Japan and connect."""
    _exec_js(
        "var input = document.querySelector('[data-testid=\"location-card-search-input\"]');"
        " var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
        " setter.call(input, 'Japan');"
        " input.dispatchEvent(new Event('input', {bubbles: true}));"
        " 'searched'"
    )
    print("Searching for Japan...")
    time.sleep(1)

    result = _exec_js(
        "var btn = document.querySelector('[role=\"button\"][aria-label=\"Japan\"]');"
        " if (btn) { btn.click(); 'clicked' } else { 'not found' }"
    )
    if result != "clicked":
        raise VPNError("Japan not found in NordVPN country list")

    print("Connecting to Japan...")

    deadline = time.time() + timeout
    while time.time() < deadline:
        state = _get_connection_state()
        if state and "Japan" in state:
            print(f"Connected to {state}")
            return
        time.sleep(2)
    raise VPNError("Failed to connect to Japan within timeout")


def run(samsung: DisplayInfo) -> None:
    """Connect to Japan via NordVPN Chrome extension, fullscreen on Samsung."""
    window_id = open_url_in_new_window(NORDVPN_POPUP_URL, samsung)
    print(f"Opened NordVPN in Chrome window {window_id}")
    make_window_fullscreen(window_id)
    print(f"NordVPN window {window_id} set to fullscreen")

    _wait_for_ui()

    state = _get_connection_state()
    if state and "Japan" in state:
        print(f"Already connected to {state}")
        _close_vpn_window(window_id)
        return

    if state:
        print(f"Currently connected to {state}")
        _disconnect()

    _connect_japan()
    _close_vpn_window(window_id)


if __name__ == "__main__":
    samsung = find_samsung_display()
    if samsung is None:
        print("Samsung display not found")
        raise SystemExit(1)
    run(samsung)

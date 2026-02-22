#!/usr/bin/env python3
"""Step: Connect to or disconnect from VPN via the NordVPN Chrome extension."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.applescript import AppleScriptError, run as applescript
from lib.chrome import exec_js_on_extension, make_window_fullscreen, open_url_in_new_window
from lib.config import NORDVPN_EXTENSION_ID, NORDVPN_POPUP_URL
from lib.display import DisplayInfo, find_samsung_display


class VPNError(Exception):
    """Raised when the VPN connection fails."""


def _exec_js(js: str) -> str | None:
    """Execute JavaScript on the NordVPN extension tab in Chrome."""
    try:
        return exec_js_on_extension(NORDVPN_EXTENSION_ID, js)
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


def _connect(country: str, timeout: int = 30) -> None:
    """Search for a country and connect."""
    _exec_js(
        "var input = document.querySelector('[data-testid=\"location-card-search-input\"]');"
        " var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
        f" setter.call(input, '{country}');"
        " input.dispatchEvent(new Event('input', {bubbles: true}));"
        " 'searched'"
    )
    print(f"Searching for {country}...")
    time.sleep(1)

    result = _exec_js(
        f"var btn = document.querySelector('[role=\"button\"][aria-label=\"{country}\"]');"
        " if (btn) { btn.click(); 'clicked' } else { 'not found' }"
    )
    if result != "clicked":
        raise VPNError(f"{country} not found in NordVPN country list")

    print(f"Connecting to {country}...")

    deadline = time.time() + timeout
    while time.time() < deadline:
        state = _get_connection_state()
        if state and country in state:
            print(f"Connected to {state}")
            return
        time.sleep(2)
    raise VPNError(f"Failed to connect to {country} within timeout")


def run(samsung: DisplayInfo, country: str | None = None) -> None:
    """Connect to or disconnect from VPN via NordVPN Chrome extension.

    Args:
        samsung: Samsung display info for window placement.
        country: Country to connect to (e.g. "Japan"), or None to disconnect.
    """
    window_id = open_url_in_new_window(NORDVPN_POPUP_URL, samsung)
    print(f"Opened NordVPN in Chrome window {window_id}")
    make_window_fullscreen(window_id)
    print(f"NordVPN window {window_id} set to fullscreen")

    _wait_for_ui()

    state = _get_connection_state()

    if country is None:
        # Disconnect mode
        if state is None:
            print("VPN already disconnected")
        else:
            print(f"Currently connected to {state}")
            _disconnect()
        _close_vpn_window(window_id)
        return

    # Connect mode
    if state and country in state:
        print(f"Already connected to {state}")
        _close_vpn_window(window_id)
        return

    if state:
        print(f"Currently connected to {state}")
        _disconnect()

    _connect(country)
    _close_vpn_window(window_id)


if __name__ == "__main__":
    samsung = find_samsung_display()
    if samsung is None:
        print("Samsung display not found")
        raise SystemExit(1)
    if "--disconnect" in sys.argv:
        run(samsung, country=None)
    else:
        country = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "--disconnect" else "Japan"
        run(samsung, country=country)

#!/usr/bin/env python3
"""Pin the Migaku toolbar on the CI page."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.applescript import AppleScriptError
from lib.chrome import exec_js_on_window


class PinToolbarError(Exception):
    """Raised when the toolbar cannot be pinned."""


def _exec_js(window_id: int, js: str) -> str | None:
    """Execute JavaScript on the active tab of a Chrome window by ID."""
    try:
        return exec_js_on_window(window_id, js)
    except AppleScriptError as e:
        if "JavaScript through AppleScript is turned off" in str(e):
            raise PinToolbarError(
                "In Chrome, enable View > Developer > 'Allow JavaScript from Apple Events'."
            ) from e
        raise


def run(ci_window_id: int) -> None:
    """Pin the Migaku toolbar on the CI page. Raises PinToolbarError on failure."""
    # Poll for the Migaku shadow DOM to appear (toolbar injects after page load)
    for attempt in range(20):
        result = _exec_js(ci_window_id, (
            "var host = document.querySelector('#MigakuShadowDom');"
            " if (!host || !host.shadowRoot) 'no-shadow';"
            " else {"
            "   var btns = host.shadowRoot.querySelectorAll('button');"
            "   var found = 'no-button';"
            "   for (var i = 0; i < btns.length; i++) {"
            "     var label = btns[i].getAttribute('aria-label') || '';"
            "     if (label.indexOf('toolbar') !== -1) {"
            "       if (label === 'Pin toolbar') { btns[i].click(); found = 'pinned'; }"
            "       else { found = 'already-pinned'; }"
            "       break;"
            "     }"
            "   } found;"
            " }"
        ))
        if result == "pinned":
            print("Migaku toolbar pinned")
            return
        if result == "already-pinned":
            print("Migaku toolbar already pinned")
            return
        time.sleep(0.5)

    raise PinToolbarError(f"Migaku toolbar not found after 10s (last result: {result})")


if __name__ == "__main__":
    wid = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if wid is None:
        print("Usage: step_pin_toolbar.py <ci_window_id>")
        raise SystemExit(1)
    run(wid)

#!/usr/bin/env python3
"""Refresh Migaku extension tab after language switch."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.applescript import AppleScriptError, run as applescript
from lib.config import MIGAKU_EXTENSION_ID


def _exec_js(js: str) -> str | None:
    """Execute JavaScript on the Migaku extension tab in Chrome."""
    escaped = js.replace("\\", "\\\\").replace('"', '\\"')
    return applescript(f'''
tell application "Google Chrome"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "{MIGAKU_EXTENSION_ID}" then
                return execute t javascript "{escaped}"
            end if
        end repeat
    end repeat
    error "Migaku extension tab not found in Chrome"
end tell
''')


def run() -> None:
    """Reload the Migaku tab and wait for it to finish loading."""
    _exec_js("location.reload()")
    for _ in range(30):
        time.sleep(0.5)
        if _exec_js("document.readyState") == "complete":
            print("Migaku tab refreshed")
            return
    print("Warning: Migaku tab reload timed out after 15s")


if __name__ == "__main__":
    run()

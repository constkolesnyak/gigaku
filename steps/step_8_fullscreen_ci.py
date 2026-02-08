#!/usr/bin/env python3
"""Step 8: Make the CI Chrome window fullscreen."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import applescript
from lib.chrome import make_window_fullscreen
from lib.config import MIGAKU_EXTENSION_ID


def run(window_id: int) -> None:
    """Make the CI window fullscreen."""
    make_window_fullscreen(window_id)
    print(f"CI window {window_id} set to fullscreen")


def _find_ci_window_id() -> int:
    """Find the Chrome window ID that does NOT contain the Migaku extension URL."""
    source = f'''\
tell application "Google Chrome"
    repeat with w in windows
        set isMigaku to false
        repeat with t in tabs of w
            if URL of t contains "{MIGAKU_EXTENSION_ID}" then
                set isMigaku to true
                exit repeat
            end if
        end repeat
        if not isMigaku then
            return id of w
        end if
    end repeat
end tell'''
    return applescript.run_int(source)


if __name__ == "__main__":
    wid = _find_ci_window_id()
    run(wid)

#!/usr/bin/env python3
"""Step 7: Make the Migaku Chrome window fullscreen."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import applescript
from lib.chrome import make_window_fullscreen
from lib.config import MIGAKU_EXTENSION_ID


def _find_migaku_window_id() -> int:
    """Find the Chrome window ID containing the Migaku extension URL."""
    source = f'''\
tell application "Google Chrome"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "{MIGAKU_EXTENSION_ID}" then
                return id of w
            end if
        end repeat
    end repeat
end tell'''
    return applescript.run_int(source)


def run(window_id: int | None = None) -> None:
    """Find the Migaku window and make it fullscreen."""
    if window_id is None:
        window_id = _find_migaku_window_id()
    make_window_fullscreen(window_id)
    print(f"Migaku window {window_id} set to fullscreen")


if __name__ == "__main__":
    run()

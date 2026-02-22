#!/usr/bin/env python3
"""Open the CI bookmark in a new Chrome window on Samsung and fullscreen it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import applescript
from lib.chrome import get_ci_bookmark_url, open_url_in_new_window
from lib.display import DisplayInfo, find_samsung_display


def _maximize_on_samsung(window_id: int, samsung: DisplayInfo) -> None:
    """Set Chrome window bounds to fill the Samsung display before fullscreening."""
    x1 = samsung.x
    y1 = samsung.y
    x2 = samsung.x + samsung.width
    y2 = samsung.y + samsung.height
    applescript.run(f'''\
tell application "Google Chrome"
    repeat with w in windows
        if (id of w as text) = "{window_id}" then
            set bounds of w to {{{x1}, {y1}, {x2}, {y2}}}
            exit repeat
        end if
    end repeat
end tell''')


def run(samsung: DisplayInfo, subfolder: str = "ger") -> int:
    """Open CI bookmark URL in a new Chrome window and fullscreen it. Returns window ID."""
    url = get_ci_bookmark_url(subfolder)
    window_id = open_url_in_new_window(url, samsung)
    print(f"Opened CI in Chrome window {window_id}")
    _maximize_on_samsung(window_id, samsung)
    return window_id


if __name__ == "__main__":
    samsung = find_samsung_display()
    if samsung is None:
        print("Samsung display not found")
        raise SystemExit(1)
    sf = sys.argv[1] if len(sys.argv) > 1 else "ger"
    run(samsung, subfolder=sf)

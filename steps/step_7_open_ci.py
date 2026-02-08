#!/usr/bin/env python3
"""Step 7: Open the CI bookmark in a new Chrome window on Samsung and fullscreen it."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.chrome import get_ci_bookmark_url, make_window_fullscreen, open_url_in_new_window
from lib.display import DisplayInfo, find_samsung_display


def run(samsung: DisplayInfo) -> int:
    """Open CI bookmark URL in a new Chrome window and fullscreen it. Returns window ID."""
    url = get_ci_bookmark_url()
    window_id = open_url_in_new_window(url, samsung)
    print(f"Opened CI in Chrome window {window_id}")
    time.sleep(1.5)  # macOS fullscreen animation
    make_window_fullscreen(window_id)
    print(f"CI window {window_id} set to fullscreen")
    return window_id


if __name__ == "__main__":
    samsung = find_samsung_display()
    if samsung is None:
        print("Samsung display not found")
        raise SystemExit(1)
    run(samsung)

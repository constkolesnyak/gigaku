#!/usr/bin/env python3
"""Step 4: Open the CI bookmark in a new Chrome window on Samsung."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.chrome import get_ci_bookmark_url, open_url_in_new_window
from lib.display import DisplayInfo, find_samsung_display


def run(samsung: DisplayInfo) -> int:
    """Open CI bookmark URL in a new Chrome window. Returns window ID."""
    url = get_ci_bookmark_url()
    window_id = open_url_in_new_window(url, samsung)
    print(f"Opened CI in Chrome window {window_id}")
    return window_id


if __name__ == "__main__":
    samsung = find_samsung_display()
    if samsung is None:
        print("Samsung display not found")
        raise SystemExit(1)
    run(samsung)

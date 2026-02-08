#!/usr/bin/env python3
"""Step 4: Open Migaku extension in a new Chrome window on Samsung."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.chrome import open_url_in_new_window
from lib.config import MIGAKU_APP_URL
from lib.display import DisplayInfo, find_samsung_display


def run(samsung: DisplayInfo) -> int:
    """Open Migaku app URL in a new Chrome window. Returns window ID."""
    window_id = open_url_in_new_window(MIGAKU_APP_URL, samsung)
    print(f"Opened Migaku in Chrome window {window_id}")
    return window_id


if __name__ == "__main__":
    samsung = find_samsung_display()
    if samsung is None:
        print("Samsung display not found")
        raise SystemExit(1)
    run(samsung)

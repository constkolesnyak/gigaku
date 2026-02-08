#!/usr/bin/env python3
"""Step 1: Poll until Samsung TV display is connected."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import POLL_INTERVAL
from lib.display import DisplayInfo, find_samsung_display, list_displays


def run() -> DisplayInfo:
    """Block until a Samsung display appears, then return its info."""
    print("Connect the Samsung TV display...")
    while True:
        samsung = find_samsung_display()
        if samsung is not None:
            print(f"Samsung TV detected! ({samsung.width}x{samsung.height} at {samsung.x},{samsung.y})")
            return samsung
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    print("Detected displays:")
    for d in list_displays():
        print(f"  id={d.display_id} vendor=0x{d.vendor:04X} {d.width}x{d.height} builtin={d.builtin}")
    result = run()
    print(f"Samsung: {result}")

#!/usr/bin/env python3
"""Close any Chrome windows on the Samsung display."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.chrome import close_windows_on_display
from lib.display import DisplayInfo, find_samsung_display


def run(samsung: DisplayInfo) -> None:
    """Close Chrome windows positioned on the Samsung display."""
    close_windows_on_display(samsung)
    print("Closed existing Chrome windows on Samsung display")


if __name__ == "__main__":
    samsung = find_samsung_display()
    if samsung is None:
        print("Samsung display not found")
        raise SystemExit(1)
    run(samsung)

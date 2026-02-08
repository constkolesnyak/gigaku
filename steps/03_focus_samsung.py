"""Step 3: Move cursor to Samsung display center and click to focus."""

import time

from Quartz.CoreGraphics import (
    CGEventCreateMouseEvent,
    CGEventPost,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventMouseMoved,
    kCGHIDEventTap,
    kCGMouseButtonLeft,
)

from lib.display import DisplayInfo, find_samsung_display


def run(samsung: DisplayInfo) -> None:
    """Move cursor to Samsung center and click to shift focus."""
    x, y = samsung.center

    # Move cursor
    move = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (x, y), 0)
    CGEventPost(kCGHIDEventTap, move)
    time.sleep(0.1)

    # Click
    down = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, (x, y), kCGMouseButtonLeft)
    CGEventPost(kCGHIDEventTap, down)
    time.sleep(0.05)
    up = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, (x, y), kCGMouseButtonLeft)
    CGEventPost(kCGHIDEventTap, up)

    print(f"Clicked on Samsung display ({x}, {y})")


if __name__ == "__main__":
    samsung = find_samsung_display()
    if samsung is None:
        print("Samsung display not found")
        raise SystemExit(1)
    run(samsung)

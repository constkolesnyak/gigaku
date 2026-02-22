#!/usr/bin/env python3
"""Make the Netflix video player fullscreen via 'f' keystroke."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.chrome import exec_js_on_window, send_keystroke_to_window


def run(ci_window_id: int) -> None:
    """Send 'f' to fullscreen the Netflix video player. Skips non-Netflix pages."""
    hostname = exec_js_on_window(ci_window_id, "window.location.hostname")
    if hostname is None or "netflix" not in hostname:
        print(f"CI page is not Netflix ({hostname}), skipping video fullscreen")
        return

    send_keystroke_to_window(ci_window_id, "f")
    time.sleep(1)
    print("Netflix video fullscreened")


if __name__ == "__main__":
    wid = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if wid is None:
        print("Usage: step_fullscreen_ci_video.py <ci_window_id>")
        raise SystemExit(1)
    run(wid)

#!/usr/bin/env python3
"""Pause media: KEY_PAUSE on HDMI1 device via CEC, JS pause on CI Chrome window."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import TV_MAC_SOURCE


def _exec_js(window_id: int, js: str) -> str | None:
    """Execute JavaScript on the active tab of a Chrome window by ID."""
    from lib.applescript import run as applescript

    escaped = js.replace("\\", "\\\\").replace('"', '\\"')
    return applescript(f'''
tell application "Google Chrome"
    repeat with w in windows
        if (id of w as text) = "{window_id}" then
            return execute active tab of w javascript "{escaped}"
        end if
    end repeat
    error "Chrome window {window_id} not found"
end tell
''')


def run(ci_window_id: int | None = None) -> None:
    """Pause media at current playback points.

    - If TV is on HDMI1 (not Mac input), send KEY_PAUSE via TV remote (CEC forwards to device).
    - If ci_window_id is given, wait for video/audio to load and pause it via JS.
    """
    # Pause HDMI1 device if TV is currently on a non-Mac input
    if ci_window_id is None:
        try:
            from lib.tv import get_current_source, send_key

            current = get_current_source()
            if current != TV_MAC_SOURCE:
                print(f"TV on {current}, sending KEY_PAUSE...")
                send_key("KEY_PAUSE")
                print("Sent KEY_PAUSE.")
            else:
                print(f"TV already on {TV_MAC_SOURCE}, skipping pause.")
        except Exception as e:
            print(f"Could not pause TV input ({e}), skipping.")

    # Pause CI Chrome window via JS
    if ci_window_id is not None:
        print(f"Waiting for media to load in CI window {ci_window_id}...")
        for attempt in range(30):
            result = _exec_js(ci_window_id, (
                "var m = document.querySelector('video') || document.querySelector('audio');"
                " if (!m) {"
                "   var frames = document.querySelectorAll('iframe');"
                "   for (var i = 0; i < frames.length; i++) {"
                "     try { var fd = frames[i].contentDocument;"
                "       if (fd) { m = fd.querySelector('video') || fd.querySelector('audio'); }"
                "     } catch(e) {}"
                "     if (m) break;"
                "   }"
                " }"
                " var r = 'no_media';"
                " if (m && m.readyState >= 3) { m.pause(); r = 'paused'; }"
                " else if (m) { r = 'loading'; }"
                " r"
            ))
            if result == "paused":
                print(f"Paused media in CI window {ci_window_id}.")
                return
            print(f"  {result} (attempt {attempt + 1}/30)")
            time.sleep(1)
        print("Warning: no media found or loaded after 30s, skipping pause.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run(ci_window_id=int(sys.argv[1]))
    else:
        run()

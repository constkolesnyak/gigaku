#!/usr/bin/env python3
"""Pause media: KEY_PAUSE on HDMI1 device via CEC, spacebar on CI Chrome window."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import TV_MAC_SOURCE


def run(ci_window_id: int | None = None) -> None:
    """Pause media at current playback points.

    - If TV is on HDMI1 (not Mac input), send KEY_PAUSE via TV remote (CEC forwards to device).
    - If ci_window_id is given, send spacebar to pause Netflix/YouTube in that Chrome window.
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

    # Pause CI Chrome window via spacebar
    if ci_window_id is not None:
        from lib.chrome import send_keystroke_to_window

        print(f"Waiting 3s for video autoplay in CI window {ci_window_id}...")
        time.sleep(3)
        send_keystroke_to_window(ci_window_id, " ")
        print(f"Sent spacebar to CI window {ci_window_id}.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run(ci_window_id=int(sys.argv[1]))
    else:
        run()

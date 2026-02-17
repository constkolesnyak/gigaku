"""CLI entry point for the gigaku command."""

import signal
import sys
import time

from lib.chrome import dismiss_chrome_dialogs, focus_window, get_ci_bookmark_url
from lib.config import LANG_MAP
from steps import (
    step_0_wait_samsung,
    step_1_switch_input,
    step_2_focus_samsung,
    step_3_close_samsung_windows,
    step_4_open_migaku,
    step_5_fullscreen_migaku,
    step_6_switch_language,
    step_7_open_ci,
    step_8_pin_toolbar,
    step_pause_media,
    step_vpn,
)


def main():
    # Parse language arg
    if len(sys.argv) != 2 or sys.argv[1] not in LANG_MAP:
        valid = ", ".join(LANG_MAP)
        print(f"Usage: gigaku <{valid}>")
        raise SystemExit(1)

    language, subfolder, vpn_country = LANG_MAP[sys.argv[1]]

    # Validate early — fail before any steps if CI bookmarks are misconfigured
    get_ci_bookmark_url(subfolder)

    samsung = step_0_wait_samsung.run()
    try:
        dismiss_chrome_dialogs()
        step_pause_media.run()
        dismiss_chrome_dialogs()
        step_1_switch_input.run()
        time.sleep(3)  # wait for TV input switch + source menu to close
        dismiss_chrome_dialogs()
        step_2_focus_samsung.run(samsung)
        dismiss_chrome_dialogs()
        step_3_close_samsung_windows.run(samsung)
        dismiss_chrome_dialogs()
        step_vpn.run(samsung, country=vpn_country)
        dismiss_chrome_dialogs()
        ci_window_id = step_7_open_ci.run(samsung, subfolder=subfolder)
        dismiss_chrome_dialogs()
        step_pause_media.run(ci_window_id=ci_window_id)
        dismiss_chrome_dialogs()
        migaku_window_id = step_4_open_migaku.run(samsung)
        dismiss_chrome_dialogs()
        step_6_switch_language.run(language=language)
        dismiss_chrome_dialogs()
        step_5_fullscreen_migaku.run(migaku_window_id)
        dismiss_chrome_dialogs()
        focus_window(ci_window_id)
        dismiss_chrome_dialogs()
        step_8_pin_toolbar.run(ci_window_id)

        print("\nSetup complete. Press Ctrl+C to clean up and exit.")
        while True:
            signal.pause()
    except KeyboardInterrupt:
        print("\nCleaning up...")

        try:
            step_vpn.run(samsung, country=None)
        except Exception as e:
            print(f"  VPN disconnect failed: {e}")

        try:
            step_3_close_samsung_windows.run(samsung)
        except Exception as e:
            print(f"  Close windows failed: {e}")

        try:
            from lib.tv import switch_to_hdmi1
            switch_to_hdmi1()
        except Exception as e:
            print(f"  TV switch failed: {e}")

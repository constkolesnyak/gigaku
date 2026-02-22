"""CLI entry point for the gigaku command."""

import signal
import sys
import time

from lib.chrome import dismiss_chrome_dialogs, focus_window, get_ci_bookmark_url
from lib.config import LANG_MAP
from lib.tv import switch_to_hdmi1
from steps import (
    step_close_samsung_windows,
    step_dim_display,
    step_focus_samsung,
    step_fullscreen_migaku,
    step_open_ci,
    step_open_migaku,
    step_pause_media,
    step_pin_toolbar,
    step_switch_input,
    step_switch_language,
    step_vpn,
    step_wait_samsung,
)


def _step(fn, *args, **kwargs):
    """Dismiss Chrome dialogs then run a step function."""
    dismiss_chrome_dialogs()
    return fn(*args, **kwargs)


def main():
    # Parse language arg
    if len(sys.argv) != 2 or sys.argv[1] not in LANG_MAP:
        valid = ", ".join(LANG_MAP)
        print(f"Usage: gigaku <{valid}>")
        raise SystemExit(1)

    language, subfolder, vpn_country = LANG_MAP[sys.argv[1]]

    # Validate early — fail before any steps if CI bookmarks are misconfigured
    get_ci_bookmark_url(subfolder)

    samsung = step_wait_samsung.run()
    try:
        _step(step_pause_media.run)
        _step(step_switch_input.run)
        time.sleep(3)  # wait for TV input switch + source menu to close
        step_dim_display.run()  # no Chrome interaction, no dismiss needed
        _step(step_focus_samsung.run, samsung)
        _step(step_close_samsung_windows.run, samsung)
        _step(step_vpn.run, samsung, country=vpn_country)
        ci_window_id = _step(step_open_ci.run, samsung, subfolder=subfolder)
        _step(step_pause_media.run, ci_window_id=ci_window_id)
        migaku_window_id = _step(step_open_migaku.run, samsung)
        _step(step_switch_language.run, language=language)
        _step(step_fullscreen_migaku.run, migaku_window_id)
        _step(focus_window, ci_window_id)
        _step(step_pin_toolbar.run, ci_window_id)

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
            step_close_samsung_windows.run(samsung)
        except Exception as e:
            print(f"  Close windows failed: {e}")

        try:
            switch_to_hdmi1()
        except Exception as e:
            print(f"  TV switch failed: {e}")

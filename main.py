"""Gigaku — Samsung TV display auto-setup orchestrator."""

import time

from lib.chrome import get_ci_bookmark_url
from steps import (
    step_0_wait_samsung,
    step_1_switch_input,
    step_2_focus_samsung,
    step_3_close_samsung_windows,
    step_4_open_migaku,
    step_5_fullscreen_migaku,
    step_6_switch_language,
    step_7_open_ci,
    step_pause_media,
)

# Validate early — fail before any steps if CI bookmarks are misconfigured
get_ci_bookmark_url()

samsung = step_0_wait_samsung.run()
step_pause_media.run()
step_1_switch_input.run()
time.sleep(3)  # wait for TV input switch + source menu to close
step_2_focus_samsung.run(samsung)
step_3_close_samsung_windows.run(samsung)
migaku_window_id = step_4_open_migaku.run(samsung)
step_5_fullscreen_migaku.run(migaku_window_id)
step_6_switch_language.run()
ci_window_id = step_7_open_ci.run(samsung)
step_pause_media.run(ci_window_id=ci_window_id)

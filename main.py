"""Gigaku — Samsung TV display auto-setup orchestrator."""

import time

from steps import (
    step_1_wait_samsung,
    step_2_focus_samsung,
    step_3_close_samsung_windows,
    step_4_open_migaku,
    step_5_fullscreen_migaku,
    step_6_switch_language,
    step_7_open_ci,
)

samsung = step_1_wait_samsung.run()
step_2_focus_samsung.run(samsung)
step_3_close_samsung_windows.run(samsung)
migaku_window_id = step_4_open_migaku.run(samsung)
step_5_fullscreen_migaku.run(migaku_window_id)
time.sleep(1.5)  # macOS fullscreen animation
step_6_switch_language.run()
step_7_open_ci.run(samsung)

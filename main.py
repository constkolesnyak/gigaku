"""Gigaku — Samsung TV display auto-setup orchestrator."""

import time
from importlib import import_module

wait_samsung = import_module("steps.step_1_wait_samsung")
close_samsung_windows = import_module("steps.step_2_close_samsung_windows")
focus_samsung = import_module("steps.step_3_focus_samsung")
open_ci = import_module("steps.step_4_open_ci")
open_migaku = import_module("steps.step_5_open_migaku")
switch_language = import_module("steps.step_6_switch_language")
fullscreen_migaku = import_module("steps.step_7_fullscreen_migaku")
fullscreen_ci = import_module("steps.step_8_fullscreen_ci")

samsung = wait_samsung.run()
close_samsung_windows.run(samsung)
focus_samsung.run(samsung)
ci_window_id = open_ci.run(samsung)
migaku_window_id = open_migaku.run(samsung)
switch_language.run()
fullscreen_migaku.run(migaku_window_id)
time.sleep(1.5)  # macOS fullscreen animation
fullscreen_ci.run(ci_window_id)

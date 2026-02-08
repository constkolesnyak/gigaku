# Gigaku

macOS automation that sets up a Samsung TV display with Chrome windows for CI and Migaku language learning.

## Run

```bash
poetry run python main.py              # Full workflow
poetry run steps/step_5_fullscreen_migaku.py  # Individual step
```

## Architecture

**`lib/`** — shared modules, no subprocess anywhere:
- `config.py` — all constants (paths, IDs, vendor codes, timing)
- `applescript.py` — `Foundation.NSAppleScript` wrapper (`run()`, `run_int()`, `AppleScriptError`)
- `display.py` — `CoreGraphics` display detection (`DisplayInfo` dataclass, `list_displays()`, `find_samsung_display()`)
- `chrome.py` — bookmarks JSON reading, window open/close/fullscreen via AppleScript (`BookmarkError`)

**`steps/`** — each step has a `run()` function and `if __name__ == "__main__":` for standalone testing:
1. `step_1_wait_samsung` — polls `find_samsung_display()` every 2s, returns `DisplayInfo`
2. `step_2_focus_samsung` — moves cursor to `samsung.center` + clicks via `CGEvent`
3. `step_3_close_samsung_windows` — closes Chrome windows on Samsung (ignores Chrome-not-running)
4. `step_4_open_migaku` — opens Migaku extension URL in new Chrome window, returns window ID
5. `step_5_fullscreen_migaku` — fullscreens Migaku window by ID
6. `step_6_switch_language` — AppleScript `execute javascript` on existing Migaku tab in Chrome
7. `step_7_open_ci` — reads CI bookmark, opens in new Chrome window, and fullscreens it

**`main.py`** — orchestrator calling steps in order. No try/except — errors propagate with full tracebacks.

## Key Design Decisions

- **No subprocess**: `osascript` replaced by `NSAppleScript` (`lib/applescript.py`), `system_profiler` replaced by `CoreGraphics` APIs (`lib/display.py`)
- **Real display coordinates**: `DisplayInfo` from CoreGraphics replaces hardcoded `MAIN_DISPLAY_WIDTH = 2560`
- **Single CI bookmark enforced**: `get_ci_bookmark_url()` raises `BookmarkError` if CI folder has != 1 bookmark
- **Samsung vendor IDs**: EDID codes `0x4C2D` ("SAM") and `0x4CA3` ("SEC") in `SAMSUNG_VENDOR_IDS`. If a new Samsung TV reports a different code, step 1 prints all detected displays so the user can add the ID to `config.py`

## Error Types

- `AppleScriptError` (`.error_number`) — error -600 (app not running) silently ignored in close step
- `BookmarkError` — CI folder missing, empty, or wrong count
- `LanguageSwitchError` — wraps AppleScript/JS failures in language switch

## Dependencies

- `pyobjc-framework-quartz` — provides `Foundation`, `Quartz.CoreGraphics`
- Chrome "Allow JavaScript from Apple Events" must be enabled (View > Developer)
- Python ^3.14, managed by Poetry

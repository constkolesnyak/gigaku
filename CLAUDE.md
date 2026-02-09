# Gigaku

macOS automation that sets up a Samsung TV display with Chrome windows for CI and Migaku language learning.

## Run

```bash
poetry run python main.py              # Full workflow
poetry run steps/step_5_fullscreen_migaku.py  # Individual step
```

## Architecture

**`lib/`** — shared modules:
- `config.py` — all constants (paths, IDs, vendor codes, timing)
- `applescript.py` — `Foundation.NSAppleScript` wrapper (`run()`, `run_int()`, `AppleScriptError`)
- `display.py` — `CoreGraphics` display detection (`DisplayInfo` dataclass, `list_displays()`, `find_samsung_display()`)
- `chrome.py` — bookmarks JSON reading, window open/close/fullscreen/keystroke via AppleScript (`BookmarkError`)
- `tv.py` — Samsung TV control: UPnP SOAP for direct input switching (`get_current_source()`, `set_source()`, `get_source_list()`), encrypted WebSocket as fallback (`switch_to_mac()`, `send_key()`, `discover()`, `TVError`)
- `_rijndael.py` — reduced-round Rijndael (3 rounds) for Samsung SamyGO key derivation

**`steps/`** — each step has a `run()` function and `if __name__ == "__main__":` for standalone testing:
0. `step_0_wait_samsung` — polls `find_samsung_display()` every 2s, returns `DisplayInfo`
1. `step_1_switch_input` — switches TV input to Mac via UPnP SOAP, falls back to encrypted WebSocket (`discover` arg for SSDP, `sources` arg to list available inputs)
2. `step_2_focus_samsung` — moves cursor to `samsung.center` + clicks via `CGEvent`
3. `step_3_close_samsung_windows` — closes Chrome windows on Samsung (ignores Chrome-not-running)
4. `step_4_open_migaku` — opens Migaku extension URL in new Chrome window, returns window ID
5. `step_5_fullscreen_migaku` — fullscreens Migaku window by ID
6. `step_6_switch_language` — AppleScript `execute javascript` on existing Migaku tab in Chrome
7. `step_7_open_ci` — reads CI bookmark, opens in new Chrome window, and fullscreens it
- `step_pause_media` — pauses media: `KEY_PAUSE` via TV remote if on HDMI1, spacebar to CI Chrome window. Called twice in main: before input switch and after CI opens

**`main.py`** — orchestrator calling steps in order. No try/except — errors propagate with full tracebacks.

## Key Design Decisions

- **No subprocess**: `osascript` replaced by `NSAppleScript` (`lib/applescript.py`), `system_profiler` replaced by `CoreGraphics` APIs (`lib/display.py`), TV control uses encrypted WebSocket via `pycryptodome` + `websocket-client` (`lib/tv.py`)
- **Samsung TV input switching**: UPnP SOAP on port 7676 (`MainTVAgent2` service) for direct input detection and switching — no menu navigation needed. Falls back to encrypted WebSocket key sequence (`KEY_SOURCE → KEY_RIGHT → KEY_ENTER`) if SOAP is unavailable. SOAP uses IP-based ACL (one-time TV popup), independent of WebSocket pairing
- **Samsung TV encrypted protocol**: 2014 H-series uses encrypted Socket.IO on port 8000 with PIN-based pairing on port 8080. Requires reduced-round Rijndael (3 rounds, NOT standard AES) for key derivation
- **Real display coordinates**: `DisplayInfo` from CoreGraphics replaces hardcoded `MAIN_DISPLAY_WIDTH = 2560`
- **Single CI bookmark enforced**: `get_ci_bookmark_url()` raises `BookmarkError` if CI folder has != 1 bookmark
- **Samsung vendor IDs**: EDID codes `0x4C2D` ("SAM") and `0x4CA3` ("SEC") in `SAMSUNG_VENDOR_IDS`. If a new Samsung TV reports a different code, step 0 prints all detected displays so the user can add the ID to `config.py`

## Error Types

- `AppleScriptError` (`.error_number`) — error -600 (app not running) silently ignored in close step
- `BookmarkError` — CI folder missing, empty, or wrong count
- `TVError` — TV IP not set, pairing failure, WebSocket connection failure, or key send failure
- `LanguageSwitchError` — wraps AppleScript/JS failures in language switch

## Dependencies

- `pyobjc-framework-quartz` — provides `Foundation`, `Quartz.CoreGraphics`
- `pycryptodome` — AES encryption for Samsung TV encrypted WebSocket protocol
- `requests` — HTTP requests for TV pairing
- `websocket-client` — Socket.IO WebSocket connection to TV
- Chrome "Allow JavaScript from Apple Events" must be enabled (View > Developer)
- Python ^3.14, managed by Poetry

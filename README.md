# Gigaku

macOS automation that sets up a Samsung TV as a second display with Chrome windows for CI media and [Migaku](https://www.migaku.com/) language learning.

## What it does

1. Waits for the Samsung TV to appear as a connected display
2. Switches the TV input to the Mac via UPnP SOAP (or encrypted WebSocket fallback)
3. Closes any existing Chrome windows on the TV display
4. Connects to a VPN if needed (Japan for Japanese)
5. Opens the Migaku browser extension fullscreen on the TV
6. Switches Migaku to the target language
7. Opens a CI media bookmark fullscreen on the TV
8. Pauses any playing media on the TV

On `Ctrl+C`, it disconnects the VPN, closes Chrome windows on the TV, and switches the TV input back to HDMI1.

## Requirements

- macOS 15+ (Sequoia)
- Python 3.14+
- [Poetry](https://python-poetry.org/)
- Google Chrome with "Allow JavaScript from Apple Events" enabled (Chrome > View > Developer)
- Samsung 2014 H-series TV (tested on UE40H7000) connected as a display
- Migaku and NordVPN Chrome extensions installed

## Install

```bash
poetry install
```

Or with [pipx](https://pipx.pypa.io/):

```bash
pipx install .
```

## Usage

```bash
gigaku <language>
```

Available languages: `jap`, `ger`

```bash
gigaku jap   # Japanese + Japan VPN
gigaku ger   # German
```

Individual steps can be run standalone for testing:

```bash
poetry run python steps/step_1_switch_input.py
poetry run python steps/step_5_fullscreen_migaku.py
```

## Configuration

Edit `lib/config.py` to change:

- `TV_IP` — Samsung TV IP address (run step 1 with `discover` to find via SSDP)
- `TV_MAC_SOURCE` / `TV_MAC_SOURCE_ID` — which HDMI input the Mac is on
- `CHROME_PROFILE` — Chrome profile to read bookmarks from
- `CI_FOLDER_NAME` — bookmarks folder name containing exactly one CI media bookmark
- `LANG_MAP` — add new language/bookmark subfolder mappings

## Samsung TV setup

The TV must approve the Mac's IP for UPnP control (one-time popup on first connection). The encrypted WebSocket fallback requires a separate PIN-based pairing — the token is saved to `.tv_token`.

Run `poetry run python steps/step_1_switch_input.py sources` to list available TV inputs and their IDs.

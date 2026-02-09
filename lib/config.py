"""All constants: paths, IDs, vendor codes, timing."""

import os

# Samsung TV EDID vendor codes ("SAM" and "SEC")
SAMSUNG_VENDOR_IDS = {0x4C2D, 0x4CA3}

# Chrome paths
CHROME_USER_DATA = os.path.expanduser("~/Library/Application Support/Google/Chrome")
CHROME_PROFILE = "Profile 1"
CHROME_BOOKMARKS_PATH = os.path.join(CHROME_USER_DATA, CHROME_PROFILE, "Bookmarks")

# Migaku extension
MIGAKU_EXTENSION_ID = "dmeppfcidcpcocleneopiblmpnbokhep"
MIGAKU_APP_URL = (
    f"chrome-extension://{MIGAKU_EXTENSION_ID}/pages/app-window/index.html"
)

# Bookmarks
CI_FOLDER_NAME = "CI"

# Timing
POLL_INTERVAL = 2  # seconds between Samsung display polls

# Available Migaku languages
AVAILABLE_LANGUAGES = [
    "Cantonese", "English", "French", "German", "Italian",
    "Japanese", "Korean", "Mandarin", "Portuguese", "Spanish", "Vietnamese",
]

# Samsung TV remote control (encrypted WebSocket, 2014 H-series)
TV_IP = "192.168.0.77"  # Samsung TV IP — run step_0 with 'discover' to find
TV_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", ".tv_token")

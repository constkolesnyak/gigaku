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

# NordVPN extension
NORDVPN_EXTENSION_ID = "fjoaledfpmneenckfbpdfhkmimnjocfa"
NORDVPN_POPUP_URL = f"chrome-extension://{NORDVPN_EXTENSION_ID}/index.html"

# Bookmarks
CI_FOLDER_NAME = "ci"

# Language arg mapping: arg -> (Migaku language name, CI bookmark subfolder)
LANG_MAP = {
    "ger": ("German", "ger"),
    "jap": ("Japanese", "jap"),
}

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

# Samsung TV UPnP SOAP (direct input switching, no menu navigation)
TV_UPNP_PORT = 7676
TV_UPNP_CONTROL_PATH = "/smp_31_"  # MainTVAgent2 controlURL from /smp_29_ device desc
TV_MAC_SOURCE = "HDMI2"
TV_MAC_SOURCE_ID = 58  # from GetSourceList — 0=TV, 57=HDMI1, 58=HDMI2, 59=HDMI3, etc.

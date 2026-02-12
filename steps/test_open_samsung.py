#!/usr/bin/env python3
"""Test helper: open Migaku + CI on Samsung, fullscreen both, pause CI."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.chrome import get_ci_bookmark_url, make_window_fullscreen, open_url_in_new_window
from lib.config import MIGAKU_APP_URL
from lib.display import find_samsung_display
from steps.step_pause_media import run as pause_media

if __name__ == "__main__":
    samsung = find_samsung_display()
    if samsung is None:
        print("Samsung display not found")
        raise SystemExit(1)

    sf = sys.argv[1] if len(sys.argv) > 1 else "ger"

    mid = open_url_in_new_window(MIGAKU_APP_URL, samsung)
    print(f"Opened Migaku window {mid}")
    make_window_fullscreen(mid)
    print("Migaku fullscreened")

    ci_url = get_ci_bookmark_url(sf)
    cid = open_url_in_new_window(ci_url, samsung)
    print(f"Opened CI window {cid}")
    make_window_fullscreen(cid)
    print("CI fullscreened")

    pause_media(ci_window_id=cid)
    print("Done")

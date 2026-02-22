#!/usr/bin/env python3
"""Refresh Migaku extension tab after language switch."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.chrome import exec_js_on_extension
from lib.config import MIGAKU_EXTENSION_ID


def run() -> None:
    """Reload the Migaku tab and wait for it to finish loading."""
    exec_js_on_extension(MIGAKU_EXTENSION_ID, "location.reload()")
    for _ in range(30):
        time.sleep(0.5)
        if exec_js_on_extension(MIGAKU_EXTENSION_ID, "document.readyState") == "complete":
            print("Migaku tab refreshed")
            return
    print("Warning: Migaku tab reload timed out after 15s")


if __name__ == "__main__":
    run()

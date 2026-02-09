#!/usr/bin/env python3
"""Step 0: Switch Samsung TV input to Mac via WebSocket."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.tv import discover, switch_to_mac


def run() -> None:
    """Switch the TV to the Mac's HDMI input."""
    switch_to_mac()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "discover":
        ips = discover()
        if ips:
            print("Found Samsung TVs:")
            for ip in ips:
                print(f"  {ip}")
        else:
            print("No Samsung TVs found on the network.")
    else:
        run()

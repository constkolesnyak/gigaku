#!/usr/bin/env python3
"""Close any Netflix tabs left open from previous sessions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.applescript import AppleScriptError, run as run_applescript


def run() -> None:
    """Close all Chrome tabs with 'netflix' in the URL."""
    try:
        run_applescript("""
            tell application "Google Chrome"
                repeat with w from (count of windows) to 1 by -1
                    set theWindow to window w
                    repeat with t from (count of tabs of theWindow) to 1 by -1
                        set theURL to URL of tab t of theWindow
                        if theURL contains "netflix" then
                            close tab t of theWindow
                        end if
                    end repeat
                end repeat
            end tell
        """)
    except AppleScriptError as e:
        if e.error_number == -600:
            return  # Chrome not running
        raise
    print("Closed Netflix tabs")


if __name__ == "__main__":
    run()

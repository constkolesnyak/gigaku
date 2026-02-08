"""Step 7: Make the Migaku Chrome window fullscreen."""

from lib import applescript
from lib.chrome import make_window_fullscreen
from lib.config import MIGAKU_EXTENSION_ID


def run(window_id: int) -> None:
    """Make the Migaku window fullscreen."""
    make_window_fullscreen(window_id)
    print(f"Migaku window {window_id} set to fullscreen")


def _find_migaku_window_id() -> int:
    """Find the Chrome window ID containing the Migaku extension URL."""
    source = f'''\
tell application "Google Chrome"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "{MIGAKU_EXTENSION_ID}" then
                return id of w
            end if
        end repeat
    end repeat
end tell'''
    return applescript.run_int(source)


if __name__ == "__main__":
    wid = _find_migaku_window_id()
    run(wid)

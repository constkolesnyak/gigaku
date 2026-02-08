#!/usr/bin/env python3
"""Step 6: Switch Migaku extension language via AppleScript JS execution."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.applescript import AppleScriptError, run as applescript
from lib.config import AVAILABLE_LANGUAGES, MIGAKU_EXTENSION_ID


class LanguageSwitchError(Exception):
    """Raised when the language switch fails."""


def _exec_js(js: str) -> str | None:
    """Execute JavaScript on the Migaku extension tab in Chrome."""
    # Escape backslashes and double quotes for AppleScript string embedding
    escaped = js.replace("\\", "\\\\").replace('"', '\\"')
    try:
        return applescript(f'''
tell application "Google Chrome"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "{MIGAKU_EXTENSION_ID}" then
                return execute t javascript "{escaped}"
            end if
        end repeat
    end repeat
    error "Migaku extension tab not found in Chrome"
end tell
''')
    except AppleScriptError as e:
        if "JavaScript through AppleScript is turned off" in str(e):
            raise LanguageSwitchError(
                "In Chrome, enable View > Developer > 'Allow JavaScript from Apple Events'."
            ) from e
        raise


def run(language: str = "German") -> None:
    """Switch Migaku to the given language. Raises LanguageSwitchError on failure."""
    if language not in AVAILABLE_LANGUAGES:
        raise LanguageSwitchError(
            f"'{language}' is not available. Choose from: {', '.join(AVAILABLE_LANGUAGES)}"
        )

    try:
        # Navigate to language selection if not already there
        page = _exec_js("window.location.hash")
        if page != "#/language-select":
            result = _exec_js(
                "document.querySelector('.LangSelectButton')"
                " ? (document.querySelector('.LangSelectButton').click(), 'clicked')"
                " : (window.location.hash = '#/language-select', 'navigated')"
            )
            print(f"Opened language selector ({result})")
            time.sleep(2)

        # Click the target language
        result = _exec_js(
            "var btns = document.querySelectorAll('button');"
            " var result = 'not found';"
            " for (var i = 0; i < btns.length; i++) {"
            "   var p = btns[i].querySelector('p');"
            f"  if (p && p.textContent === '{language}') {{"
            "     btns[i].click(); result = 'clicked'; break;"
            "   }"
            " } result"
        )
        if result != "clicked":
            raise LanguageSwitchError(f"Language '{language}': {result}")

        time.sleep(5)
        print(f"Switched to {language}")

    except LanguageSwitchError:
        raise
    except Exception as e:
        raise LanguageSwitchError(str(e)) from e


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "German"
    run(target)

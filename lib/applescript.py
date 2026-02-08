"""NSAppleScript wrapper — replaces all subprocess osascript calls."""

import Foundation


class AppleScriptError(Exception):
    """Raised when an AppleScript fails to execute."""

    def __init__(self, message: str, error_number: int | None = None):
        super().__init__(message)
        self.error_number = error_number


def run(source: str) -> str | None:
    """Execute AppleScript and return the string result, or None if no result."""
    script = Foundation.NSAppleScript.alloc().initWithSource_(source)
    result, error = script.executeAndReturnError_(None)
    if error is not None:
        number = error.get("NSAppleScriptErrorNumber")
        message = error.get("NSAppleScriptErrorBriefMessage", str(error))
        raise AppleScriptError(message, error_number=number)
    if result is None:
        return None
    return result.stringValue()


def run_int(source: str) -> int:
    """Execute AppleScript and return an integer result."""
    value = run(source)
    if value is None:
        raise AppleScriptError("Expected integer result, got nothing")
    return int(value)

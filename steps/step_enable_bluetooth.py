#!/usr/bin/env python3
"""Enable Bluetooth if it's off (needed for Samsung TV audio)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import Foundation


def run() -> None:
    """Enable Bluetooth if currently off."""
    # IOBluetooth framework aborts in Python CLI processes (macOS Sequoia
    # security restriction). Run via osascript in a separate process using
    # NSTask (Cocoa API, not subprocess).
    pipe = Foundation.NSPipe.pipe()
    err_pipe = Foundation.NSPipe.pipe()
    task = Foundation.NSTask.alloc().init()
    task.setLaunchPath_("/usr/bin/osascript")
    task.setArguments_(["-e", _APPLESCRIPT])
    task.setStandardOutput_(pipe)
    task.setStandardError_(err_pipe)
    task.launch()
    task.waitUntilExit()

    data = pipe.fileHandleForReading().readDataToEndOfFile()
    output = Foundation.NSString.alloc().initWithData_encoding_(data, 4)  # UTF-8
    if output:
        print(str(output).strip())


_APPLESCRIPT = """\
use framework "IOBluetooth"
set controller to current application's IOBluetoothHostController's defaultController()
set state to controller's powerState() as integer
if state is 1 then
    return "Bluetooth already on"
else
    controller's setPowerState:1
    return "Bluetooth enabled"
end if
"""


if __name__ == "__main__":
    run()

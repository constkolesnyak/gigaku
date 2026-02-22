#!/usr/bin/env python3
"""Dim the built-in display brightness to 0 via DisplayServices."""

import ctypes
import ctypes.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# DisplayServices private framework (Apple Silicon + modern macOS)
_ds = ctypes.cdll.LoadLibrary(
    "/System/Library/PrivateFrameworks/DisplayServices.framework/DisplayServices"
)
_ds.DisplayServicesGetBrightness.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
_ds.DisplayServicesGetBrightness.restype = ctypes.c_int
_ds.DisplayServicesSetBrightness.argtypes = [ctypes.c_uint32, ctypes.c_float]
_ds.DisplayServicesSetBrightness.restype = ctypes.c_int

# CoreGraphics for display ID
_cg = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreGraphics"))
_cg.CGMainDisplayID.restype = ctypes.c_uint32


def run() -> None:
    """Set built-in display brightness to 0."""
    display_id = _cg.CGMainDisplayID()
    brightness = ctypes.c_float()
    err = _ds.DisplayServicesGetBrightness(display_id, ctypes.byref(brightness))
    if err != 0:
        print(f"Cannot read brightness for display {display_id} (err={err})")
        return
    _ds.DisplayServicesSetBrightness(display_id, ctypes.c_float(0.0))
    print("Main display brightness \u2192 0")


if __name__ == "__main__":
    run()

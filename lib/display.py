"""CoreGraphics display detection — replaces subprocess system_profiler."""

from dataclasses import dataclass

from Quartz.CoreGraphics import (
    CGDisplayBounds,
    CGDisplayIsBuiltin,
    CGDisplayVendorNumber,
    CGGetActiveDisplayList,
)

from lib.config import SAMSUNG_VENDOR_IDS


@dataclass(frozen=True)
class DisplayInfo:
    display_id: int
    x: int
    y: int
    width: int
    height: int
    vendor: int
    builtin: bool

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)


def list_displays() -> list[DisplayInfo]:
    """Return info for all active displays."""
    err, display_ids, count = CGGetActiveDisplayList(16, None, None)
    if err != 0:
        return []
    displays = []
    for did in display_ids[:count]:
        bounds = CGDisplayBounds(did)
        displays.append(DisplayInfo(
            display_id=did,
            x=int(bounds.origin.x),
            y=int(bounds.origin.y),
            width=int(bounds.size.width),
            height=int(bounds.size.height),
            vendor=CGDisplayVendorNumber(did),
            builtin=bool(CGDisplayIsBuiltin(did)),
        ))
    return displays


def find_samsung_display() -> DisplayInfo | None:
    """Find a Samsung external display, or None if not connected."""
    for d in list_displays():
        if not d.builtin and d.vendor in SAMSUNG_VENDOR_IDS:
            return d
    return None

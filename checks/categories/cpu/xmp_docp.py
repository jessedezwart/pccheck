from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_xmp_docp() -> CheckResult:
    """XMP/DOCP/EXPO enables your RAM to run at its rated speed.
    Without it, RAM defaults to a lower JEDEC base speed."""
    # Collect (rated, configured) pairs per DIMM.
    # Speed              = rated/max speed from SPD (reflects XMP if present)
    # ConfiguredClockSpeed = what the BIOS actually set
    pairs: list[tuple[int, int]] = []

    rows = wmi_query("Win32_PhysicalMemory", props=["Speed", "ConfiguredClockSpeed"])
    for row in rows:
        rated = row.get("Speed")
        configured = row.get("ConfiguredClockSpeed") or rated
        if rated:
            try:
                pairs.append((int(rated), int(configured)))
            except (ValueError, TypeError):
                pass

    if pairs:
        min_rated = min(r for r, _ in pairs)
        min_configured = min(c for _, c in pairs)
        if min_configured < min_rated:
            return CheckResult(
                "XMP / DOCP / EXPO",
                Status.WARNING,
                f"{min_configured} MT/s (rated {min_rated} MT/s)",
                "RAM is running below its rated speed. Enable XMP/DOCP/EXPO in BIOS.",
            )
        return CheckResult(
            "XMP / DOCP / EXPO",
            Status.GOOD,
            f"{min_configured} MT/s (at rated speed)",
        )

    # Fallback: wmic gives configured speed only — no rated comparison possible.
    speeds: list[int] = []
    out = run_cmd("wmic memorychip get ConfiguredClockSpeed /format:list")
    for m in re.findall(r"ConfiguredClockSpeed=(\d+)", out):
        speeds.append(int(m))

    if not speeds:
        return CheckResult("XMP / DOCP / EXPO", Status.UNKNOWN, "Cannot read RAM speed")

    current = min(speeds)
    return CheckResult(
        "XMP / DOCP / EXPO",
        Status.INFO,
        f"{current} MT/s",
        "Verify BIOS has XMP/DOCP/EXPO enabled. Compare to your RAM's rated speed on the label.",
    )


def run_check() -> CheckResult:
    return check_xmp_docp()

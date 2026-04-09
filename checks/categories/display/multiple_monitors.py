from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_multiple_monitors() -> CheckResult:
    """Each active monitor requires DWM to composite its output, consuming GPU
    resources. Disabling secondary monitors while gaming frees GPU bandwidth."""
    rows = wmi_query(
        "Win32_DesktopMonitor",
        props=["DeviceID", "Name", "ScreenWidth", "ScreenHeight"],
    )
    # Filter out disconnected/null entries
    active = [r for r in rows if r.get("ScreenWidth") or r.get("Name")]

    # Cross-check with Win32_VideoController connected outputs
    adapters = wmi_query(
        "Win32_VideoController",
        props=["Name", "CurrentHorizontalResolution", "CurrentVerticalResolution"],
    )
    active_adapters = [
        a
        for a in adapters
        if a.get("CurrentHorizontalResolution") and "Microsoft" not in (a.get("Name") or "")
    ]

    # Use the powershell Get-DisplayResolution if available for accuracy
    ps_out = run_powershell(
        "Get-WmiObject -Class Win32_DesktopMonitor | "
        "Where-Object { $_.ScreenWidth } | "
        "Measure-Object | Select-Object -ExpandProperty Count"
    )
    count_str = ps_out.strip()
    try:
        count = int(count_str)
    except (ValueError, TypeError):
        count = len(active) or len(active_adapters)

    if count <= 1:
        return CheckResult(
            "Multiple Monitors",
            Status.GOOD,
            f"{count or 1} active monitor",
        )
    return CheckResult(
        "Multiple Monitors",
        Status.INFO,
        f"{count} monitors active",
        f"Having {count} monitors active consumes extra GPU resources for composition. "
        "Disable unused monitors in Display Settings > Multiple Displays > Disconnect before competitive gaming.",
    )


IMPACT_EXPLANATION = "Likely low-to-moderate impact: additional active displays increase composition workload and can affect frame-time consistency in edge cases. Source: https://learn.microsoft.com/en-us/windows/win32/w8cookbook/desktop-window-manager-is-always-on"


def run_check() -> CheckResult:
    return check_multiple_monitors()

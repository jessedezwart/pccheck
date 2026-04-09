from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_windows_version() -> CheckResult:
    """Windows 10 22H2 and Windows 11 23H2+ have gaming improvements.
    Older builds miss latency fixes, HAGS enhancements, and DirectStorage."""
    ver = platform.version()  # e.g. '10.0.22621'
    build_str = platform.version().split(".")[-1] if "." in ver else "0"
    edition = run_powershell("(Get-WmiObject Win32_OperatingSystem).Caption")
    run_powershell("(Get-WmiObject Win32_OperatingSystem).Version")
    try:
        build = int(build_str)
    except ValueError:
        build = 0

    display = f"{edition or 'Windows'}  (build {build})"

    if build >= 22621:  # Win11 22H2+
        return CheckResult("Windows Version", Status.GOOD, display)
    if build >= 19044:  # Win10 21H2+
        return CheckResult(
            "Windows Version",
            Status.INFO,
            display,
            "Windows 11 23H2 adds Auto HDR, DirectStorage 1.2, and better HAGS. "
            "Consider upgrading if hardware supports it.",
        )
    return CheckResult(
        "Windows Version",
        Status.WARNING,
        display,
        "Outdated Windows build. Update via Settings > Windows Update for gaming improvements.",
    )


IMPACT_EXPLANATION = "Likely low-to-moderate impact over time: newer Windows builds frequently include graphics scheduler, driver model, and gaming stack updates. Source: https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information"


def run_check() -> CheckResult:
    return check_windows_version()

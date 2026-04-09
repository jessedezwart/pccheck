from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_sysmain() -> CheckResult:
    """SysMain (Superfetch) preloads frequently used apps into RAM.
    On fast NVMe SSDs it wastes RAM and can cause disk activity during gaming."""
    try:
        svc = psutil.win_service_get("SysMain")
        status_str = svc.status()
        if status_str == "running":
            return CheckResult(
                "SysMain / Superfetch",
                Status.INFO,
                "Running",
                "On NVMe SSDs, SysMain provides little benefit. Disable: "
                "services.msc > SysMain > Startup type = Disabled.",
            )
        return CheckResult(
            "SysMain / Superfetch",
            Status.GOOD,
            f"Not running ({status_str})",
        )
    except Exception:
        return CheckResult(
            "SysMain / Superfetch",
            Status.UNKNOWN,
            "Could not read service status",
        )


IMPACT_EXPLANATION = "Likely low impact on average FPS, but background caching activity can affect storage contention and stutter on some systems. Source: https://learn.microsoft.com/en-us/windows/win32/fileio/file-caching"


def run_check() -> CheckResult:
    return check_sysmain()

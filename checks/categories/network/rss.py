from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_rss() -> CheckResult:
    """Receive Side Scaling distributes network interrupt processing across
    multiple CPU cores, reducing NIC bottlenecks on fast connections."""
    # Per-adapter registry check
    nics = _physical_nics()
    disabled_nics: list[str] = []
    enabled_nics: list[str] = []

    for desc, path in nics[:4]:
        val = reg_hklm(path, "*RSS")
        if val == "0":
            disabled_nics.append(desc)
        elif val == "1":
            enabled_nics.append(desc)
        else:
            enabled_nics.append(f"{desc} (default)")

    if disabled_nics:
        return CheckResult(
            "Receive Side Scaling (RSS)",
            Status.WARNING,
            f"Disabled on: {', '.join(disabled_nics[:2])}",
            "Enable in Device Manager > NIC > Properties > Advanced > "
            "Receive Side Scaling = Enabled.",
        )
    if enabled_nics:
        return CheckResult(
            "Receive Side Scaling (RSS)",
            Status.GOOD,
            f"Enabled: {', '.join(enabled_nics[:2])}",
        )

    # PowerShell fallback
    ps_out = run_powershell(
        "Get-NetAdapterRss -ErrorAction SilentlyContinue | "
        "Select-Object Name, Enabled | ConvertTo-Json"
    )
    if ps_out:
        return CheckResult(
            "Receive Side Scaling (RSS)", Status.INFO, "See Get-NetAdapterRss output"
        )

    return CheckResult(
        "Receive Side Scaling (RSS)",
        Status.UNKNOWN,
        "Could not detect NIC RSS settings",
        "Check via PowerShell: Get-NetAdapterRss",
    )


def run_check() -> CheckResult:
    return check_rss()

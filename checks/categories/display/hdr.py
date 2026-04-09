from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_hdr() -> CheckResult:
    """HDR adds tone-mapping processing and can slightly increase input latency
    or cause colour shift in SDR games. Many gamers disable it while gaming."""
    # Primary path: query per-monitor advanced color state from WMI.
    # This is more reliable than legacy registry flags on modern Windows builds.
    ps = (
        "Get-CimInstance -Namespace root\\wmi "
        "-ClassName WmiMonitorAdvancedColorInformation "
        "-ErrorAction SilentlyContinue | "
        "Select-Object Active, AdvancedColorEnabled, AdvancedColorSupported | "
        "ConvertTo-Json"
    )
    out = run_powershell(ps)

    if out:
        try:
            data = json.loads(out)
            rows = data if isinstance(data, list) else [data]

            active_rows = [r for r in rows if bool(r.get("Active"))]
            enabled_active = [r for r in active_rows if bool(r.get("AdvancedColorEnabled"))]

            if enabled_active:
                return CheckResult(
                    "HDR",
                    Status.INFO,
                    f"Enabled ({len(enabled_active)} active HDR display{'s' if len(enabled_active) != 1 else ''})",
                    "HDR adds tone-mapping overhead and can shift SDR game colours. "
                    "Disable in Settings > Display > HDR if you don't need it for gaming.",
                )

            if active_rows:
                return CheckResult("HDR", Status.GOOD, "Disabled")
        except Exception:
            pass

    # Fallback: legacy registry values (can be stale/inaccurate on some systems).
    hdr_val = reg_hkcu(
        r"Software\Microsoft\Windows\CurrentVersion\VideoSettings",
        "EnableHDROutput",
    )
    hdr_val2 = reg_hkcu(
        r"Software\Microsoft\Windows\CurrentVersion\VideoSettings",
        "UseHDR",
    )

    enabled = hdr_val == 1 or hdr_val2 == 1

    if enabled:
        return CheckResult(
            "HDR",
            Status.INFO,
            "Enabled",
            "HDR adds tone-mapping overhead and can shift SDR game colours. "
            "Disable in Settings > Display > HDR if you don't need it for gaming.",
        )

    return CheckResult("HDR", Status.GOOD, "Disabled")


IMPACT_EXPLANATION = "Likely low-to-moderate impact: HDR tone mapping and composition paths can affect latency and consistency depending on game and display pipeline. Source: https://learn.microsoft.com/en-us/windows/win32/direct3darticles/high-dynamic-range"


def run_check() -> CheckResult:
    return check_hdr()

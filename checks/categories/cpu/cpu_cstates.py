from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_cpu_cstates() -> CheckResult:
    """C-states let the CPU enter low-power idle states between tasks."""
    plan = get_active_plan_guid()
    if not plan:
        return CheckResult("CPU C-States", Status.UNKNOWN, "Cannot read power plan")

    # Primary modern setting: IDLEDISABLE (0 = idle states enabled, 1 = disabled).
    value = read_power_setting(plan, _PROC_SUBGROUP, _CSTATES_GUID)
    if value is not None:
        if value == 1:
            return CheckResult("CPU C-States", Status.GOOD, "Disabled (IDLEDISABLE=1)")
        if value == 0:
            return CheckResult(
                "CPU C-States",
                Status.INFO,
                "Enabled (IDLEDISABLE=0)",
                "Disable in BIOS for lowest latency if you are tuning for competitive gaming.",
            )
        return CheckResult(
            "CPU C-States",
            Status.INFO,
            f"Policy value {value}",
            "Check BIOS/UEFI CPU power-management settings for full C-state control.",
        )

    # Legacy setting fallback used by some systems/plans.
    legacy_value = read_power_setting(plan, _PROC_SUBGROUP, _CSTATES_LEGACY_GUID)
    if legacy_value is None:
        return CheckResult(
            "CPU C-States",
            Status.INFO,
            "Setting not exposed in active power plan",
            "Check BIOS for C-state settings (typically under CPU > Power Management).",
        )
    if legacy_value == 0:
        return CheckResult("CPU C-States", Status.GOOD, "Disabled")
    if legacy_value == 1:
        return CheckResult(
            "CPU C-States",
            Status.INFO,
            "C1 only",
            "Shallow sleep only. Disable entirely in BIOS for the lowest latency.",
        )
    return CheckResult(
        "CPU C-States",
        Status.INFO,
        f"Enabled (legacy value {legacy_value})",
        "C-states save power but can introduce latency spikes. Disable in BIOS for competitive gaming.",
    )


def run_check() -> CheckResult:
    return check_cpu_cstates()

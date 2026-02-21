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
            return CheckResult(
                "CPU C-States",
                Status.GOOD,
                "Windows policy: disabled (IDLEDISABLE=1)",
            )
        if value == 0:
            return CheckResult(
                "CPU C-States",
                Status.INFO,
                "Windows policy: enabled (IDLEDISABLE=0)",
                "This reflects Windows power-plan policy only; BIOS/UEFI can still force C-states off. "
                "For lowest latency tuning, disable C-states in BIOS/UEFI.",
            )
        return CheckResult(
            "CPU C-States",
            Status.INFO,
            f"Windows policy value: {value}",
            "Windows policy is non-standard here. Check BIOS/UEFI CPU power-management "
            "settings for effective C-state behavior.",
        )

    # Legacy setting fallback used by some systems/plans.
    legacy_value = read_power_setting(plan, _PROC_SUBGROUP, _CSTATES_LEGACY_GUID)
    if legacy_value is None:
        return CheckResult(
            "CPU C-States",
            Status.INFO,
            "Windows policy setting not exposed in active power plan",
            "Check BIOS/UEFI for C-state settings (typically under CPU > Power Management).",
        )
    if legacy_value == 0:
        return CheckResult("CPU C-States", Status.GOOD, "Windows legacy policy: disabled")
    if legacy_value == 1:
        return CheckResult(
            "CPU C-States",
            Status.INFO,
            "Windows legacy policy: C1 only",
            "This may still be overridden by BIOS/UEFI. Disable entirely in BIOS for lowest latency.",
        )
    return CheckResult(
        "CPU C-States",
        Status.INFO,
        f"Windows legacy policy: enabled (value {legacy_value})",
        "This may still be overridden by BIOS/UEFI. Disable C-states in BIOS for competitive gaming.",
    )


def run_check() -> CheckResult:
    return check_cpu_cstates()

from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_core_parking() -> CheckResult:
    """Core parking suspends CPU cores to save power, adding latency.
    For gaming, set minimum unparked cores to 100%."""
    plan = get_active_plan_guid()
    if not plan:
        return CheckResult(
            "Core Parking",
            Status.UNKNOWN,
            "Cannot read active power plan",
            "Run as Administrator or check power settings manually.",
        )

    value = read_power_setting(plan, _PROC_SUBGROUP, _CORE_PARKING_GUID)
    if value is None:
        return CheckResult(
            "Core Parking",
            Status.INFO,
            "Setting not exposed in active power plan",
            "Verify via `powercfg /qh SCHEME_CURRENT SUB_PROCESSOR CPMINCORES` or ParkControl.",
        )

    # This setting is "minimum unparked cores" (higher is less parking).
    if value >= 100:
        return CheckResult("Core Parking", Status.GOOD, "Disabled (100% unparked)")
    if value >= 90:
        return CheckResult("Core Parking", Status.GOOD, f"Nearly disabled ({value}% unparked)")
    if value >= 50:
        return CheckResult(
            "Core Parking",
            Status.WARNING,
            f"{value}% minimum unparked cores",
            "Set core parking minimum cores to 100% in power plan advanced settings or ParkControl.",
        )
    return CheckResult(
        "Core Parking",
        Status.BAD,
        f"{value}% minimum unparked cores",
        "Core parking is aggressive. Set minimum unparked cores to 100% for lowest latency.",
    )


IMPACT_EXPLANATION = "Likely moderate-to-high impact on 1% lows: aggressive core parking can increase scheduling latency and frame-time variance. Source: https://learn.microsoft.com/en-us/windows-hardware/customize/power-settings/static-configuration-options-for-the-performance-state-engine"


def run_check() -> CheckResult:
    return check_core_parking()

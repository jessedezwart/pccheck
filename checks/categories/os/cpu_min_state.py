from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_cpu_min_state() -> CheckResult:
    """Minimum processor state controls idle clock floor."""
    plan = get_active_plan_guid()
    if not plan:
        return CheckResult("CPU Min Processor State", Status.UNKNOWN, "Cannot read power plan")

    val = read_power_setting(plan, _PROC_SUBGROUP, _MIN_PROC_STATE_GUID)
    if val is None:
        return CheckResult(
            "CPU Min Processor State",
            Status.INFO,
            "Setting not exposed in active power plan",
            "Verify via `powercfg /qh SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMIN`.",
        )
    if val == 100:
        return CheckResult("CPU Min Processor State", Status.GOOD, "100% (always max clock)")
    if val >= 50:
        return CheckResult(
            "CPU Min Processor State",
            Status.INFO,
            f"{val}%",
            "Set to 100% to prevent idle clock dips during short gaming bursts.",
        )
    return CheckResult(
        "CPU Min Processor State",
        Status.WARNING,
        f"{val}%",
        f"CPU can idle at {val}% of max frequency - latency spikes possible. "
        "Set to 100% in power plan advanced settings.",
    )


def run_check() -> CheckResult:
    return check_cpu_min_state()

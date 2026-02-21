from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_cpu_boost() -> CheckResult:
    """Max processor state should be 100% so the CPU can boost freely.
    Capping at 99% can disable Turbo/Boost on some systems."""
    plan = get_active_plan_guid()
    if not plan:
        return CheckResult("CPU Max Processor State", Status.UNKNOWN, "Cannot read power plan")

    max_state = read_power_setting(plan, _PROC_SUBGROUP, _MAX_PROC_STATE_GUID)
    min_state = read_power_setting(plan, _PROC_SUBGROUP, _MIN_PROC_STATE_GUID)

    if max_state is None:
        return CheckResult(
            "CPU Max Processor State",
            Status.INFO,
            "Setting not exposed in active power plan",
            "Verify via `powercfg /qh SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX`.",
        )

    value_str = f"Max {max_state}%  /  Min {min_state if min_state is not None else '?'}%"

    if max_state < 100:
        return CheckResult(
            "CPU Max Processor State",
            Status.BAD,
            value_str,
            f"Max state is {max_state}% - CPU cannot reach full Turbo/Boost frequency. "
            "Set to 100% in power plan advanced settings.",
        )
    if min_state is not None and min_state < 100:
        return CheckResult(
            "CPU Max Processor State",
            Status.INFO,
            value_str,
            "Min processor state < 100% allows idle frequency scaling (fine for desktop). "
            "Set to 100% only if you need absolute minimum latency.",
        )
    return CheckResult("CPU Max Processor State", Status.GOOD, value_str)


def run_check() -> CheckResult:
    return check_cpu_boost()

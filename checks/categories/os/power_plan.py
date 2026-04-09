from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_power_plan() -> CheckResult:
    """High Performance or Ultimate Performance prevents CPU/GPU clock scaling
    that causes frame-time variance. Balanced is bad for competitive gaming."""
    out = run_cmd("powercfg /getactivescheme", timeout=8)
    m = re.search(
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
        out,
        re.IGNORECASE,
    )
    if not m:
        return CheckResult(
            "Power Plan",
            Status.UNKNOWN,
            "Could not read active power plan",
            "Run: powercfg /getactivescheme in Command Prompt.",
        )
    guid = m.group(1).lower()
    # Try to get the friendly name from the powercfg output
    name_match = re.search(r"\((.+?)\)", out)
    name = name_match.group(1) if name_match else _PLAN_NAMES.get(guid, guid)

    if guid == _PLAN_ULTIMATE:
        return CheckResult("Power Plan", Status.GOOD, f"Ultimate Performance ({guid[:8]}…)")
    if guid == _PLAN_HIGH_PERF:
        return CheckResult("Power Plan", Status.GOOD, "High Performance")
    if guid == _PLAN_POWER_SAVE:
        return CheckResult(
            "Power Plan",
            Status.BAD,
            "Power Saver — severely limits performance",
            "Switch to High Performance or Ultimate Performance in Control Panel > Power Options.",
        )
    # Balanced or unknown custom plan
    return CheckResult(
        "Power Plan",
        Status.WARNING,
        f"Balanced / {name}",
        "Switch to High Performance or Ultimate Performance for gaming. "
        "Enable Ultimate: powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61",
    )


IMPACT_EXPLANATION = "Likely moderate impact: power-plan processor policy can materially affect boost behavior and consistency in CPU-limited games. Source: https://learn.microsoft.com/en-us/windows-hardware/customize/power-settings/static-configuration-options-for-the-performance-state-engine"


def run_check() -> CheckResult:
    return check_power_plan()

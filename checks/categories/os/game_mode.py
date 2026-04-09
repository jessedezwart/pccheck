from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_game_mode() -> CheckResult:
    """Windows Game Mode prioritizes CPU/GPU resources for the foreground game
    and suppresses Windows Update restarts during gaming."""
    val = reg_hkcu(
        r"Software\Microsoft\GameBar",
        "AutoGameModeEnabled",
    )
    # 1 = enabled (default since Win10 1809), 0 = disabled
    if val == 0:
        return CheckResult(
            "Game Mode",
            Status.WARNING,
            "Disabled",
            "Enable in Settings > Gaming > Game Mode for better resource prioritization.",
        )
    return CheckResult("Game Mode", Status.GOOD, "Enabled (default)")


IMPACT_EXPLANATION = "Likely low-to-moderate impact depending on workload contention: scheduler prioritization can improve consistency when background activity exists. Source: https://learn.microsoft.com/en-us/windows/win32/procthread/multimedia-class-scheduler-service"


def run_check() -> CheckResult:
    return check_game_mode()

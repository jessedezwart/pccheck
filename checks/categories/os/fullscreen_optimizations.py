from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_fullscreen_optimizations() -> CheckResult:
    """Fullscreen Optimizations allow Windows to optimize fullscreen games,
    enabling features like Alt+Tab and per-game optimizations. FSE (exclusive
    fullscreen) is often faster; optimizations can add input lag in some games."""
    # GameDVR_FSEBehaviorMode:
    #   0 = let Windows decide (default)
    #   1 = force FSO (fullscreen optimizations)
    #   2 = force FSE (exclusive — disables DWM, lower latency)
    val = reg_hkcu(
        r"System\GameConfigStore",
        "GameDVR_FSEBehaviorMode",
    )
    reg_hkcu(
        r"System\GameConfigStore",
        "GameDVR_DXGIHonorFSEWindowsCompatible",
    )
    if val == 2:
        return CheckResult(
            "Fullscreen Optimizations",
            Status.INFO,
            "Forced FSE (Exclusive Fullscreen)",
            "Exclusive fullscreen can lower latency but may break Alt+Tab. Test per-game.",
        )
    if val == 0 or val is None:
        return CheckResult(
            "Fullscreen Optimizations",
            Status.GOOD,
            "Default (Windows decides per app)",
        )
    return CheckResult(
        "Fullscreen Optimizations",
        Status.INFO,
        f"FSO mode forced (GameDVR_FSEBehaviorMode={val})",
        "If games stutter, try disabling 'Fullscreen optimizations' on the game .exe > Compatibility tab.",
    )


IMPACT_EXPLANATION = "Likely low-to-moderate, game-dependent impact: presentation/composition mode can influence latency and smoothness. Source: https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/dxgi-flip-model"


def run_check() -> CheckResult:
    return check_fullscreen_optimizations()

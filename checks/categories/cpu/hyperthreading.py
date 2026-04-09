from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_hyperthreading() -> CheckResult:
    """Hyperthreading/SMT doubles logical cores. Most modern games benefit
    from it being ON, but a few titles prefer it OFF for lower variance."""
    logical = psutil.cpu_count(logical=True)
    physical = psutil.cpu_count(logical=False)
    if logical is None or physical is None:
        return CheckResult("Hyperthreading / SMT", Status.UNKNOWN, "Could not detect")
    if logical > physical:
        return CheckResult(
            "Hyperthreading / SMT",
            Status.GOOD,
            f"Enabled ({physical} cores → {logical} threads)",
            "Generally beneficial for gaming. Some competitive titles perform better with HT off — test per-game.",
        )
    return CheckResult(
        "Hyperthreading / SMT",
        Status.INFO,
        f"Disabled / not supported ({physical} cores)",
        "Disabling HT reduces thread count. Re-enable in BIOS if you need it for productivity tasks.",
    )


IMPACT_EXPLANATION = "Likely moderate, game-dependent impact: SMT/Hyperthreading affects thread scheduling and can improve or sometimes reduce consistency depending on title and CPU. Source: https://en.wikipedia.org/wiki/Simultaneous_multithreading"


def run_check() -> CheckResult:
    return check_hyperthreading()

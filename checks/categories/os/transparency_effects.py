from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_transparency_effects() -> CheckResult:
    """Transparency effects require continuous GPU compositing.
    Disabling them reduces GPU Desktop Window Manager (DWM) overhead."""
    val = reg_hkcu(
        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        "EnableTransparency",
    )
    if val == 0:
        return CheckResult("Transparency Effects", Status.GOOD, "Disabled")
    if val == 1 or val is None:
        return CheckResult(
            "Transparency Effects",
            Status.INFO,
            "Enabled",
            "Disable in Settings > Personalization > Colors > Transparency effects = Off "
            "to slightly reduce DWM GPU usage.",
        )
    return CheckResult("Transparency Effects", Status.UNKNOWN, f"Value = {val}")


def run_check() -> CheckResult:
    return check_transparency_effects()

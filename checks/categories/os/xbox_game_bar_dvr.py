from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_xbox_game_bar_dvr() -> CheckResult:
    """Xbox Game Bar background recording (DVR) continuously encodes video
    using your GPU encoder, reducing available encode capacity and GPU headroom."""
    # AppCaptureEnabled = 1 means Game DVR background recording is on
    dvr = reg_hkcu(
        r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
        "AppCaptureEnabled",
    )
    reg_hkcu(
        r"Software\Microsoft\GameBar",
        "UseNexusForGameBarEnabled",
    )
    if dvr == 1:
        return CheckResult(
            "Xbox DVR / Game Bar Recording",
            Status.WARNING,
            "Background recording is ON",
            "Disable: Settings > Gaming > Xbox Game Bar > turn off background recording, "
            "or Settings > Gaming > Captures > Record in background = Off.",
        )
    if dvr == 0:
        return CheckResult(
            "Xbox DVR / Game Bar Recording", Status.GOOD, "Background recording disabled"
        )
    return CheckResult(
        "Xbox DVR / Game Bar Recording",
        Status.GOOD,
        "Not explicitly enabled (default off)",
    )


IMPACT_EXPLANATION = "Likely moderate impact when background recording is enabled: real-time capture uses encoder/GPU resources and can reduce headroom. Source: https://support.xbox.com/en-US/help/games-apps/game-setup-and-play/how-to-record-with-game-bar"


def run_check() -> CheckResult:
    return check_xbox_game_bar_dvr()

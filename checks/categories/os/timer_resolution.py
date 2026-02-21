from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_timer_resolution() -> CheckResult:
    """Windows default timer resolution is 15.6 ms — too coarse for smooth gaming.
    Games and tools (RTSS, ISLC) request 0.5-1 ms for accurate frame timing."""
    try:
        ntdll = ctypes.WinDLL("ntdll")
        minimum = ctypes.c_ulong()
        maximum = ctypes.c_ulong()
        current = ctypes.c_ulong()
        ret = ntdll.NtQueryTimerResolution(
            ctypes.byref(minimum),
            ctypes.byref(maximum),
            ctypes.byref(current),
        )
        if ret != 0:
            raise OSError(f"NtQueryTimerResolution returned {ret}")

        # Values are in 100-nanosecond units
        cur_ms = current.value / 10_000.0
        min_ms = minimum.value / 10_000.0  # worst (largest interval)
        max_ms = maximum.value / 10_000.0  # best (smallest interval)

        value_str = f"{cur_ms:.2f} ms  (range {max_ms:.2f} – {min_ms:.2f} ms)"

        if cur_ms <= 1.0:
            return CheckResult("Timer Resolution", Status.GOOD, value_str)
        if cur_ms <= 5.0:
            return CheckResult(
                "Timer Resolution",
                Status.WARNING,
                value_str,
                "Timer is above 1 ms. A game or tool may not be requesting high res. "
                "ISLC or Intelligent Standby List Cleaner can set 0.5 ms globally.",
            )
        return CheckResult(
            "Timer Resolution",
            Status.BAD,
            value_str,
            "Running at Windows default 15.6 ms. Launch your game (which usually sets 1 ms) "
            "or use ISLC to globally lock at 0.5 ms for smoother frame pacing.",
        )
    except Exception as e:
        return CheckResult("Timer Resolution", Status.UNKNOWN, f"Error: {e}")


def run_check() -> CheckResult:
    return check_timer_resolution()

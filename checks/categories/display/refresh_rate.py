from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_refresh_rate() -> CheckResult:
    """Running below your monitor's maximum refresh rate is a simple oversight
    that is easy to fix. Many monitors default to 60 Hz even when capable of more."""
    primary_refresh = _get_primary_display_refresh()
    if primary_refresh is not None:
        current, maximum = primary_refresh
        if current < maximum:
            return CheckResult(
                "Refresh Rate",
                Status.BAD,
                f"Primary monitor: {current} Hz (max {maximum} Hz)",
                "Set refresh rate: Display Settings > Advanced Display Settings > "
                "Choose a refresh rate (select your maximum).",
            )
        return CheckResult(
            "Refresh Rate",
            Status.GOOD,
            f"Primary monitor: {current} Hz (at maximum)",
        )

    rows = _get_display_adapters()
    if not rows:
        # WMI fallback
        out = run_cmd(
            "wmic path Win32_VideoController get "
            "CurrentRefreshRate,MaxRefreshRate,Name /format:list"
        )
        if not out:
            return CheckResult(
                "Refresh Rate",
                Status.UNKNOWN,
                "Could not read display info",
                "Check Display Settings > Advanced Display > Refresh Rate.",
            )
        # Parse wmic output
        rows = []
        block: dict = {}
        for line in out.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                block[k.strip()] = v.strip()
            elif not line.strip() and block:
                rows.append(block)
                block = {}
        if block:
            rows.append(block)

    # Only check the primary (first non-Microsoft) adapter
    row = next(
        (r for r in rows if "Microsoft" not in str(r.get("Name") or "")),
        None,
    )
    if row is None:
        return CheckResult(
            "Refresh Rate",
            Status.UNKNOWN,
            "No active display detected",
            "Check Display Settings > Advanced Display > Refresh Rate.",
        )

    name = str(row.get("Name") or "Monitor")
    try:
        current = int(row.get("CurrentRefreshRate") or 0)
        maximum = int(row.get("MaxRefreshRate") or current)
    except (ValueError, TypeError):
        return CheckResult(
            "Refresh Rate",
            Status.UNKNOWN,
            "Could not parse refresh rate",
            "Check Display Settings > Advanced Display > Refresh Rate.",
        )

    if current == 0:
        return CheckResult(
            "Refresh Rate",
            Status.UNKNOWN,
            "No active display detected",
            "Check Display Settings > Advanced Display > Refresh Rate.",
        )
    if current < maximum:
        return CheckResult(
            "Refresh Rate",
            Status.BAD,
            f"{name[:30]}: {current} Hz (max {maximum} Hz)",
            "Set refresh rate: Display Settings > Advanced Display Settings > "
            "Choose a refresh rate (select your maximum).",
        )
    return CheckResult(
        "Refresh Rate",
        Status.GOOD,
        f"{current} Hz (at maximum)",
    )


def run_check() -> CheckResult:
    return check_refresh_rate()

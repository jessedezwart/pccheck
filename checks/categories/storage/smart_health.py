from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def _collect_disk_status_rows() -> list[tuple[str, str]]:
    rows = wmi_query("Win32_DiskDrive", props=["Model", "Status"])
    pairs: list[tuple[str, str]] = []
    for row in rows:
        model = str(row.get("Model") or "").strip()
        status = str(row.get("Status") or "").strip()
        if model:
            pairs.append((model, status))
    return pairs


def check_smart_health() -> CheckResult:
    """S.M.A.R.T./health status from available Windows telemetry."""
    rows = _collect_disk_status_rows()
    if not rows:
        return CheckResult(
            "Drive Health (S.M.A.R.T.)",
            Status.INFO,
            "Disk health not exposed by current API path",
            "Use CrystalDiskInfo or vendor SSD tools for full SMART details (wear, pending sectors, error counts).",
        )

    bad_disks: list[str] = []
    ok_disks: list[str] = []
    unknown_disks: list[str] = []

    for model, status in rows:
        normalized = status.upper()
        if normalized in ("OK", "HEALTHY"):
            ok_disks.append(model)
        elif normalized == "PRED FAILURE":
            bad_disks.append(f"{model} (PRED FAILURE)")
        elif not normalized:
            unknown_disks.append(model)
        else:
            bad_disks.append(f"{model} ({status})")

    if bad_disks:
        return CheckResult(
            "Drive Health (S.M.A.R.T.)",
            Status.BAD,
            f"Issues: {', '.join(bad_disks[:3])}",
            "Back up data immediately and replace failing drives.",
        )

    if ok_disks:
        suffix = "..." if len(ok_disks) > 3 else ""
        return CheckResult(
            "Drive Health (S.M.A.R.T.)",
            Status.GOOD,
            f"OK ({', '.join(ok_disks[:3])}{suffix})",
        )

    return CheckResult(
        "Drive Health (S.M.A.R.T.)",
        Status.INFO,
        "Drive status not reported by WMI",
        "Use CrystalDiskInfo for detailed SMART telemetry.",
    )


IMPACT_EXPLANATION = "Likely low direct FPS impact, but degrading drive health can cause stalls, long loads, and severe streaming hitching. Source: https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-diskdrive"


def run_check() -> CheckResult:
    return check_smart_health()

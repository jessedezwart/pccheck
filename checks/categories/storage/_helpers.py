"""
Storage checks:
  - AHCI vs NVMe interface
  - Write caching enabled
  - Drive health via S.M.A.R.T.
  - Games installed on SSD vs HDD

To remove a check, delete or comment out its entry in get_checks().
"""

from __future__ import annotations

import json
import re

from checks.base import (
    CheckResult,
    Status,
    reg_hklm,
    run_cmd,
    run_powershell,
    wmi_query,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_disk_info() -> list[dict]:
    """Return list of physical disk dicts from WMI."""
    rows = wmi_query(
        "Win32_DiskDrive",
        props=["DeviceID", "MediaType", "InterfaceType", "Model", "Size", "Status", "Index"],
    )
    return rows or []


def _get_logical_to_physical() -> dict[str, int]:
    """Map logical disk letter to physical disk index via WMI."""
    # Simpler approach: use Get-PhysicalDisk + Get-StorageReliabilityCounter
    ps2 = "Get-Partition | Select-Object DriveLetter, DiskNumber | ConvertTo-Json"
    out = run_powershell(ps2)
    mapping: dict[str, int] = {}
    if out:
        try:
            data = json.loads(out)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                letter = item.get("DriveLetter") or item.get("DriveLetter ")
                idx = item.get("DiskNumber")
                if letter and idx is not None:
                    mapping[str(letter).strip().upper()] = int(idx)
        except Exception:
            pass
    return mapping


__all__ = [
    "annotations",
    "json",
    "re",
    "CheckResult",
    "Status",
    "reg_hklm",
    "run_cmd",
    "run_powershell",
    "wmi_query",
    "_get_disk_info",
    "_get_logical_to_physical",
]

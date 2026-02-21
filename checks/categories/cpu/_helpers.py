"""
CPU / System checks:
  - CPU core parking
  - Hyperthreading / SMT
  - Virtualization Based Security (VBS / HVCI)
  - Memory channel config (dual vs single)
  - XMP / DOCP enabled
  - CPU C-states
  - CPU boost / max processor state

To remove a check, delete or comment out its entry in get_checks().
"""

from __future__ import annotations

import re
from typing import Optional

import psutil

from checks.base import (
    _CORE_PARKING_GUID,
    _CSTATES_LEGACY_GUID,
    _CSTATES_GUID,
    _MAX_PROC_STATE_GUID,
    _MIN_PROC_STATE_GUID,
    _PROC_SUBGROUP,
    CheckResult,
    Status,
    get_active_plan_guid,
    read_power_setting,
    reg_hkcu,
    reg_hklm,
    run_cmd,
    run_powershell,
    wmi_query,
)

__all__ = [
    "annotations",
    "re",
    "Optional",
    "psutil",
    "CheckResult",
    "Status",
    "reg_hklm",
    "reg_hkcu",
    "run_cmd",
    "run_powershell",
    "wmi_query",
    "get_active_plan_guid",
    "read_power_setting",
    "_PROC_SUBGROUP",
    "_CORE_PARKING_GUID",
    "_MIN_PROC_STATE_GUID",
    "_MAX_PROC_STATE_GUID",
    "_CSTATES_GUID",
    "_CSTATES_LEGACY_GUID",
]

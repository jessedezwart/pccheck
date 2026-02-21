"""
OS / Windows checks:
  - Active power plan (High Performance / Ultimate Performance)
  - CPU minimum processor state
  - Game Mode enabled
  - Fullscreen optimizations (GameDVR_FSEBehaviorMode)
  - Windows visual effects setting
  - SysMain / Superfetch service
  - Xbox Game Bar / DVR background recording
  - Transparency effects
  - Search indexing (WSearch)
  - Timer resolution
  - Windows version / build
  - Background processes consuming significant CPU

To remove a check, delete or comment out its entry in get_checks().
"""

from __future__ import annotations

import ctypes
import platform
import re

import psutil

from checks.base import (
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
)

# Known power plan GUIDs
_PLAN_HIGH_PERF = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
_PLAN_BALANCED = "381b4222-f694-41f0-9685-ff5bb260df2e"
_PLAN_POWER_SAVE = "a1841308-3541-4fab-bc81-f71556f20b4a"
_PLAN_ULTIMATE = "e9a42b02-d5df-448d-aa00-03f14749eb61"

_PLAN_NAMES = {
    _PLAN_HIGH_PERF: "High Performance",
    _PLAN_BALANCED: "Balanced",
    _PLAN_POWER_SAVE: "Power Saver",
    _PLAN_ULTIMATE: "Ultimate Performance",
}

__all__ = [
    "annotations",
    "ctypes",
    "platform",
    "re",
    "psutil",
    "CheckResult",
    "Status",
    "reg_hklm",
    "reg_hkcu",
    "run_cmd",
    "run_powershell",
    "get_active_plan_guid",
    "read_power_setting",
    "_PROC_SUBGROUP",
    "_MIN_PROC_STATE_GUID",
    "_PLAN_HIGH_PERF",
    "_PLAN_BALANCED",
    "_PLAN_POWER_SAVE",
    "_PLAN_ULTIMATE",
    "_PLAN_NAMES",
]

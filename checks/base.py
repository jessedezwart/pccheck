"""
Shared utilities, data classes, and helper functions for all checks.
"""

from __future__ import annotations

import json
import re
import subprocess
import winreg
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Status(Enum):
    GOOD = "good"
    WARNING = "warning"
    BAD = "bad"
    INFO = "info"
    UNKNOWN = "unknown"
    ERROR = "error"


STATUS_ICON = {
    Status.GOOD: "✓",
    Status.WARNING: "⚠",
    Status.BAD: "✗",
    Status.INFO: "ℹ",
    Status.UNKNOWN: "?",
    Status.ERROR: "!",
}

UNKNOWN_TEXT_STYLE = "grey70"
DETAIL_TEXT_STYLE = "grey50"

STATUS_COLOR = {
    Status.GOOD: "green",
    Status.WARNING: "yellow",
    Status.BAD: "red",
    Status.INFO: "cyan",
    Status.UNKNOWN: UNKNOWN_TEXT_STYLE,
    Status.ERROR: "red",
}


@dataclass
class CheckResult:
    """Result of a single check. Fields:
    - name: human-readable check name
    - status: Status enum value
    - value: the detected/current value as a string
    - recommendation: what to do to improve (empty if already good)
    - perf_impact: estimated gaming performance impact if this setting is wrong
                   e.g. "High", "Med", "Low", or "" if not applicable
    """

    name: str
    status: Status
    value: str
    recommendation: str = ""
    perf_impact: str = ""


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------


def _reg_read(hive, path: str, name: str, default=None):
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        try:
            value, _ = winreg.QueryValueEx(key, name)
            return value
        finally:
            winreg.CloseKey(key)
    except OSError:
        return default


def reg_hklm(path: str, name: str, default=None):
    return _reg_read(winreg.HKEY_LOCAL_MACHINE, path, name, default)


def reg_hkcu(path: str, name: str, default=None):
    return _reg_read(winreg.HKEY_CURRENT_USER, path, name, default)


def reg_enum_subkeys(hive, path: str) -> list[str]:
    keys = []
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        i = 0
        while True:
            try:
                keys.append(winreg.EnumKey(key, i))
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except OSError:
        pass
    return keys


# ---------------------------------------------------------------------------
# Subprocess helpers
# ---------------------------------------------------------------------------


def run_powershell(cmd: str, timeout: int = 15) -> str:
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def run_cmd(cmd: str, timeout: int = 10) -> str:
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def ps_json(cmd: str, timeout: int = 15) -> list[dict] | dict | None:
    """Run PowerShell command, append | ConvertTo-Json, parse result."""
    output = run_powershell(f"{cmd} | ConvertTo-Json -Depth 3", timeout=timeout)
    if not output:
        return None
    try:
        data = json.loads(output)
        return data
    except json.JSONDecodeError:
        return None


def wmi_query(
    wql: str, namespace: str = "root/cimv2", props: Optional[list[str]] = None, timeout: int = 15
) -> list[dict]:
    """Execute a WMI query via PowerShell and return a list of dicts."""
    select = ", ".join(props) if props else "*"
    ps = (
        f'Get-WmiObject -Query "SELECT {select} FROM {wql}" '
        f'-Namespace "{namespace}" -ErrorAction SilentlyContinue | '
        "ConvertTo-Json -Depth 2"
    )
    output = run_powershell(ps, timeout=timeout)
    if not output:
        return []
    try:
        data = json.loads(output)
        if isinstance(data, dict):
            return [data]
        return data or []
    except json.JSONDecodeError:
        return []


# ---------------------------------------------------------------------------
# Power plan helpers
# ---------------------------------------------------------------------------

_PROC_SUBGROUP = "54533251-82be-4824-96c1-47b60b740d00"
_CORE_PARKING_GUID = "0cc5b647-c1df-4637-891a-dec35c318583"
_MIN_PROC_STATE_GUID = "893dee8e-2bef-41e0-89c6-b55d0929964c"
_MAX_PROC_STATE_GUID = "bc5038f7-23e0-4960-96da-33abaf5935ec"
_CSTATES_GUID = "5d76a2ca-e8c0-402f-a133-2158492d58ad"
_CSTATES_LEGACY_GUID = "68f262a7-f621-4069-b9a5-4874169be23c"
_BOOST_MODE_GUID = "be337238-0d82-4146-a960-4f3749d470c7"

_POWER_SCHEME_ROOT = r"SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes"
_POWERCFG_VALUE_CACHE: dict[tuple[str, str, str, bool], Optional[int]] = {}


def get_active_plan_guid() -> Optional[str]:
    output = run_cmd("powercfg /getactivescheme", timeout=8)
    m = re.search(
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
        output,
        re.IGNORECASE,
    )
    return m.group(1).lower() if m else None


def _read_power_setting_from_powercfg(
    plan_guid: str, subgroup: str, setting: str, ac: bool = True
) -> Optional[int]:
    cache_key = (plan_guid.lower(), subgroup.lower(), setting.lower(), ac)
    if cache_key in _POWERCFG_VALUE_CACHE:
        return _POWERCFG_VALUE_CACHE[cache_key]

    target = "AC" if ac else "DC"
    pattern = rf"Current {target} Power Setting Index:\s*0x([0-9a-fA-F]+)"

    commands = [
        f"powercfg /qh {plan_guid} {subgroup} {setting}",
        f"powercfg /q {plan_guid} {subgroup} {setting}",
        f"powercfg /qh SCHEME_CURRENT {subgroup} {setting}",
        f"powercfg /q SCHEME_CURRENT {subgroup} {setting}",
    ]

    for cmd in commands:
        output = run_cmd(cmd, timeout=8)
        if not output:
            continue
        match = re.search(pattern, output, re.IGNORECASE)
        if not match:
            continue
        try:
            value = int(match.group(1), 16)
            _POWERCFG_VALUE_CACHE[cache_key] = value
            return value
        except ValueError:
            continue

    _POWERCFG_VALUE_CACHE[cache_key] = None
    return None


def read_power_setting(
    plan_guid: str, subgroup: str, setting: str, ac: bool = True
) -> Optional[int]:
    key = "ACSettingIndex" if ac else "DCSettingIndex"
    path = f"{_POWER_SCHEME_ROOT}\\{plan_guid}\\{subgroup}\\{setting}"
    value = reg_hklm(path, key)
    if value is not None:
        if isinstance(value, str):
            try:
                return int(value, 0)
            except ValueError:
                return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return _read_power_setting_from_powercfg(plan_guid, subgroup, setting, ac=ac)


# ---------------------------------------------------------------------------
# GPU adapter helper
# ---------------------------------------------------------------------------

VIDEO_CLASS_GUID = "{4d36e968-e325-11ce-bfc1-08002be10318}"
NIC_CLASS_GUID = "{4d36e972-e325-11ce-bfc1-08002be10318}"


def find_adapter_subkeys(class_guid: str) -> list[tuple[str, str]]:
    """Return [(description, registry_path), ...] for class adapters."""
    results = []
    base = f"SYSTEM\\CurrentControlSet\\Control\\Class\\{class_guid}"
    for subkey in reg_enum_subkeys(winreg.HKEY_LOCAL_MACHINE, base):
        if not subkey.isdigit():
            continue
        path = f"{base}\\{subkey}"
        desc = reg_hklm(path, "DriverDesc") or reg_hklm(path, "DeviceDesc")
        if desc:
            results.append((desc, path))
    return results

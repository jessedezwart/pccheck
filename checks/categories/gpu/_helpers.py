"""
GPU checks:
  - Resizable BAR / Smart Access Memory
  - PCIe link width (x16 / x8 / x4)
  - GPU thermal throttling
  - Driver version (installed + optional online latest)
  - Hardware-Accelerated GPU Scheduling (HAGS)
  - Shader cache size limit (NVIDIA)
  - NVIDIA Whisper Mode / AMD Chill enabled unexpectedly

To remove a check, delete or comment out its entry in get_checks().
"""

from __future__ import annotations

import re
from typing import Optional

from checks.base import (
    VIDEO_CLASS_GUID,
    CheckResult,
    Status,
    find_adapter_subkeys,
    reg_hkcu,
    reg_hklm,
    run_cmd,
    run_powershell,
    wmi_query,
)

# ---------------------------------------------------------------------------
# GPU vendor detection helpers
# ---------------------------------------------------------------------------


def _nvidia_smi(args: str) -> str:
    """Run nvidia-smi with given args; returns empty string on failure."""
    return run_cmd(f"nvidia-smi {args} 2>nul")


def _is_nvidia() -> bool:
    return bool(_nvidia_smi("--query-gpu=name --format=csv,noheader"))


def _gpu_adapters() -> list[tuple[str, str]]:
    """Return (desc, registry_path) for display adapters."""
    return find_adapter_subkeys(VIDEO_CLASS_GUID)


def _primary_gpu_name() -> str:
    rows = wmi_query("Win32_VideoController", props=["Name", "AdapterCompatibility"])
    for row in rows:
        name = row.get("Name", "")
        if name and "Microsoft" not in name:
            return name
    return ""


__all__ = [
    "annotations",
    "re",
    "Optional",
    "CheckResult",
    "Status",
    "reg_hklm",
    "reg_hkcu",
    "run_cmd",
    "run_powershell",
    "wmi_query",
    "find_adapter_subkeys",
    "VIDEO_CLASS_GUID",
    "_nvidia_smi",
    "_is_nvidia",
    "_gpu_adapters",
    "_primary_gpu_name",
]

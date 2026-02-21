from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_interface_type() -> CheckResult:
    """Check the interface type of the C: drive (NVMe, SATA SSD, or HDD).
    NVMe is dramatically faster than SATA/AHCI; HDDs bottleneck load times."""
    # Primary: PowerShell Get-PhysicalDisk correctly reports BusType=NVMe
    ps = (
        "$n = (Get-Partition -DriveLetter C -ErrorAction SilentlyContinue).DiskNumber; "
        "if ($null -ne $n) { "
        "  $p = Get-PhysicalDisk | Where-Object { $_.DeviceId -eq [string]$n } | Select-Object -First 1; "
        "  if ($p) { @{ BusType=$p.BusType; MediaType=$p.MediaType; FriendlyName=$p.FriendlyName } | ConvertTo-Json } "
        "}"
    )
    out = run_powershell(ps)
    if out:
        try:
            data = json.loads(out)
            bus = (data.get("BusType") or "").strip()
            media = (data.get("MediaType") or "").strip()
            name = (data.get("FriendlyName") or "C: drive").strip()
            if "NVM" in bus.upper():
                return CheckResult("C: Drive Interface", Status.GOOD, f"NVMe — {name[:42]}")
            if media.upper() == "SSD":
                return CheckResult("C: Drive Interface", Status.GOOD, f"SATA SSD — {name[:40]}")
            if media.upper() == "HDD":
                return CheckResult(
                    "C: Drive Interface",
                    Status.BAD,
                    f"HDD — {name[:42]}",
                    "Upgrade C: to an NVMe SSD for dramatically faster load times.",
                )
            return CheckResult(
                "C: Drive Interface",
                Status.INFO,
                f"{bus or '?'} / {media or '?'} — {name[:36]}",
                "Verify C: drive type in Task Manager > Performance > Disk.",
            )
        except Exception:
            pass

    # Fallback: WMI — assume disk 0 is C:
    for d in _get_disk_info():
        if str(d.get("Index", "1")) != "0":
            continue
        model = (d.get("Model") or "").upper()
        iface = (d.get("InterfaceType") or "").upper()
        media = (d.get("MediaType") or "").lower()
        label = d.get("Model", "")[:42]
        if "NVME" in model or "NVM" in iface:
            return CheckResult("C: Drive Interface", Status.GOOD, f"NVMe — {label}")
        if "SSD" in model and "HARD" not in model:
            return CheckResult("C: Drive Interface", Status.GOOD, f"SSD — {label}")
        if "fixed hard" in media:
            return CheckResult(
                "C: Drive Interface",
                Status.BAD,
                f"HDD — {label}",
                "Upgrade C: to an NVMe SSD for dramatically faster load times.",
            )
        return CheckResult(
            "C: Drive Interface",
            Status.INFO,
            f"{iface} — {label}",
            "Verify C: drive type in Task Manager > Performance > Disk.",
        )

    return CheckResult(
        "C: Drive Interface",
        Status.UNKNOWN,
        "Cannot read drive info",
        "Check Task Manager > Performance > Disk for drive type.",
    )


def run_check() -> CheckResult:
    return check_interface_type()

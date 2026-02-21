from __future__ import annotations

import pkgutil
from importlib import import_module
from typing import TYPE_CHECKING, Callable, cast

if TYPE_CHECKING:
    from checks.base import CheckResult


def _guess_impact_explanation(result: CheckResult) -> str:
    name = (getattr(result, "name", "") or "").lower()

    if any(token in name for token in ("thermal", "temperature", "throttl")):
        return "Likely moderate-to-high impact: thermal limits can reduce clocks, lowering sustained FPS and causing frame-time instability."
    if any(token in name for token in ("refresh", "vrr", "g-sync", "freesync", "display")):
        return "Likely moderate impact: display timing mismatches usually reduce smoothness and can increase perceived input delay."
    if any(
        token in name for token in ("cpu", "core", "boost", "c-state", "hyperthread", "vbs", "hvci")
    ):
        return "Likely moderate-to-high impact: CPU scheduling/boost behavior can significantly affect 1% lows and frame-time consistency."
    if any(token in name for token in ("gpu", "pcie", "hags", "rebar", "shader")):
        return "Likely moderate impact: GPU/PCIe settings often affect frame consistency and can lower performance in GPU-heavy scenes."
    if any(token in name for token in ("network", "dns", "interrupt", "rss", "nagle")):
        return "Likely low-to-moderate impact: mostly affects online responsiveness (latency/jitter) rather than raw FPS."
    if any(token in name for token in ("audio", "sample", "spatial", "exclusive")):
        return "Likely low impact on FPS, but can affect audio latency/clarity and add minor CPU overhead."
    if any(token in name for token in ("storage", "drive", "smart", "write cach", "nvme", "ssd")):
        return "Likely low impact on average FPS, but can meaningfully affect load times and asset-streaming stutter."
    if any(token in name for token in ("usb", "mouse", "polling", "controller")):
        return "Likely low-to-moderate impact: input path settings can affect responsiveness and consistency."

    status_value = getattr(getattr(result, "status", None), "value", "")
    if status_value in ("bad", "error"):
        return "Likely moderate-to-high impact: this type of issue often causes visible performance or responsiveness degradation."
    if status_value == "warning":
        return "Likely moderate impact: this can reduce smoothness or consistency depending on game and hardware."
    if status_value in ("info", "unknown"):
        return "Likely low-to-moderate impact: uncertain automatically, but commonly affects latency or frame consistency."
    return "No likely negative performance impact."


def run_checks_from_package(
    package_name: str,
    on_result: Callable[[CheckResult], None] | None = None,
) -> list[CheckResult]:
    package = import_module(package_name)
    module_names = sorted(
        module_info.name
        for module_info in pkgutil.iter_modules(package.__path__)
        if not module_info.name.startswith("_")
    )

    results: list[CheckResult] = []
    for module_name in module_names:
        module = import_module(f"{package_name}.{module_name}")
        run_check = getattr(module, "run_check", None)
        if callable(run_check):
            result = cast("CheckResult", run_check())

            impact_explanation = (getattr(result, "perf_impact", "") or "").strip()
            if not impact_explanation:
                module_impact = getattr(module, "IMPACT_EXPLANATION", "")
                impact_getter = getattr(module, "get_impact_explanation", None)

                if callable(impact_getter):
                    impact_value = impact_getter(result)
                    impact_explanation = (
                        str(impact_value).strip() if impact_value is not None else ""
                    )
                elif isinstance(module_impact, str):
                    impact_explanation = module_impact.strip()

                if not impact_explanation:
                    status_value = getattr(getattr(result, "status", None), "value", "")
                    if status_value != "good":
                        impact_explanation = _guess_impact_explanation(result)

            if impact_explanation:
                result.perf_impact = impact_explanation

            results.append(result)
            if on_result:
                on_result(result)
    return results

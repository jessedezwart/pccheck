from __future__ import annotations

import pkgutil
from importlib import import_module
from typing import TYPE_CHECKING, Callable, cast

if TYPE_CHECKING:
    from checks.base import CheckResult


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

            if impact_explanation:
                result.perf_impact = impact_explanation

            results.append(result)
            if on_result:
                on_result(result)
    return results

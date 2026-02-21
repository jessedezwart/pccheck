from __future__ import annotations

import pkgutil
from importlib import import_module
from typing import Callable


def _discover_category_packages() -> list[tuple[str, str]]:
    categories_package = import_module("checks.categories")

    return sorted(
        (
            module_info.name,
            f"checks.categories.{module_info.name}",
        )
        for module_info in pkgutil.iter_modules(categories_package.__path__)
        if module_info.ispkg and not module_info.name.startswith("_")
    )


def get_categories() -> dict[str, tuple[str, Callable[..., list]]]:
    categories: dict[str, tuple[str, Callable[..., list]]] = {}
    for key, package_path in _discover_category_packages():
        package = import_module(package_path)
        display_name = getattr(package, "CATEGORY_NAME", key.replace("_", " ").title())
        get_checks = getattr(package, "get_checks")
        categories[key] = (display_name, get_checks)
    return categories

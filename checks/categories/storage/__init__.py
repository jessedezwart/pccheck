from __future__ import annotations

from typing import Callable

from checks.base import CheckResult
from checks.categories import run_checks_from_package

CATEGORY_NAME = "Storage"


def get_checks(on_result: Callable[[CheckResult], None] | None = None) -> list[CheckResult]:
    return run_checks_from_package(__name__, on_result=on_result)

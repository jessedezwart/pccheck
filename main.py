"""
pccheck — PC Gaming Performance Analyzer
=========================================
Analyzes your Windows PC configuration and flags settings that hurt gaming
performance: CPU parking, power plans, HAGS, VBS, driver issues, and more.

Usage:
    python main.py              # Run all checks

Requires Windows + Python 3.10+. Run as Administrator for full results.
"""

from __future__ import annotations

import sys

# Platform guard must come before any Windows-specific check imports.
if sys.platform != "win32":
    from rich.console import Console as _Console

    _Console().print(
        "[red]pccheck only supports Windows.[/red] "
        "Run this with a native Windows Python installation, not WSL."
    )
    sys.exit(1)

import ctypes
import os

from rich.console import Console, Group
from rich.live import Live
from rich.text import Text
from rich.tree import Tree

# ── Category registry ─────────────────────────────────────────────────────
from checks import get_categories

CATEGORIES = get_categories()
console = Console()


def _format_tree_result_line(result) -> Text:
    from checks.base import STATUS_COLOR, STATUS_ICON

    color = STATUS_COLOR.get(result.status, "white")
    icon = STATUS_ICON.get(result.status, "?")

    text = Text()
    text.append(icon, style=color)
    text.append("  ")
    text.append(f"{result.name}: ", style=color)
    text.append(result.value, style=color)
    return text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _elevate_if_needed() -> None:
    """Re-launch with UAC elevation if not already running as admin.
    Opens an elevated window and exits the current (non-admin) process.
    If the user cancels the UAC prompt, execution continues without admin rights.
    """
    if _is_admin():
        return
    if getattr(sys, "frozen", False):
        # Running as a frozen EXE — re-launch self with no extra args
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, None, None, 1)
    else:
        # Running as a script — pass the script path to the interpreter, no extra args
        script = os.path.abspath(sys.argv[0])
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}"', None, 1
        )
    if ret > 32:  # > 32 means ShellExecute succeeded
        sys.exit(0)
    # ret <= 32 means failure (user cancelled UAC, etc.) — fall through unelevated


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------


def run_checks() -> None:
    """
    [bold]Run gaming performance checks[/bold] on this Windows PC.

    Results are color-coded:
      [green]✓ Good[/green]    [yellow]⚠ Warning[/yellow]    [red]✗ Issue[/red]    [cyan]ℹ Info[/cyan]    [dim]? Unknown[/dim]
    """
    from checks.base import DETAIL_TEXT_STYLE, Status

    if not _is_admin():
        console.print(
            "[yellow]⚠  Not running as Administrator — some checks may be incomplete.[/yellow]\n"
        )

    keys = list(CATEGORIES.keys())

    if not keys:
        console.print("[red]No categories discovered.[/red]")
        console.print(f"Available: {', '.join(CATEGORIES)}")
        sys.exit(1)

    all_results: list = []

    category_trees: list[Tree] = []

    console.print("[bold]Check Results[/bold]")

    def _render_tree_group() -> Group:
        return Group(*category_trees)

    with Live(_render_tree_group(), console=console, refresh_per_second=8) as live:
        for key in keys:
            display_name, get_fn = CATEGORIES[key]
            category_node = Tree(f"[bold cyan]{display_name}[/bold cyan]")
            category_trees.append(category_node)

            def on_result(result):
                all_results.append((display_name, result))
                result_node = category_node.add(_format_tree_result_line(result))

                if result.status != Status.GOOD:
                    impact_explanation = (getattr(result, "perf_impact", "") or "").strip()
                    if impact_explanation:
                        result_node.add(
                            f"[{DETAIL_TEXT_STYLE}]Impact:[/{DETAIL_TEXT_STYLE}] {impact_explanation}"
                        )

                if result.recommendation and result.status in (
                    Status.BAD,
                    Status.WARNING,
                    Status.ERROR,
                    Status.UNKNOWN,
                    Status.INFO,
                ):
                    result_node.add(
                        f"[{DETAIL_TEXT_STYLE}]↳ {result.recommendation}[/{DETAIL_TEXT_STYLE}]"
                    )
                live.update(_render_tree_group(), refresh=True)

            try:
                get_fn(on_result=on_result)
            except Exception as exc:
                from checks.base import CheckResult, Status

                error_result = CheckResult(
                    f"{display_name} (error)",
                    Status.ERROR,
                    str(exc)[:120],
                    "This category failed to run. Try running as Administrator.",
                )
                on_result(error_result)

    bad_count = sum(1 for _, result in all_results if result.status in (Status.BAD, Status.ERROR))
    warn_count = sum(1 for _, result in all_results if result.status == Status.WARNING)
    good_count = sum(1 for _, result in all_results if result.status == Status.GOOD)
    total_count = len(all_results)

    if bad_count > 0:
        summary_style = "red"
    elif warn_count > 0:
        summary_style = "yellow"
    else:
        summary_style = "green"

    console.print()
    console.print(
        f"[bold {summary_style}]Summary:[/bold {summary_style}] "
        f"{bad_count} issues, {warn_count} warnings, {good_count} passed ({total_count} total)"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _elevate_if_needed()
    run_checks()

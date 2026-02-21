"""
Rich-based report renderer for pccheck results.
"""

from __future__ import annotations

from typing import Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from checks.base import STATUS_COLOR, STATUS_ICON, CheckResult, Status

# Status display priority for sorting (worst first)
_SORT_ORDER = {
    Status.ERROR: 0,
    Status.BAD: 1,
    Status.WARNING: 2,
    Status.UNKNOWN: 3,
    Status.INFO: 4,
    Status.GOOD: 5,
}

_IMPACT_COLOR = {
    "High": "red",
    "Med": "yellow",
    "Low": "green",
}


def print_report(
    console: Console,
    all_results: dict[str, list[CheckResult]],
    verbose: bool = False,
    output_file: Optional[str] = None,
) -> None:
    """Render the full report to the console (and optionally to a file)."""
    total_bad = 0
    total_warn = 0
    total_good = 0
    total_unknown = 0

    console.print()

    for category, results in all_results.items():
        bad = [r for r in results if r.status in (Status.BAD, Status.ERROR)]
        warn = [r for r in results if r.status == Status.WARNING]
        good = [r for r in results if r.status == Status.GOOD]
        unknown = [r for r in results if r.status == Status.UNKNOWN]

        total_bad += len(bad)
        total_warn += len(warn)
        total_good += len(good)
        total_unknown += len(unknown)

        # Show the Impact column only when at least one result has a value
        has_impact = any(r.perf_impact for r in results)

        table = Table(
            title=f"[bold]{category}[/bold]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold dim",
            pad_edge=True,
            show_edge=True,
            expand=True,
        )
        table.add_column("", width=3, justify="center", no_wrap=True)
        table.add_column("Check", min_width=26, no_wrap=False)
        table.add_column("Detected Value", min_width=24, no_wrap=False)
        if has_impact:
            table.add_column("Impact", width=7, justify="center", no_wrap=True)
        table.add_column("Recommendation", min_width=35, no_wrap=False)

        sorted_results = sorted(results, key=lambda r: _SORT_ORDER[r.status])

        for result in sorted_results:
            color = STATUS_COLOR[result.status]
            icon = STATUS_ICON[result.status]

            cells = [
                f"[{color}]{icon}[/{color}]",
                f"[bold]{result.name}[/bold]",
                f"[{color}]{result.value}[/{color}]",
            ]
            if has_impact:
                icol = _IMPACT_COLOR.get(result.perf_impact, "dim")
                cells.append(f"[{icol}]{result.perf_impact}[/{icol}]" if result.perf_impact else "")
            cells.append(f"[dim]{result.recommendation}[/dim]" if result.recommendation else "")

            table.add_row(*cells)

        console.print(table)

    # ---- Summary panel ----
    console.print()

    score_parts: list[str] = []
    if total_bad:
        score_parts.append(f"[bold red]{total_bad} issue{'s' if total_bad != 1 else ''}[/bold red]")
    if total_warn:
        score_parts.append(
            f"[bold yellow]{total_warn} warning{'s' if total_warn != 1 else ''}[/bold yellow]"
        )
    score_parts.append(f"[green]{total_good} passed[/green]")
    if total_unknown:
        score_parts.append(f"[dim]{total_unknown} unknown[/dim]")

    total = total_bad + total_warn + total_good + total_unknown
    score_parts.append(f"[dim]({total} total)[/dim]")

    summary_text = Text.assemble("  ", *[Text.from_markup(p + "  ") for p in score_parts])

    if total_bad == 0 and total_warn == 0:
        border = "green"
        heading = "[bold green]All clear! No issues found.[/bold green]"
    elif total_bad > 0:
        border = "red"
        heading = (
            f"[bold red]{total_bad} critical issue"
            f"{'s' if total_bad != 1 else ''} need attention.[/bold red]"
        )
    else:
        border = "yellow"
        heading = (
            f"[bold yellow]{total_warn} optimization"
            f"{'s' if total_warn != 1 else ''} available.[/bold yellow]"
        )

    console.print(
        Panel(
            Text.assemble(heading, "\n", summary_text),
            title="[bold]Summary[/bold]",
            border_style=border,
        )
    )

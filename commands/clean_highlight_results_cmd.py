"""CLI: remove files in results/highlight older than N days."""

import os
from datetime import datetime, timedelta

import click

from flask import current_app


def _clean_highlight_results(dir_path: str, max_age_days: int, dry_run: bool) -> int:
    cutoff_ts = (datetime.now() - timedelta(days=max_age_days)).timestamp()
    removed = 0

    if not os.path.isdir(dir_path):
        return 0

    for name in os.listdir(dir_path):
        path = os.path.join(dir_path, name)
        if not os.path.isfile(path):
            continue
        if os.path.getmtime(path) >= cutoff_ts:
            continue
        if dry_run:
            click.echo(f"Would remove: {path}")
        else:
            os.remove(path)
            click.echo(f"Removed: {path}")
        removed += 1

    return removed


@click.command("highlight:clean-results")
@click.option(
    "--days",
    type=int,
    default=3,
    help="Remove files older than this many days (default: 3).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Only list files that would be removed, do not delete.",
)
def clean_highlight_results_cmd(days: int, dry_run: bool) -> None:
    """Remove files in results/highlight older than N days."""
    dir_path: str = current_app.config["RESULT_DIR_HIGHLIGHT"]
    removed = _clean_highlight_results(dir_path, days, dry_run)
    suffix = " (dry-run)" if dry_run else ""
    click.echo(f"Done: {removed} file(s) removed{suffix}.")

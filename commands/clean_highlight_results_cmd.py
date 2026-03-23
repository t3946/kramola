"""CLI: remove files in results/highlight older than N days (results + paired source archives)."""

import os
import re
from datetime import datetime, timedelta

import click

from flask import current_app

_UUID_RE_PART: str = r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
_HIGHLIGHTED_OR_SOURCE_RE: re.Pattern[str] = re.compile(
    rf"^(?:highlighted_|source_){_UUID_RE_PART}",
    re.IGNORECASE,
)


def _task_id_from_highlight_result_name(name: str) -> str | None:
    match: re.Match[str] | None = _HIGHLIGHTED_OR_SOURCE_RE.match(name)

    if not match:
        return None

    return match.group(1).lower()


def _companion_paths_for_task(dir_path: str, task_id: str) -> list[str]:
    prefix_highlighted: str = f"highlighted_{task_id}"
    prefix_source: str = f"source_{task_id}"
    paths: list[str] = []

    for name in os.listdir(dir_path):
        path: str = os.path.join(dir_path, name)

        if not os.path.isfile(path):
            continue

        name_lower: str = name.lower()

        if name_lower.startswith(prefix_highlighted) or name_lower.startswith(prefix_source):
            paths.append(path)

    return paths


def _clean_highlight_results(dir_path: str, max_age_days: int, dry_run: bool) -> int:
    cutoff_ts: float = (datetime.now() - timedelta(days=max_age_days)).timestamp()
    removed: int = 0

    if not os.path.isdir(dir_path):
        return 0

    to_remove: set[str] = set()

    for name in os.listdir(dir_path):
        path: str = os.path.join(dir_path, name)

        if not os.path.isfile(path):
            continue

        if os.path.getmtime(path) >= cutoff_ts:
            continue

        to_remove.add(path)

    task_ids: set[str] = set()

    for path in to_remove:
        tid: str | None = _task_id_from_highlight_result_name(os.path.basename(path))

        if tid:
            task_ids.add(tid)

    for tid in task_ids:
        for companion_path in _companion_paths_for_task(dir_path, tid):
            to_remove.add(companion_path)

    for path in sorted(to_remove):
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
    """Remove highlight results and paired source_* archives in results/highlight older than N days (by mtime)."""
    dir_path: str = current_app.config["RESULT_DIR_HIGHLIGHT"]
    removed: int = _clean_highlight_results(dir_path, days, dry_run)
    suffix: str = " (dry-run)" if dry_run else ""

    click.echo(f"Done: {removed} file(s) removed{suffix}.")

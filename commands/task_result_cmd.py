"""CLI: print TaskResult.load(task_id) to console."""

import json
from dataclasses import asdict

import click

from services.analysis.stats import StatsMatches
from services.task.result import TaskResult


@click.command("task:result")
@click.argument("task_id", type=str)
def task_result_cmd(task_id: str) -> None:
    result = TaskResult.load(task_id)

    if result is None:
        click.echo("(no result)")
        return

    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


def _json_default(obj):
    if hasattr(obj, "value"):
        return obj.value
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    raise TypeError(type(obj))


@click.command("task:stats")
@click.argument("task_id", type=str)
def task_stats_cmd(task_id: str) -> None:
    """Print StatsMatches for task_id as JSON to console."""
    if TaskResult.load(task_id) is None:
        click.echo(f"Stats not found for task_id: \"{task_id}\"")
        return

    stats = StatsMatches(task_id).get_stats()
    click.echo(json.dumps(stats, ensure_ascii=False, indent=2, default=_json_default))
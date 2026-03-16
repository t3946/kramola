"""CLI: print TaskResult.load(task_id) to console."""

import json
import click
from services.task.result import TaskResult
from services.view_stats import ViewStats


@click.command("task:result")
@click.argument("task_id", type=str)
def task_result_cmd(task_id: str) -> None:
    result = TaskResult.load(task_id)

    if result is None:
        click.echo("(no result)")
        return

    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


@click.command("task:stats")
@click.argument("task_id", type=str)
def task_stats_cmd(task_id: str) -> None:
    """Print ViewStats for task_id as JSON to console."""
    if TaskResult.load(task_id) is None:
        click.echo(f"Stats not found for task_id: \"{task_id}\"")
        return

    stats = ViewStats(task_id).get()
    click.echo(stats)
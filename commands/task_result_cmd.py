"""CLI: print TaskResult.load(task_id) to console."""

import json
import click
from services.task.result import TaskResult


@click.command("task:result")
@click.argument("task_id", type=str)
def task_result_cmd(task_id: str) -> None:
    result = TaskResult.load(task_id)
    if result is None:
        click.echo("(no result)")
        return
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))

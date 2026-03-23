"""CLI: delete Redis keys for a highlight task (task:<id> and task:<id>:*)."""

import click

from flask import current_app


def _collect_task_key_names(redis_client, task_id: str) -> list[str]:
    pattern: str = f"task:{task_id}*"
    keys: list[str] = []

    for raw_key in redis_client.scan_iter(match=pattern, count=500):
        key: str = raw_key.decode() if isinstance(raw_key, bytes) else raw_key
        keys.append(key)

    return sorted(set(keys))


def _delete_keys(redis_client, key_names: list[str]) -> int:
    chunk_size: int = 500
    deleted_total: int = 0

    for offset in range(0, len(key_names), chunk_size):
        chunk: list[str] = key_names[offset: offset + chunk_size]
        deleted_total += int(redis_client.delete(*chunk))

    return deleted_total


@click.command("task:delete")
@click.argument("task_id", type=str)
def task_delete_cmd(task_id: str) -> None:
    """Remove all Redis keys for TASK_ID (main hash, :preparation, :search, etc.)."""
    redis_client = current_app.redis_client_tasks

    if redis_client is None:
        raise click.ClickException("Redis client is not available (check app startup / REDIS_* env).")

    stripped_id: str = task_id.strip()

    if not stripped_id:
        raise click.ClickException("task_id must not be empty.")

    key_names: list[str] = _collect_task_key_names(redis_client, stripped_id)

    if not key_names:
        click.echo(f"No Redis keys matched pattern task:{stripped_id}*")
        return

    deleted: int = _delete_keys(redis_client, key_names)

    click.echo(f"Deleted {deleted} key(s):")
    for name in key_names:
        click.echo(f"  {name}")

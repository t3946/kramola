"""Flask CLI command: run inagents:load then inagents:parse in sequence."""

import click

from commands.load_inagents_cmd import load_inagents_cmd, run_load_inagents
from commands.parse_inagents_cmd import parse_inagents_cmd, run_parse_inagents


def run_update_inagents() -> tuple[int, int] | None:
    """Run inagents update flow and return parse stats."""
    loaded_file_path = run_load_inagents()

    return run_parse_inagents(loaded_file_path)


@click.command("inagents:update")
def update_inagents_cmd() -> None:
    ctx = click.get_current_context()
    ctx.invoke(load_inagents_cmd)
    ctx.invoke(parse_inagents_cmd)

"""Flask CLI command: run inagents:load then inagents:parse in sequence."""

import click

from commands.load_inagents_cmd import load_inagents_cmd
from commands.parse_inagents_cmd import parse_inagents_cmd


@click.command("inagents:update")
def update_inagents_cmd() -> None:
    ctx = click.get_current_context()
    ctx.invoke(load_inagents_cmd)
    ctx.invoke(parse_inagents_cmd)

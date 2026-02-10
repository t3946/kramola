"""Register Flask CLI commands."""

from flask import Flask

from commands.create_admin import create_admin_cmd
from commands.load_inagents_cmd import load_inagents_cmd
from commands.parse_inagents_cmd import parse_inagents_cmd


def register_commands(app: Flask) -> None:
    app.cli.add_command(create_admin_cmd)
    app.cli.add_command(load_inagents_cmd)
    app.cli.add_command(parse_inagents_cmd)

"""Register Flask CLI commands."""

from flask import Flask

from commands.create_admin import create_admin_cmd
from commands.load_inagents_cmd import load_inagents_cmd
from commands.parse_inagents_cmd import parse_inagents_cmd
from commands.strip_inagents_search_terms_initials import strip_inagents_search_initials_cmd
from commands.task_result_cmd import task_result_cmd, task_stats_cmd
from commands.update_inagents_cmd import update_inagents_cmd
from commands.parse_extremists import sync_extremists_cmd


def register_commands(app: Flask) -> None:
    app.cli.add_command(create_admin_cmd)
    app.cli.add_command(load_inagents_cmd)
    app.cli.add_command(parse_inagents_cmd)
    app.cli.add_command(strip_inagents_search_initials_cmd)
    app.cli.add_command(task_result_cmd)
    app.cli.add_command(task_stats_cmd)
    app.cli.add_command(update_inagents_cmd)
    app.cli.add_command(sync_extremists_cmd)

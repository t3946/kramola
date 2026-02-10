"""Flask CLI command: load foreign agents registry xlsx from minjust.gov.ru."""

import importlib.util
from pathlib import Path

import click


def _load_run():
    # Module lives in commands/load-inagents/ (hyphen = not importable as package)
    path = Path(__file__).resolve().parent / "load-inagents" / "load_inagents.py"
    spec = importlib.util.spec_from_file_location("load_inagents_module", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run


@click.command("load-inagents")
def load_inagents_cmd() -> None:
    run = _load_run()
    out = run()
    if out is None:
        click.echo("Export link not found.")
    else:
        click.echo(f"Saved: {out}")

"""Flask CLI command: parse temp/export.xlsx or export.csv and sync inagents to DB."""

import importlib.util
from pathlib import Path

import click


def _get_parser_module():
    path = Path(__file__).resolve().parent / "load-inagents" / "parse_inagents.py"
    spec = importlib.util.spec_from_file_location("parse_inagents_module", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@click.command("parse-inagents")
@click.option("--path", "file_path", type=click.Path(path_type=Path), default=None, help="Path to export.xlsx or export.csv (default: commands/load-inagents/temp/export.csv or export.xlsx)")
def parse_inagents_cmd(file_path: Path | None) -> None:
    mod = _get_parser_module()
    if file_path is None:
        temp_dir = Path(__file__).resolve().parent / "load-inagents" / "temp"
        file_path = temp_dir / "export.csv" if (temp_dir / "export.csv").exists() else temp_dir / "export.xlsx"
    if not file_path.exists():
        click.echo(f"File not found: {file_path}")
        return
    parser = mod.InagentsXlsxParser(file_path)
    inserted, updated = parser.sync_to_db()
    click.echo(f"Synced: {inserted} inserted, {updated} updated.")

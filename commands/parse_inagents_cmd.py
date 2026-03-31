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


def get_parse_inagents_module():
    """Loads parse_inagents from commands/load-inagents (hyphen path) for callers outside the CLI."""
    return _get_parser_module()


def run_parse_inagents(file_path: Path | None = None) -> tuple[int, int] | None:
    """Parse inagents file and sync DB. Returns (inserted, updated) or None when file not found."""
    mod = _get_parser_module()
    target_file_path: Path | None = file_path

    if target_file_path is None:
        temp_dir = Path(__file__).resolve().parent / "load-inagents" / "temp"
        target_file_path = temp_dir / "export.csv" if (temp_dir / "export.csv").exists() else temp_dir / "export.xlsx"

    if not target_file_path.exists():
        return None

    parser = mod.InagentsXlsxParser(target_file_path)
    inserted: int
    updated: int
    inserted, updated = parser.sync_to_db()

    return (inserted, updated)


@click.command("inagents:parse")
@click.option("--path", "file_path", type=click.Path(path_type=Path), default=None, help="Path to export.xlsx or export.csv (default: commands/load-inagents/temp/export.csv or export.xlsx)")
def parse_inagents_cmd(file_path: Path | None) -> None:
    sync_result: tuple[int, int] | None = run_parse_inagents(file_path)

    if sync_result is None:
        temp_dir = Path(__file__).resolve().parent / "load-inagents" / "temp"
        default_file_path = temp_dir / "export.csv" if (temp_dir / "export.csv").exists() else temp_dir / "export.xlsx"
        show_file_path: Path = file_path or default_file_path
        click.echo(f"File not found: {show_file_path}")
        return

    inserted, updated = sync_result
    click.echo(f"Synced: {inserted} inserted, {updated} updated.")
